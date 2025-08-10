import numpy as np
import pandas as pd
import os
import fnmatch
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from database.models.user import User
from database.models.portfolio import Portfolio
from database.models.ticker_data import TickerData
from database.models.ticker import TickerInfo
from services.ibkr_service import IBKRService
from datetime import datetime, timedelta
from quant.volatility import forecast_sigma, log_returns, annualized_vol
from quant.risk import clamp, build_cov, risk_contribution
from quant.linear import ols_beta
from quant.cov import ewma_corr
from quant.drawdown import drawdown
from quant.regime import regime_metrics
from quant.scoring import risk_mix
from quant.scenario import scenario_pnl
from quant.concentration import concentration_metrics
from quant.weights import inverse_vol_allocation
from quant.correlation import avg_and_high_corr
from quant.returns import stack_common_returns
from quant.stats import basic_stats
from quant.var import var_cvar
import threading
import time
import random
from collections import defaultdict

# Memo cache for volatility calculations within a single request
_vol_cache = {}

# Risk Scoring Configuration
NORMALIZATION = {
    "HHI_LOW": 0.05, 
    "HHI_HIGH": 0.30,
    "VOL_MAX": 0.40, 
    "BETA_ABS_MAX": 1.5,
    "FACTOR_L1_MAX": 3.0,
    "STRESS_5PCT_FULLSCORE": 0.10,
}

# Stress Testing Configuration
from datetime import date

STRESS_SCENARIOS = [
    {"name": "2018 Q4 Volatility", "start": date(2018,10,1), "end": date(2018,12,24)},
    {"name": "2020 COVID Crash",   "start": date(2020,2,20), "end": date(2020,3,23)},
    {"name": "2020 Recovery",      "start": date(2020,3,24), "end": date(2020,8,31)},
    {"name": "2022 Inflation Shock","start": date(2022,1,3), "end": date(2022,10,14)},
    {"name": "2015 China Deval",   "start": date(2015,8,10), "end": date(2015,9,1)},
]
STRESS_LIMITS = {
    "lookback_regime_days": 60,
    "momentum_window_days": 20,
    "scenario_min_days": 10,
    "scenario_min_weight_coverage": 0.30,  # at least 30% market value must be covered by data
    "clamp_return_abs": 0.40,              # ±40% guard na dzienne zwroty
}

# Market Regime Thresholds
REGIME_THRESH = {
    "crisis_vol": 0.30,
    "cautious_vol": 0.20, 
    "cautious_corr": 0.45,
    "bull_mom": 0.05,
    "bull_vol": 0.18,
    "bull_corr": 0.25
}

class DataService:
    def __init__(self):
        self.ibkr_service = IBKRService()
        # Static tickers always fetched from IBKR
        self.STATIC_TICKERS = ['SPY', 'MTUM', 'IWM', 'VLUE', 'QUAL']
        
        # Cache system for expensive operations
        self._cache = {}
        self._cache_timestamps = {}
        self._cache_lock = threading.Lock()
        self.CACHE_TTL = 300  # 5 minutes cache TTL
        
    def _get_cache_key(self, method: str, username: str, **kwargs) -> str:
        """Generate cache key for method call"""
        key_parts = [method, username]
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}:{v}")
        return "|".join(key_parts)
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get data from cache if valid"""
        with self._cache_lock:
            if key in self._cache:
                timestamp = self._cache_timestamps.get(key, 0)
                if time.time() - timestamp < self.CACHE_TTL:
                    return self._cache[key]
                else:
                    # Remove expired cache
                    del self._cache[key]
                    if key in self._cache_timestamps:
                        del self._cache_timestamps[key]
        return None
    
    def _set_cache(self, key: str, data: Any) -> None:
        """Set data in cache"""
        with self._cache_lock:
            self._cache[key] = data
            self._cache_timestamps[key] = time.time()
    
    def _clear_cache(self, pattern: str = None) -> None:
        """Clear cache entries matching pattern using fnmatch for wildcard support"""
        with self._cache_lock:
            if pattern:
                # Use fnmatch for proper wildcard matching
                keys_to_remove = [k for k in self._cache.keys() if fnmatch.fnmatch(k, pattern)]
            else:
                keys_to_remove = list(self._cache.keys())
            
            print(f"🧹 Clearing cache for pattern '{pattern}': {len(keys_to_remove)} keys")
            for key in keys_to_remove:
                if key in self._cache:
                    del self._cache[key]
                    print(f"   🗑️  Removed: {key}")
                if key in self._cache_timestamps:
                    del self._cache_timestamps[key]
            
            # Also clear global volatility cache
            global _vol_cache
            _vol_cache.clear()
            print(f"   🗑️  Cleared global volatility cache ({len(_vol_cache)} entries)")
    
    def _get_cached_volatility(self, symbol: str, model: str, returns: np.ndarray) -> float:
        """Get cached volatility calculation or compute and cache"""
        cache_key = f"{symbol}_{model}_{hash(returns.tobytes())}"
        
        if cache_key in _vol_cache:
            return _vol_cache[cache_key]
        
        # Calculate and cache
        vol = forecast_sigma(returns, model)
        _vol_cache[cache_key] = vol
        return vol
        
    def _ensure_ticker_info(self, db: Session, symbol: str, *, preloaded: Optional[dict] = None) -> Optional[TickerInfo]:
        """
        Ensure ticker info exists in database, fetch from IBKR and yfinance if needed
        Returns TickerInfo object or None if failed
        """
        try:
            # 0️⃣ – cache check
            info = db.query(TickerInfo).filter(TickerInfo.symbol == symbol).first()
            if info and (datetime.utcnow() - info.updated_at).days < 30:
                print(f"✅ Using cached ticker info for {symbol}")
                return info

            # 1) accept preload (incl. {"type": "ETF"}); do not call IBKR again
            fundamental_data = preloaded

            # 2) if preload marks ETF → skip IBKR and use yfinance
            if fundamental_data and fundamental_data.get("type") == "ETF":
                print(f"🔎 {symbol} is ETF → skipping IBKR, going straight to yfinance")
                sector, industry = self.ibkr_service._get_sector_industry_external(symbol)
                market_cap = self.ibkr_service._get_market_cap_external(symbol)
                fundamental_data = {
                    "industry": industry,
                    "sector": sector,
                    "market_cap": market_cap,
                    "company_name": fundamental_data.get("company_name", symbol)
                }

            # 3) if still missing, perform a single IBKR/yfinance call
            if not fundamental_data:
                if self.ibkr_service.connection and self.ibkr_service.connection.connected:
                    fundamental_data = self.ibkr_service.get_fundamentals(symbol)
                if not fundamental_data or fundamental_data.get("industry") == "Unknown":
                    sector, industry = self.ibkr_service._get_sector_industry_external(symbol)
                    market_cap = self.ibkr_service._get_market_cap_external(symbol)
                    if not fundamental_data:
                        fundamental_data = {}
                    fundamental_data.update({"industry": industry,
                                         "sector": sector,
                                         "market_cap": market_cap})

            if not fundamental_data:
                return info   # whatever we had

            # 4️⃣ – zapis do DB
            if not info:
                info = TickerInfo(symbol=symbol)
                db.add(info)
            
            info.industry = fundamental_data.get("industry")
            info.sector = fundamental_data.get("sector")
            info.market_cap = fundamental_data.get("market_cap")
            info.company_name = fundamental_data.get("company_name")
            info.updated_at = datetime.utcnow()
            
            db.commit()
            print(f"✅ Updated ticker info for {symbol}: {fundamental_data}")
            return info
            
        except Exception as e:
            print(f"Error ensuring ticker info for {symbol}: {e}")
            db.rollback()
            return None
    
    def _looks_like_etf(self, symbol: str) -> bool:
        """Simple check if symbol looks like an ETF"""
        etf_hints = {"etf", "trust", "fund", "treasury", "ultra", "proshares", "ishares", "vanguard", "spy", "qqq", "iwm", "mtum", "vlue", "qual", "sgov", "ulty", "bull"}
        symbol_lower = symbol.lower()
        return any(hint in symbol_lower for hint in etf_hints)
    
    def get_all_tickers(self, db: Session, username: str = "admin") -> List[str]:
        """Get all tickers: user portfolio + static tickers"""
        portfolio_tickers = self.get_user_portfolio_tickers(db, username)
        all_tickers = list(set(portfolio_tickers + self.STATIC_TICKERS))
        return sorted(all_tickers)
        
    def get_static_tickers(self) -> List[str]:
        """Get list of static tickers"""
        return self.STATIC_TICKERS.copy()
        
    def add_static_ticker(self, symbol: str) -> bool:
        """Add a new static ticker"""
        if symbol not in self.STATIC_TICKERS:
            self.STATIC_TICKERS.append(symbol)
            return True
        return False
        
    def remove_static_ticker(self, symbol: str) -> bool:
        """Remove a static ticker"""
        if symbol in self.STATIC_TICKERS:
            self.STATIC_TICKERS.remove(symbol)
            return True
        return False
        
    # _lambda_from_half_life moved to backend.quant.volatility
        
    def get_user_portfolio_tickers(self, db: Session, username: str = "admin") -> List[str]:
        """Get ticker symbols from user's portfolio"""
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return []
        
        portfolio_items = db.query(Portfolio).filter(Portfolio.user_id == user.id).all()
        return [item.ticker_symbol for item in portfolio_items]
    
    def fetch_and_store_historical_data(self, db: Session, symbol: str) -> bool:
        """Fetch historical data from IBKR and store in database"""
        try:
            # Connect to IBKR
            if not self.ibkr_service.connect():
                print(f"Failed to connect to IBKR for {symbol}")
                return False
            
            # Get historical data
            historical_data = self.ibkr_service.get_historical_data(symbol)
            if not historical_data:
                print(f"No historical data received for {symbol}")
                return False
            
            # Parse dates with multiple patterns
            DATE_PATTERNS = ['%Y%m%d', '%Y-%m-%d', '%Y%m%d %H:%M:%S', '%Y-%m-%d %H:%M:%S']
            
            def parse_date(date_str: str):
                for pat in DATE_PATTERNS:
                    try:
                        return datetime.strptime(date_str, pat).date()
                    except ValueError:
                        continue
                raise ValueError(f"Unrecognized date format: {date_str}")
            
            # Batch check existing dates
            dates_to_check = [parse_date(bar['date']) for bar in historical_data]
            existing_dates = {
                d[0] for d in db.query(TickerData.date)
                                .filter(TickerData.ticker_symbol == symbol,
                                        TickerData.date.in_(dates_to_check))
                                .all()
            }
            
            # Store historical data
            for bar in historical_data:
                date_obj = parse_date(bar['date'])
                
                if date_obj in existing_dates:
                    continue
                
                ticker_record = TickerData(
                    ticker_symbol=symbol,
                    date=date_obj,
                    open_price=bar['open'],
                    close_price=bar['close'],
                    high_price=bar['high'],
                    low_price=bar['low'],
                    volume=bar['volume']
                )
                db.add(ticker_record)
            
            db.commit()
            print(f"Successfully stored historical data for {symbol}")
            return True
            
        except Exception as e:
            print(f"Error fetching/storing data for {symbol}: {e}")
            return False
        finally:
            self.ibkr_service.disconnect()
    
    def calculate_volatility_metrics(self, db: Session, symbol: str, 
                                   forecast_model: str = 'EWMA (5D)',
                                   risk_free_annual: float = 0.0) -> Dict[str, float]:
        """Calculate volatility metrics for a ticker"""
        try:
            # Get all historical data (not just last 1000)
            historical_data = (db.query(TickerData)
                                 .filter(TickerData.ticker_symbol == symbol)
                                 .order_by(TickerData.date.desc())
                                 .all())
            
            if len(historical_data) < 30:
                print(f"Not enough data for {symbol} ({len(historical_data)} records)")
                return {}
            
            print(f"{symbol}: Found {len(historical_data)} historical records")
            
            # Sort by date ascending for calculations
            historical_data.sort(key=lambda x: x.date)
            
            # Extract prices and calculate returns
            prices = [row.close_price for row in historical_data]
            print(f"{symbol}: Prices range: {min(prices):.2f} - {max(prices):.2f}")
            
            # Calculate log returns
            returns = np.diff(np.log(prices))
            print(f"{symbol}: Returns shape: {returns.shape}, mean: {np.mean(returns):.6f}")
            
            if len(returns) < 30:
                print(f"Not enough returns for {symbol}")
                return {}
            
            # Calculate basic statistics
            stats = basic_stats(returns, risk_free_annual)
            mean_daily = stats["mean_daily"]
            std_daily = stats["std_daily"]
            std_annual = stats["std_annual"]
            sharpe_ratio = stats["sharpe_ratio"]
            
            # Calculate forecast volatility using cached calculation
            print(f"Calculating {forecast_model} volatility for returns shape: {returns.shape}")
            forecast_vol = self._get_cached_volatility(symbol, forecast_model, returns) * 100  # Convert to percentage
            print(f"{symbol}: Calculated volatility: {forecast_vol:.2f}%")
            
            # Annualize mean
            mean_annual = mean_daily * 252
            
            # Get last price from database (NO LIVE FETCHING!)
            last_price = float(historical_data[-1].close_price)
            print(f"Using database price for {symbol}: ${last_price}")
            
            metrics = {
                'volatility_pct': forecast_vol,   # %
                'mean_return_annual': mean_annual,  # fraction per year
                'mean_return_pct': mean_annual * 100,  # %
                'sharpe_ratio': sharpe_ratio,
                'last_price': last_price
            }
            
            print(f"🔍 {symbol} metrics: {metrics}")
            return metrics
            
        except Exception as e:
            print(f"Error calculating metrics for {symbol}: {e}")
            return {}
    
    # _calculate_forecast_volatility, _ewma_volatility, _garch_volatility, _egarch_volatility moved to backend.quant.volatility

    def get_portfolio_volatility_data(self, db: Session, username: str = "admin",
                                      forecast_model: str = 'EWMA (5D)',
                                      vol_floor_annual_pct: float = 8.0,
                                      risk_free_annual: float = 0.0) -> List[Dict[str, Any]]:
        """Get volatility data for user's portfolio tickers + static tickers with caching"""
        try:
            # Check cache first
            cache_key = self._get_cache_key("portfolio_volatility_data", username, 
                                          forecast_model=forecast_model, 
                                          vol_floor=vol_floor_annual_pct,
                                          risk_free=risk_free_annual)
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                print(f"Using cached portfolio volatility data for user: {username}")
                return cached_data
            
            print(f"Getting portfolio volatility data for user: {username}")
            
            portfolio_data = []

            # Get only user's portfolio tickers (no static tickers)
            portfolio_tickers = self.get_user_portfolio_tickers(db, username)
            if not portfolio_tickers:
                print(f"No portfolio tickers found for user {username}")
                result = []
                self._set_cache(cache_key, result)
                return result

            # Get portfolio items with shares info
            user = db.query(User).filter(User.username == username).first()
            portfolio_items = db.query(Portfolio).filter(Portfolio.user_id == user.id).all()
            shares_map = {item.ticker_symbol: item.shares for item in portfolio_items}

        # 1) collect metrics for user's portfolio tickers only
            for symbol in portfolio_tickers:
                print(f"Processing {symbol}...")
                m = self.calculate_volatility_metrics(db, symbol, forecast_model, risk_free_annual)
                print(f"{symbol} metrics: {m}")
                if m:
                    # All tickers are from user's portfolio
                    shares = shares_map.get(symbol, 1000)
                    portfolio_data.append({
                        'symbol': symbol,
                        'forecast_volatility_pct': float(m.get('volatility_pct', 0.0)),
                        'last_price': float(m.get('last_price', 0.0)),
                        'sharpe_ratio': float(m.get('sharpe_ratio', 0.0)),
                        'shares': shares,
                        'is_static': False  # All tickers are from user's portfolio
                    })
                else:
                    print(f"No metrics for {symbol}")

            if not portfolio_data:
                result = []
                self._set_cache(cache_key, result)
                return result

            # 2) Current MV (przed liczeniem wag)
            for item in portfolio_data:
                lp = item['last_price']
                shares = item['shares']
                item['current_mv'] = float(lp) * float(shares)

            total_portfolio_value = float(sum(d['current_mv'] for d in portfolio_data)) if portfolio_data else 0.0
            if total_portfolio_value <= 0:
                result = portfolio_data
                self._set_cache(cache_key, result)
                return result

            # 3) Current weights (po policzeniu totalu)
            for item in portfolio_data:
                item['current_weight_pct'] = 100.0 * item['current_mv'] / total_portfolio_value

            # 4) Inverse-vol weights
            vols = np.array([d['forecast_volatility_pct'] for d in portfolio_data])
            adj_weights = inverse_vol_allocation(vols, vol_floor_annual_pct)
            
            for item, adj_weight in zip(portfolio_data, adj_weights):
                item['adj_volatility_weight_pct'] = adj_weight * 100.0

            # 5) Target MV i delty
            for item in portfolio_data:
                target_w = item['adj_volatility_weight_pct'] / 100.0
                item['target_mv'] = total_portfolio_value * target_w
                item['delta_mv'] = item['target_mv'] - item['current_mv']
                lp = item['last_price']
                item['delta_shares'] = int(np.floor(item['delta_mv'] / lp)) if lp > 0 else 0

            # Cache the result
            self._set_cache(cache_key, portfolio_data)
            
            return portfolio_data
            
        except Exception as e:
            print(f"Error getting portfolio volatility data: {e}")
            error_result = []
            self._set_cache(cache_key, error_result)
            return error_result

    def inject_sample_data(self, db: Session, symbol: str, seed: Optional[int] = None) -> bool:
        """Inject sample historical data for a ticker from 2016 to 2025"""
        try:
            # Set seed for reproducibility
            if seed is not None:
                np.random.seed(seed)
            
            # Check if data already exists
            existing_count = db.query(TickerData).filter(TickerData.ticker_symbol == symbol).count()
            if existing_count > 0:
                print(f"{symbol}: Already has {existing_count} records")
                return True

            # Generate sample data from 2016 to 2025
            base_price = 100.0
            current_price = base_price
            data_points = []
            
            # Generate dates from 2016 to today (trading days only)
            start_date = datetime(2016, 1, 1)
            end_date = datetime.now()
            
            current_date = start_date
            while current_date <= end_date:
                # Skip weekends (Saturday = 5, Sunday = 6)
                if current_date.weekday() < 5:  # Monday = 0, Friday = 4
                    # Generate realistic price movement
                    daily_return = np.random.normal(0, 0.02)  # 2% daily volatility
                    current_price *= (1 + daily_return)
                    
                    open_price = current_price * (1 + np.random.normal(0, 0.01))
                    high_price = max(open_price, current_price) * (1 + abs(np.random.normal(0, 0.015)))
                    low_price = min(open_price, current_price) * (1 - abs(np.random.normal(0, 0.015)))
                    close_price = current_price
                    volume = int(np.random.normal(1000000, 500000))
                    
                    data_points.append({
                        'ticker_symbol': symbol,
                        'date': current_date.date(),
                        'open_price': round(open_price, 2),
                        'close_price': round(close_price, 2),
                        'high_price': round(high_price, 2),
                        'low_price': round(low_price, 2),
                        'volume': max(volume, 100000)
                    })
                
                current_date += timedelta(days=1)

            # Insert data
            for data_point in data_points:
                ticker_record = TickerData(**data_point)
                db.add(ticker_record)
            
            db.commit()
            print(f"✅ Added {len(data_points)} sample records for {symbol}")
            return True

        except Exception as e:
            print(f"Error injecting sample data for {symbol}: {e}")
            db.rollback()
            return False 

    def import_ticker_data_from_file(self, db: Session, symbol: str) -> bool:
        """Import historical data for a ticker from JSON/CSV file"""
        try:
            # Check if data already exists
            existing_count = db.query(TickerData).filter(TickerData.ticker_symbol == symbol).count()
            if existing_count > 0:
                print(f"{symbol}: Already has {existing_count} records")
                return True

            # Look for data files in data/ directory
            # Handle both cases: running from project root or from backend/
            data_dir = "data"
            if not os.path.exists(data_dir):
                data_dir = "../data"
                if not os.path.exists(data_dir):
                    print(f"Data directory not found (tried 'data/' and '../data/')")
                    return False

            # Try JSON first, then CSV
            json_file = os.path.join(data_dir, f"{symbol}.json")
            csv_file = os.path.join(data_dir, f"{symbol}.csv")
            
            if os.path.exists(json_file):
                return self._import_from_json(db, symbol, json_file)
            elif os.path.exists(csv_file):
                return self._import_from_csv(db, symbol, csv_file)
            else:
                print(f"No data file found for {symbol} in {data_dir}/")
                print(f"Expected: {json_file} or {csv_file}")
                return False

        except Exception as e:
            print(f"Error importing data for {symbol}: {e}")
            return False

    def _import_from_json(self, db: Session, symbol: str, file_path: str) -> bool:
        """Import data from JSON file with new structure: {fundamental: {...}, stock: [...]}"""
        try:
            import json
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Check if it's the new combined format
            if isinstance(data, dict) and 'fundamental' in data and 'stock' in data:
                # New format: {fundamental: {...}, stock: [...]}
                fundamental_data = data['fundamental']
                stock_data = data['stock']
                
                # Import fundamental data first
                if fundamental_data:
                    self._ensure_ticker_info(db, symbol, preloaded=fundamental_data)
                
                # Import stock data
                if not isinstance(stock_data, list):
                    print(f"Invalid stock data format for {symbol}: expected list of records")
                    return False
                
                records_added = 0
                for record in stock_data:
                    try:
                        # Parse date - handle both YYYY-MM-DD and YYYYMMDD formats
                        if isinstance(record['date'], str):
                            date_str = record['date']
                            if len(date_str) == 8 and date_str.isdigit():
                                # Format: YYYYMMDD
                                date_obj = datetime.strptime(date_str, '%Y%m%d').date()
                            else:
                                # Format: YYYY-MM-DD
                                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                        else:
                            date_obj = record['date']
                        
                        # Create ticker record
                        ticker_record = TickerData(
                            ticker_symbol=symbol,
                            date=date_obj,
                            open_price=float(record['open']),
                            close_price=float(record['close']),
                            high_price=float(record['high']),
                            low_price=float(record['low']),
                            volume=int(record['volume'])
                        )
                        db.add(ticker_record)
                        records_added += 1
                        
                    except (KeyError, ValueError) as e:
                        print(f"Error parsing record for {symbol}: {e}")
                        continue
                
                db.commit()
                print(f"Imported {records_added} records for {symbol} from JSON (new format)")
                return True
                
            elif isinstance(data, list):
                # Old format: list of dicts with date, open, high, low, close, volume
                records_added = 0
                for record in data:
                    try:
                        # Parse date - handle both YYYY-MM-DD and YYYYMMDD formats
                        if isinstance(record['date'], str):
                            date_str = record['date']
                            if len(date_str) == 8 and date_str.isdigit():
                                # Format: YYYYMMDD
                                date_obj = datetime.strptime(date_str, '%Y%m%d').date()
                            else:
                                # Format: YYYY-MM-DD
                                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                        else:
                            date_obj = record['date']
                        
                        # Create ticker record
                        ticker_record = TickerData(
                            ticker_symbol=symbol,
                            date=date_obj,
                            open_price=float(record['open']),
                            close_price=float(record['close']),
                            high_price=float(record['high']),
                            low_price=float(record['low']),
                            volume=int(record['volume'])
                        )
                        db.add(ticker_record)
                        records_added += 1
                        
                    except (KeyError, ValueError) as e:
                        print(f"Error parsing record for {symbol}: {e}")
                        continue
                
                db.commit()
                print(f"Imported {records_added} records for {symbol} from JSON (old format)")
                return True
            else:
                print(f"Invalid JSON format for {symbol}: expected dict with fundamental/stock or list of records")
                return False
            
        except Exception as e:
            print(f"Error importing from JSON for {symbol}: {e}")
            db.rollback()
            return False

    def _import_from_csv(self, db: Session, symbol: str, file_path: str) -> bool:
        """Import data from CSV file"""
        try:
            import pandas as pd
            
            # Read CSV with pandas
            df = pd.read_csv(file_path)
            
            # Expected columns: date, open, high, low, close, volume
            required_cols = ['date', 'open', 'high', 'low', 'close', 'volume']
            if not all(col in df.columns for col in required_cols):
                print(f"Invalid CSV format for {symbol}: missing required columns")
                print(f"Expected: {required_cols}")
                print(f"Found: {list(df.columns)}")
                return False
            
            records_added = 0
            for _, row in df.iterrows():
                try:
                    # Parse date
                    if isinstance(row['date'], str):
                        date_obj = datetime.strptime(row['date'], '%Y-%m-%d').date()
                    else:
                        date_obj = pd.to_datetime(row['date']).date()
                    
                    # Create ticker record
                    ticker_record = TickerData(
                        ticker_symbol=symbol,
                        date=date_obj,
                        open_price=float(row['open']),
                        close_price=float(row['close']),
                        high_price=float(row['high']),
                        low_price=float(row['low']),
                        volume=int(row['volume'])
                    )
                    db.add(ticker_record)
                    records_added += 1
                    
                except (ValueError, TypeError) as e:
                    print(f"Error parsing row for {symbol}: {e}")
                    continue
            
            db.commit()
            print(f"✅ Imported {records_added} records for {symbol} from CSV")
            return True
            
        except Exception as e:
            print(f"Error importing from CSV for {symbol}: {e}")
            db.rollback()
            return False 

    def _get_close_series(self, db: Session, symbol: str):
        """Return (dates, closes) ascending; filter NaN and non-positive prices."""
        rows = (db.query(TickerData)
                  .filter(TickerData.ticker_symbol == symbol)
                  .order_by(TickerData.date)
                  .all())
        if not rows:
            # Don't print debug for synthetic tickers like PORTFOLIO
            if symbol != "PORTFOLIO":
                print(f"Debug: No TickerData found for {symbol}")
            return [], np.array([])
        dates = [r.date for r in rows]
        closes = np.array([float(r.close_price) for r in rows], dtype=float)
        mask = np.isfinite(closes) & (closes > 0)
        dates = [d for d, m in zip(dates, mask) if m]
        closes = closes[mask]
        print(f"Debug: {symbol} - Found {len(dates)} valid data points, first: {dates[0] if dates else 'N/A'}, last: {dates[-1] if dates else 'N/A'}")
        return dates, closes

    def _log_returns_from_series(self, dates, closes):
        """Return (ret_dates, log_returns); dates shifted by one for diffs."""
        if len(closes) < 2:
            return [], np.array([])
        rets = np.diff(np.log(closes))
        ret_dates = dates[1:]
        return ret_dates, rets

    def get_factor_exposure_data(self, db: Session, username: str = "admin") -> Dict[str, Any]:
        """Get factor exposure data for portfolio analysis with caching"""
        try:
            # Check cache first
            cache_key = self._get_cache_key("factor_exposure_data", username)
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                print(f"Using cached factor exposure data for user: {username}")
                return cached_data
            
            print(f"Getting factor exposure data for user: {username}")
            
            # Get all tickers: user portfolio + static tickers
            all_tickers = self.get_all_tickers(db, username)
            print(f"All tickers: {all_tickers}")
            
            if not all_tickers:
                print("No tickers found")
                result = {"factor_exposures": [], "r2_data": [], "available_factors": [], "available_tickers": []}
                self._set_cache(cache_key, result)
                return result

            # Available factors
            available_factors = ["MARKET", "MOMENTUM", "SIZE", "VALUE", "QUALITY"]
            
            # Get real historical data from database
            factor_exposures = []
            r2_data = []
            
            # Get date range from ticker data
            date_range = db.query(TickerData.date).distinct().order_by(TickerData.date).all()
            dates = [d[0] for d in date_range]
            
            if not dates:
                print("No historical data found in database")
                return {"factor_exposures": [], "r2_data": [], "available_factors": available_factors, "available_tickers": all_tickers}
            
            print(f"Found {len(dates)} dates from {min(dates)} to {max(dates)}")
            
            # Wczytaj serie ETF z bazy (real factor proxies)
            print("Loading ETF data for factor proxies...")
            
            # MARKET proxy
            spy_dates, spy_closes = self._get_close_series(db, "SPY")
            spy_ret_dates, spy_rets = self._log_returns_from_series(spy_dates, spy_closes)
            spy_ret_map = dict(zip(spy_ret_dates, spy_rets))  # date -> r_SPY
            
            # Style factors (market-neutral)
            mtum_dates, mtum_closes = self._get_close_series(db, "MTUM")
            mtum_ret_dates, mtum_rets = self._log_returns_from_series(mtum_dates, mtum_closes)
            mtum_ret_map = dict(zip(mtum_ret_dates, mtum_rets))
            
            iwm_dates, iwm_closes = self._get_close_series(db, "IWM")
            iwm_ret_dates, iwm_rets = self._log_returns_from_series(iwm_dates, iwm_closes)
            iwm_ret_map = dict(zip(iwm_ret_dates, iwm_rets))
            
            vlue_dates, vlue_closes = self._get_close_series(db, "VLUE")
            vlue_ret_dates, vlue_rets = self._log_returns_from_series(vlue_dates, vlue_closes)
            vlue_ret_map = dict(zip(vlue_ret_dates, vlue_rets))
            
            qual_dates, qual_closes = self._get_close_series(db, "QUAL")
            qual_ret_dates, qual_rets = self._log_returns_from_series(qual_dates, qual_closes)
            qual_ret_map = dict(zip(qual_ret_dates, qual_rets))
            
            print(f"ETF data loaded: SPY({len(spy_ret_dates)}), MTUM({len(mtum_ret_dates)}), IWM({len(iwm_ret_dates)}), VLUE({len(vlue_ret_dates)}), QUAL({len(qual_ret_dates)})")
            
            # Calculate factor exposures for each ticker and factor
            for ticker in all_tickers:
                print(f"🔍 Processing {ticker}...")
                
                # Get historical data for this ticker
                ticker_data = (db.query(TickerData)
                                 .filter(TickerData.ticker_symbol == ticker)
                                 .order_by(TickerData.date)
                                 .all())
                
                if len(ticker_data) < 1:
                    print(f"Not enough data for {ticker} ({len(ticker_data)} records)")
                    continue
                
                # Calculate returns for asset
                asset_dates = [row.date for row in ticker_data]
                prices = [row.close_price for row in ticker_data]
                asset_ret_dates, asset_rets = self._log_returns_from_series(asset_dates, prices)
                
                # Calculate rolling betas for each factor
                for factor in available_factors:
                    if factor == "MARKET":
                        # Use real SPY data for MARKET factor
                        common = [d for d in asset_ret_dates if d in spy_ret_map]
                        if len(common) < 5:
                            print(f"Not enough common dates for {ticker} vs SPY ({len(common)} records)")
                            continue
                        
                        # Sort common dates and build vectors for rolling
                        common.sort()
                        a = np.array([asset_rets[asset_ret_dates.index(d)] for d in common])
                        f = np.array([spy_ret_map[d] for d in common])
                        
                        window_size = 60
                        for idx in range(window_size, len(common)):
                            y = a[idx-window_size:idx]
                            x = f[idx-window_size:idx]
                            X = np.column_stack([np.ones(len(x)), x])
                            
                            try:
                                coef = np.linalg.lstsq(X, y, rcond=None)[0]
                                beta = float(coef[1])
                                
                                # R² from this regression
                                y_hat = X @ coef
                                ssr = float(((y - y_hat)**2).sum())
                                sst = float(((y - y.mean())**2).sum())
                                r2 = 1.0 - ssr/sst if sst > 0 else 0.0
                                
                                date = common[idx]
                                factor_exposures.append({
                                    "date": date.isoformat(),
                                    "ticker": ticker,
                                    "factor": factor,
                                    "beta": round(beta, 3)
                                })
                                r2_data.append({
                                    "date": date.isoformat(),
                                    "ticker": ticker,
                                    "r2": round(max(0.0, min(1.0, r2)), 3)
                                })
                            except Exception as e:
                                print(f"Error calculating MARKET beta for {ticker}: {e}")
                                continue
                    
                    elif factor == "MOMENTUM":
                        # Use real MTUM data (market-neutral)
                        common = [d for d in asset_ret_dates if d in mtum_ret_map and d in spy_ret_map]
                        if len(common) < 5:
                            print(f"Not enough common dates for {ticker} vs MTUM ({len(common)} records)")
                            continue
                        
                        common.sort()
                        a = np.array([asset_rets[asset_ret_dates.index(d)] for d in common])
                        f = np.array([mtum_ret_map[d] - spy_ret_map[d] for d in common])  # Market-neutral
                        
                        window_size = 60
                        for idx in range(window_size, len(common)):
                            y = a[idx-window_size:idx]
                            x = f[idx-window_size:idx]
                            X = np.column_stack([np.ones(len(x)), x])
                            
                            try:
                                coef = np.linalg.lstsq(X, y, rcond=None)[0]
                                beta = float(coef[1])
                                
                                # R² from this regression
                                y_hat = X @ coef
                                ssr = float(((y - y_hat)**2).sum())
                                sst = float(((y - y.mean())**2).sum())
                                r2 = 1.0 - ssr/sst if sst > 0 else 0.0
                                
                                date = common[idx]
                                factor_exposures.append({
                                    "date": date.isoformat(),
                                    "ticker": ticker,
                                    "factor": factor,
                                    "beta": round(beta, 3)
                                })
                                r2_data.append({
                                    "date": date.isoformat(),
                                    "ticker": ticker,
                                    "r2": round(max(0.0, min(1.0, r2)), 3)
                                })
                            except Exception as e:
                                print(f"Error calculating MOMENTUM beta for {ticker}: {e}")
                                continue
                    
                    elif factor == "SIZE":
                        # Use real IWM data (market-neutral)
                        common = [d for d in asset_ret_dates if d in iwm_ret_map and d in spy_ret_map]
                        if len(common) < 5:
                            print(f"Not enough common dates for {ticker} vs IWM ({len(common)} records)")
                            continue
                        
                        common.sort()
                        a = np.array([asset_rets[asset_ret_dates.index(d)] for d in common])
                        f = np.array([iwm_ret_map[d] - spy_ret_map[d] for d in common])  # Market-neutral
                        
                        window_size = 60
                        for idx in range(window_size, len(common)):
                            y = a[idx-window_size:idx]
                            x = f[idx-window_size:idx]
                            X = np.column_stack([np.ones(len(x)), x])
                            
                            try:
                                coef = np.linalg.lstsq(X, y, rcond=None)[0]
                                beta = float(coef[1])
                                
                                # R² from this regression
                                y_hat = X @ coef
                                ssr = float(((y - y_hat)**2).sum())
                                sst = float(((y - y.mean())**2).sum())
                                r2 = 1.0 - ssr/sst if sst > 0 else 0.0
                                
                                date = common[idx]
                                factor_exposures.append({
                                    "date": date.isoformat(),
                                    "ticker": ticker,
                                    "factor": factor,
                                    "beta": round(beta, 3)
                                })
                                r2_data.append({
                                    "date": date.isoformat(),
                                    "ticker": ticker,
                                    "r2": round(max(0.0, min(1.0, r2)), 3)
                                })
                            except Exception as e:
                                print(f"Error calculating SIZE beta for {ticker}: {e}")
                                continue
                    
                    elif factor == "VALUE":
                        # Use real VLUE data (market-neutral)
                        common = [d for d in asset_ret_dates if d in vlue_ret_map and d in spy_ret_map]
                        if len(common) < 5:
                            print(f"Not enough common dates for {ticker} vs VLUE ({len(common)} records)")
                            continue
                        
                        common.sort()
                        a = np.array([asset_rets[asset_ret_dates.index(d)] for d in common])
                        f = np.array([vlue_ret_map[d] - spy_ret_map[d] for d in common])  # Market-neutral
                        
                        window_size = 60
                        for idx in range(window_size, len(common)):
                            y = a[idx-window_size:idx]
                            x = f[idx-window_size:idx]
                            X = np.column_stack([np.ones(len(x)), x])
                            
                            try:
                                coef = np.linalg.lstsq(X, y, rcond=None)[0]
                                beta = float(coef[1])
                                
                                # R² from this regression
                                y_hat = X @ coef
                                ssr = float(((y - y_hat)**2).sum())
                                sst = float(((y - y.mean())**2).sum())
                                r2 = 1.0 - ssr/sst if sst > 0 else 0.0
                                
                                date = common[idx]
                                factor_exposures.append({
                                    "date": date.isoformat(),
                                    "ticker": ticker,
                                    "factor": factor,
                                    "beta": round(beta, 3)
                                })
                                r2_data.append({
                                    "date": date.isoformat(),
                                    "ticker": ticker,
                                    "r2": round(max(0.0, min(1.0, r2)), 3)
                                })
                            except Exception as e:
                                print(f"Error calculating VALUE beta for {ticker}: {e}")
                                continue
                    
                    elif factor == "QUALITY":
                        # Use real QUAL data (market-neutral)
                        common = [d for d in asset_ret_dates if d in qual_ret_map and d in spy_ret_map]
                        if len(common) < 5:
                            print(f"Not enough common dates for {ticker} vs QUAL ({len(common)} records)")
                            continue
                        
                        common.sort()
                        a = np.array([asset_rets[asset_ret_dates.index(d)] for d in common])
                        f = np.array([qual_ret_map[d] - spy_ret_map[d] for d in common])  # Market-neutral
                        
                        window_size = 60
                        for idx in range(window_size, len(common)):
                            y = a[idx-window_size:idx]
                            x = f[idx-window_size:idx]
                            X = np.column_stack([np.ones(len(x)), x])
                            
                            try:
                                coef = np.linalg.lstsq(X, y, rcond=None)[0]
                                beta = float(coef[1])
                                
                                # R² from this regression
                                y_hat = X @ coef
                                ssr = float(((y - y_hat)**2).sum())
                                sst = float(((y - y.mean())**2).sum())
                                r2 = 1.0 - ssr/sst if sst > 0 else 0.0
                                
                                date = common[idx]
                                factor_exposures.append({
                                    "date": date.isoformat(),
                                    "ticker": ticker,
                                    "factor": factor,
                                    "beta": round(beta, 3)
                                })
                                r2_data.append({
                                    "date": date.isoformat(),
                                    "ticker": ticker,
                                    "r2": round(max(0.0, min(1.0, r2)), 3)
                                })
                            except Exception as e:
                                print(f"Error calculating QUALITY beta for {ticker}: {e}")
                                continue
                    
                    else:
                        # Fallback to mock data for unknown factors
                        for i, date in enumerate(dates):
                            if i < 30:  # Need at least 30 days for rolling calculation
                                continue
                                
                            # Simulate factor returns
                            factor_returns = np.random.normal(0, 0.02, i)
                            
                            # Calculate rolling beta using last 60 days
                            window_size = min(60, i)
                            if window_size < 30:
                                continue
                                
                            # Simple rolling regression
                            y = asset_rets[-window_size:] if len(asset_rets) >= window_size else asset_rets
                            x = factor_returns[-window_size:] if len(factor_returns) >= window_size else factor_returns
                            
                            if len(y) != len(x):
                                continue
                            
                            # Add constant for regression
                            x_with_const = np.column_stack([np.ones(len(x)), x])
                            
                            try:
                                # OLS regression
                                beta, r2 = ols_beta(y, x)
                                
                                factor_exposures.append({
                                    "date": date.isoformat(),
                                    "ticker": ticker,
                                    "factor": factor,
                                    "beta": round(beta, 3)
                                })
                                
                                # Add R² data
                                r2_data.append({
                                    "date": date.isoformat(),
                                    "ticker": ticker,
                                    "factor": factor,
                                    "r2": round(r2, 3)
                                })
                            except:
                                # Fallback to simulated beta
                                base_beta = {
                                    "MOMENTUM": 0.3,
                                    "SIZE": -0.2,
                                    "VALUE": 0.1,
                                    "QUALITY": 0.4
                                }.get(factor, 0.0)
                                
                                time_factor = (date.year - 2016) / 10
                                noise = np.random.normal(0, 0.1)
                                trend = np.sin(time_factor * np.pi) * 0.3
                                
                                beta = base_beta + noise + trend
                                
                                factor_exposures.append({
                                    "date": date.isoformat(),
                                    "ticker": ticker,
                                    "factor": factor,
                                    "beta": round(beta, 3)
                                })
            
            print(f"Generated {len(factor_exposures)} factor exposures and {len(r2_data)} R² records")
            
            # Limit the number of records per (ticker, factor) pair to prevent memory issues
            MAX_PER_PAIR = 400  # 400×5 factors ≈ 2000 na ticker
            from collections import defaultdict
            trimmed_exposures = defaultdict(list)  # klucz = (ticker, factor)
            trimmed_r2 = defaultdict(list)
            
            for row in factor_exposures:
                k = (row["ticker"], row["factor"])
                if len(trimmed_exposures[k]) < MAX_PER_PAIR:
                    trimmed_exposures[k].append(row)
            
            for row in r2_data:
                if len(trimmed_r2[row["ticker"]]) < MAX_PER_PAIR:
                    trimmed_r2[row["ticker"]].append(row)
            
            factor_exposures = [r for sub in trimmed_exposures.values() for r in sub]
            r2_data = [r for sub in trimmed_r2.values() for r in sub]
            
            print(f"After trimming: {len(factor_exposures)} factor exposures and {len(r2_data)} R² records")
            
            # Get common date range for all tickers
            common_date_range = self._get_common_date_range(db, all_tickers)
            
            result = {
                "factor_exposures": factor_exposures,
                "r2_data": r2_data,
                "available_factors": available_factors,
                "available_tickers": all_tickers,
                "common_date_range": common_date_range
            }
            
            # Cache the result
            self._set_cache(cache_key, result)
            
            return result
            
        except Exception as e:
            print(f"Error getting factor exposure data: {e}")
            error_result = {"factor_exposures": [], "r2_data": [], "available_factors": [], "available_tickers": []}
            self._set_cache(cache_key, error_result)
            return error_result 

    def get_concentration_risk_data(self, db: Session, username: str = "admin") -> Dict[str, Any]:
        """Get concentration risk data for portfolio analysis with caching"""
        try:
            # Check cache first
            cache_key = self._get_cache_key("concentration_risk_data", username)
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                print(f"Using cached concentration risk data for user: {username}")
                return cached_data
            
            print(f"Getting concentration risk data for user: {username}")
            
            # Get user's portfolio with shares
            user = db.query(User).filter(User.username == username).first()
            if not user:
                result = {"error": "User not found"}
                self._set_cache(cache_key, result)
                return result
            
            portfolio_items = db.query(Portfolio).filter(Portfolio.user_id == user.id).all()
            if not portfolio_items:
                result = {"error": "No portfolio found"}
                self._set_cache(cache_key, result)
                return result
            
            # Get current prices and calculate market values
            portfolio_data = []
            total_mv = 0.0
            
            for item in portfolio_items:
                ticker = item.ticker_symbol
                shares = item.shares
                
                # Get latest price
                latest_data = (db.query(TickerData)
                                 .filter(TickerData.ticker_symbol == ticker)
                                 .order_by(TickerData.date.desc())
                                 .first())
                
                if latest_data:
                    price = float(latest_data.close_price)
                    market_value = price * shares
                    total_mv += market_value
                    
                    portfolio_data.append({
                        'ticker': ticker,
                        'shares': shares,
                        'price': price,
                        'market_value': market_value,
                        'weight': 0.0  # Will calculate after total
                    })
            
            if total_mv == 0:
                return {"error": "No market value data"}
            
            # 1) Wagi (frakcje i %)
            for item in portfolio_data:
                w = item['market_value'] / total_mv
                item['weight_frac'] = w
                item['weight'] = w * 100.0  # do UI
            
            # 2) sort by descending weight
            portfolio_data.sort(key=lambda x: x['weight'], reverse=True)
            
            # 3) KPI koncentracji
            w_frac = np.array([it['weight_frac'] for it in portfolio_data])
            largest_position, top3, top5, top10, hhi, effective_positions = concentration_metrics(w_frac)
            
            # Get real sector and market cap data from database/IBKR
            for item in portfolio_data:
                ticker = item['ticker']
                try:
                    info = self._ensure_ticker_info(db, ticker)
                    item['sector'] = info.sector if info and info.sector else 'Unknown'
                    item['industry'] = info.industry if info and info.industry else 'Unknown'
                    item['market_cap'] = info.market_cap if info and info.market_cap else 0.0
                except Exception as e:
                    item['sector'] = 'Unknown'
                    item['industry'] = 'Unknown'
                    item['market_cap'] = 0.0
            
            # 4) Sektor (agregacja po frakcjach!)
            sector_w = defaultdict(float)
            for it in portfolio_data:
                s = it.get('sector', 'Unknown')
                sector_w[s] += it['weight_frac']
            
            sector_concentration = {
                'sectors': list(sector_w.keys()),
                'weights': [v*100.0 for v in sector_w.values()],   # %
            }
            hhi_sec = sum(v*v for v in sector_w.values())          # on fractions
            sector_concentration['hhi'] = hhi_sec
            sector_concentration['effective_sectors'] = 1.0/hhi_sec if hhi_sec>0 else 0.0
            
            # 5) Market Cap Concentration (NOWE!)
            def get_market_cap_category(market_cap: float) -> str:
                """Categorize companies by market cap size"""
                if market_cap >= 200_000_000_000:  # 200B+
                    return "Mega Cap"
                elif market_cap >= 10_000_000_000:  # 10B-200B
                    return "Large Cap"
                elif market_cap >= 2_000_000_000:   # 2B-10B
                    return "Mid Cap"
                elif market_cap >= 300_000_000:     # 300M-2B
                    return "Small Cap"
                elif market_cap >= 50_000_000:      # 50M-300M
                    return "Micro Cap"
                elif market_cap >= 10_000_000:      # 10M-50M
                    return "Nano Cap"
                else:
                    return "Micro Cap"
            
            # Group by market cap category
            market_cap_w = defaultdict(float)
            market_cap_details = defaultdict(list)
            
            for it in portfolio_data:
                market_cap = it.get('market_cap', 0.0)
                category = get_market_cap_category(market_cap)
                market_cap_w[category] += it['weight_frac']
                market_cap_details[category].append({
                    'ticker': it['ticker'],
                    'market_cap': market_cap,
                    'weight': it['weight'],
                    'market_value': it['market_value']
                })
            
            market_cap_concentration = {
                'categories': list(market_cap_w.keys()),
                'weights': [v*100.0 for v in market_cap_w.values()],  # %
                'details': dict(market_cap_details)
            }
            hhi_mc = sum(v*v for v in market_cap_w.values())
            market_cap_concentration['hhi'] = hhi_mc
            market_cap_concentration['effective_categories'] = 1.0/hhi_mc if hhi_mc>0 else 0.0
            
            print(f"Calculated concentration metrics for {len(portfolio_data)} positions")
            
            result = {
                "portfolio_data": portfolio_data,  # zawiera 'weight' (%) i 'weight_frac'
                "concentration_metrics": {
                    "largest_position": round(largest_position * 100, 1),  # Convert to percentage
                    "top_3_concentration": round(top3 * 100, 1),
                    "top_5_concentration": round(top5 * 100, 1),
                    "top_10_concentration": round(top10 * 100, 1),
                    "herfindahl_index": round(hhi, 4),              # 0-1
                    "effective_positions": round(effective_positions, 1)
                },
                "sector_concentration": sector_concentration,
                "market_cap_concentration": market_cap_concentration,
                "total_market_value": total_mv
            }
            
            # Cache the result
            self._set_cache(cache_key, result)
            
            return result
            
        except Exception as e:
            print(f"Error calculating concentration risk: {e}")
            error_result = {"error": str(e)}
            self._set_cache(cache_key, error_result)
            return error_result

    def _get_return_series_map(self, db: Session, symbols: List[str], lookback_days: int = 120):
        """Zwraca dict: symbol -> (dates, returns) z ostatnich ~lookback dni. Prosto i szybko."""
        ret_map = {}
        for s in symbols:
            # skip pseudo symbols
            if s in ("PORTFOLIO", None, ""):
                ret_map[s] = ([], np.array([]))
                continue
                
            print(f"Debug: Getting data for {s}")
            dates, closes = self._get_close_series(db, s)
            print(f"Debug: {s} - dates: {len(dates)}, closes: {len(closes)}")
            if len(closes) < 2:
                print(f"Debug: {s} - insufficient data")
                ret_map[s] = ([], np.array([]))
                continue
            # trim tail (last ~lookback days)
            dates = dates[-(lookback_days+2):]
            closes = closes[-(lookback_days+2):]
            rd, r = self._log_returns_from_series(dates, closes)
            print(f"Debug: {s} - returns: {len(r)}")
            ret_map[s] = (rd, r)
        return ret_map

    def _align_on_reference(self, ret_map, symbols, ref_symbol="SPY", min_obs=40):
        """
        Zwraca: (dates_ref, M[T x N] z NaN, active_syms)
        Kalendarz = daty SPY (ostatnie dostępne), kolumny = symbole z >= min_obs wspólnych punktów vs SPY.
        """
        if ref_symbol not in ret_map:
            return [], np.empty((0, 0)), []
        dates_ref, r_ref = ret_map[ref_symbol]
        if len(dates_ref) == 0:
            return [], np.empty((0, 0)), []

        idx_ref = {d:i for i, d in enumerate(dates_ref)}
        T = len(dates_ref)
        cols = []
        X = []

        for s in symbols:
            if s == ref_symbol or s not in ret_map:
                continue
            dts, r = ret_map[s]
            if len(r) == 0:
                continue
            # align na kalendarz SPY
            x = np.full(T, np.nan, dtype=float)
            idx_s = {d:i for i, d in enumerate(dts)}
            common = [d for d in dates_ref if d in idx_s]
            if len(common) >= min_obs:
                for d in common:
                    x[idx_ref[d]] = r[idx_s[d]]
                cols.append(s)
                X.append(x)

        if not cols:
            return [], np.empty((0, 0)), []

        M = np.column_stack(X)  # [T x N] z NaN
        return dates_ref, M, cols

    def _portfolio_series_with_coverage(self, dates, R, weights_map, symbols, min_weight_cov=0.6):
        """
        Liczy serię portfela po kalendarzu 'dates', renormalizując wagi
        w każdym dniu po dostępnych papierach. R – [T x N] z NaN.
        Zwraca (dates_used, rp), gdzie day coverage >= min_weight_cov.
        """
        if R.size == 0:
            return [], np.array([])
        N = R.shape[1]
        # wagi w kolejności kolumn
        w_full = np.array([weights_map.get(s, 0.0) for s in symbols], dtype=float)
        w_full = w_full / (w_full.sum() if w_full.sum() > 0 else 1.0)

        rp = []
        used_dates = []
        for t in range(R.shape[0]):
            row = R[t, :]
            mask = np.isfinite(row)
            cov = w_full[mask].sum()
            if cov >= min_weight_cov and mask.any():
                w_t = w_full[mask] / cov
                rp.append(float((row[mask] * w_t).sum()))
                used_dates.append(dates[t])
        return used_dates, np.array(rp, dtype=float)

    def _pairwise_corr_nan_safe(self, R: np.ndarray, min_periods: int = 30):
        """
        Zwraca (avg_corr, total_pairs, high_pairs>=0.7) licząc korelacje pairwise na wspólnych datach.
        """
        if R.size == 0:
            return 0.0, 0, 0
        N = R.shape[1]
        vals = []
        high = 0
        for i in range(N):
            xi = R[:, i]
            for j in range(i+1, N):
                xj = R[:, j]
                m = np.isfinite(xi) & np.isfinite(xj)
                if m.sum() >= min_periods:
                    c = np.corrcoef(xi[m], xj[m])[0, 1]
                    if np.isfinite(c):
                        vals.append(c)
                        if c >= 0.7:
                            high += 1
        if not vals:
            return 0.0, 0, 0
        return float(np.mean(vals)), len(vals), int(high)

    def _intersect_and_stack(self, ret_map: Dict[str, Any], symbols: List[str]):
        """Return (dates, R, active) with common dates; R is [T x N] by symbols."""
        print(f"Debug: Intersecting {symbols}")
        print(f"Debug: ret_map keys: {list(ret_map.keys())}")
        for s in symbols:
            if s in ret_map:
                dates, returns = ret_map[s]
                print(f"Debug: {s} - dates: {len(dates)}, returns: {len(returns)}")
            else:
                print(f"Debug: {s} - not in ret_map")
        result = stack_common_returns(ret_map, symbols)
        print(f"Debug: Result - dates: {len(result[0])}, R shape: {result[1].shape}, active: {result[2]}")
        return result
    
    def _get_common_date_range(self, db: Session, symbols: List[str]) -> Dict[str, Any]:
        """Find common date range for all tickers."""
        try:
            all_dates = []
            for symbol in symbols:
                dates, _ = self._get_close_series(db, symbol)
                if dates:
                    all_dates.extend(dates)
            
            if not all_dates:
                return {"start_date": None, "end_date": None, "total_days": 0}
            
            # find common range
            min_date = min(all_dates)
            max_date = max(all_dates)
            
            # safe day-diff calc
            total_days = 0
            if min_date and max_date:
                try:
                    total_days = (max_date - min_date).days
                except:
                    total_days = 0
            
            return {
                "start_date": min_date.isoformat() if min_date else None,
                "end_date": max_date.isoformat() if max_date else None,
                "total_days": total_days
            }
        except Exception as e:
            print(f"Error getting common date range: {e}")
            return {"start_date": None, "end_date": None, "total_days": 0}

    def get_risk_scoring(self, db: Session, username: str = "admin") -> Dict[str, Any]:
        """Compute risk scoring metrics for the user's portfolio.

        Args/Inputs:
            db (Session): SQLAlchemy database session.
            username (str): Username for which to compute risk scoring.

        Provides:
            Portfolio risk metrics based on recent returns and exposures.

        Returns:
            Dict[str, Any]: Risk scoring results or error message.
        """
        print(f"[RISK-SCORING] Starting risk scoring for user: {username}")
        # 1) user weights and tickers list
        print(f"[RISK-SCORING] Getting concentration risk data...")
        conc = self.get_concentration_risk_data(db, username)
        if "error" in conc: 
            print(f"[RISK-SCORING] Error in concentration risk: {conc['error']}")
            return {"error": conc["error"]}
        positions = conc["portfolio_data"]
        if not positions:
            print(f"[RISK-SCORING] No positions found")
            return {"error":"No positions"}
        tickers = [p['ticker'] for p in positions]
        w = np.array([p['weight_frac'] for p in positions], dtype=float)  # sum ~1
        print(f"[RISK-SCORING] Portfolio tickers: {tickers}, weights sum: {w.sum():.4f}")

        # 2) return series: tickers + SPY + factor ETFs
        factor_proxies = {"MOMENTUM":"MTUM","SIZE":"IWM","VALUE":"VLUE","QUALITY":"QUAL"}
        needed = list(set(tickers + ["SPY"] + list(factor_proxies.values())))
        print(f"[RISK-SCORING] Getting return series for: {needed}")
        ret_map = self._get_return_series_map(db, needed, lookback_days=180)

        # 3) position returns matrix, align on SPY calendar
        print(f"[RISK-SCORING] Aligning returns on SPY calendar...")
        dates_ref, R_all, active = self._align_on_reference(ret_map, tickers + ["SPY"], ref_symbol="SPY", min_obs=40)
        if R_all.size == 0 or len(dates_ref) < 40:
            print(f"[RISK-SCORING] Insufficient overlapping history (vs SPY)")
            return {"error":"Insufficient overlapping history (vs SPY)"}
        print(f"[RISK-SCORING] Aligned data shape: {R_all.shape}, active symbols: {active}")

        # wagi na aktywne
        w_map = {p["ticker"]: p["weight_frac"] for p in positions}
        # seria portfela z pokryciem >=60%
        dates_win, rp = self._portfolio_series_with_coverage(dates_ref, R_all, w_map, active, min_weight_cov=0.60)
        if len(rp) < 40:
            return {"error": "Too few portfolio days after coverage filter"}

        # SPY na te daty:
        d_spy, r_spy_full = ret_map.get("SPY", ([], np.array([])))
        idx_spy = {d:i for i,d in enumerate(d_spy)}
        r_spy = np.array([r_spy_full[idx_spy[d]] for d in dates_win if d in idx_spy], dtype=float)
        # dopasuj rp do tych samych dat (mogło odpaść kilka dni)
        dates_common = [d for d in dates_win if d in idx_spy]
        rp_win = np.array([rp[dates_win.index(d)] for d in dates_common], dtype=float)
        if len(rp_win) < 30 or len(r_spy) < 30:
            return {"error":"Insufficient market overlap"}

        # 4) raw metrics
        # vol ann
        sigma_ann = annualized_vol(rp_win)
        # market beta
        beta_mkt = ols_beta(rp_win, r_spy)[0]

        # factors alignment
        betas = {}
        for fac, etf in factor_proxies.items():
            d_f, r_f_full = ret_map.get(etf, ([], np.array([])))
            f_idx = {d:i for i,d in enumerate(d_f)}
            dates_fac = [d for d in dates_common if d in f_idx]
            if len(dates_fac) < 30:
                betas[fac] = 0.0
                continue
            rf = np.array([r_f_full[f_idx[d]] for d in dates_fac], dtype=float)
            rs = np.array([r_spy[dates_common.index(d)] for d in dates_fac], dtype=float)
            rp_fac = np.array([rp_win[dates_common.index(d)] for d in dates_fac], dtype=float)
            f_mn = rf - rs
            betas[fac] = ols_beta(rp_fac, f_mn)[0]

        # 5) korelacje pairwise na tym samym oknie (ostatnie 60 dni z kalendarza ref)
        win = min(60, len(dates_ref))
        R_win = R_all[-win:, :]
        avg_corr, pairs, high_pairs = self._pairwise_corr_nan_safe(R_win, min_periods=30)

        # max drawdown on rp_win
        _, max_dd = drawdown(rp_win)

        # 5) concentration (HHI, Neff)
        hhi = float(conc["concentration_metrics"]["herfindahl_index"])  # already in [0..1]
        neff = float(conc["concentration_metrics"]["effective_positions"])

        # 5a) worst historical scenario (stress test)
        stress = self.get_historical_scenarios(db, username)
        worst_loss = 0.0
        if "results" in stress:
            losses = [-r["return_pct"] for r in stress["results"] if r["return_pct"] < 0]
            if losses:
                worst_loss = max(losses) / 100.0     # fraction, e.g. 0.07 = -7%

        # 6) skoring (0..1)
        raw_metrics = {
            "hhi": hhi,
            "vol_ann_pct": sigma_ann * 100,
            "beta_market": beta_mkt,
            "avg_pair_corr": avg_corr,
            "max_drawdown_pct": max_dd * 100,
            "factor_l1": sum(abs(betas[k]) for k in betas),
            "stress_loss_pct": worst_loss           # <-- NOWE!
        }
        
        WEIGHTS = {
            "concentration": 0.25,
            "volatility":    0.20,
            "factor":        0.20,
            "correlation":   0.15,
            "market":        0.10,
            "stress":        0.10,
        }
        
        scores, contrib_pct = risk_mix(raw_metrics, NORMALIZATION, WEIGHTS)

        # 7) alerty „jak na screenie"
        alerts = []
        # Drawdown
        if max_dd < -0.2:
            sev = "HIGH"
        elif max_dd < -0.1:
            sev = "MEDIUM"
        else:
            sev = None
        if sev:
            alerts.append({"severity": sev, "text": f"Drawdown Risk: Maximum drawdown ({max_dd*100:.1f}%) is significant"})
        # Market
        if abs(beta_mkt) > 0.8:
            alerts.append({"severity":"MEDIUM","text": f"Factor Exposure: High exposure to MARKET factor (beta: {beta_mkt:.2f})"})
        # Others
        for fac in ["SIZE","VALUE","MOMENTUM","QUALITY"]:
            b = betas.get(fac, 0.0)
            if abs(b) > 0.5:
                alerts.append({"severity":"MEDIUM","text": f"Factor Exposure: High exposure to {fac} factor (beta: {b:.2f})"})
        if high_pairs >= 2:
            alerts.append({"severity":"MEDIUM","text": f"Correlation Risk: {high_pairs} pairs with correlation > 0.7"})

        # 8) rekomendacje (proste)
        recs = []
        top_comp = max(contrib_pct, key=contrib_pct.get)
        if top_comp == "concentration" and neff < 8:
            recs.append("Reduce concentration: increase number of effective positions (>8).")
        if abs(beta_mkt) > 0.8:
            recs.append("Trim market beta towards 0.6–0.8 (hedge or rotate).")
        if avg_corr > 0.5:
            recs.append("Add diversifiers to lower average pairwise correlation (<0.4).")

        return {
            "score_weights": WEIGHTS,
            "component_scores": scores,                 # 0..1
            "risk_contribution_pct": contrib_pct,       # do pie chart
            "alerts": alerts,
            "recommendations": recs,
            "raw_metrics": {
                "hhi": hhi, "n_eff": neff,
                "vol_ann_pct": sigma_ann*100.0,
                "beta_market": beta_mkt,
                "avg_pair_corr": avg_corr,
                "pairs_total": pairs,
                "pairs_high_corr": high_pairs,
                "max_drawdown_pct": max_dd*100.0
            }
        }

    def _get_returns_between_dates(self, db: Session, symbol: str, start_d: date, end_d: date):
        """Return (dates, log_returns) in [start_d, end_d] for symbol; may return []."""
        rows = (db.query(TickerData)
                  .filter(TickerData.ticker_symbol == symbol,
                          TickerData.date >= start_d,
                          TickerData.date <= end_d)
                  .order_by(TickerData.date)
                  .all())
        if len(rows) < 2:
            return [], np.array([])
        dts = [r.date for r in rows]
        closes = np.array([float(r.close_price) for r in rows], dtype=float)
        rd, rets = self._log_returns_from_series(dts, closes)
        return rd, rets

        # _clamp moved to backend.quant.risk

    def _portfolio_snapshot(self, db: Session, username: str = "admin"):
        """Return list of (ticker, weight_frac)."""
        conc = self.get_concentration_risk_data(db, username)
        if "error" in conc: 
            return [], 0.0
        positions = conc["portfolio_data"]
        w_sum = sum(p.get("weight_frac", 0.0) for p in positions)
        if w_sum <= 0:
            return [], 0.0
        # normalize for safety
        for p in positions:
            p["weight_frac"] = float(p["weight_frac"]) / w_sum
        return positions, 1.0

    def get_market_regime(self, db: Session, username: str = "admin") -> Dict[str, Any]:
        """Regime = vol/corr/mom na ostatnich ~60d + etykieta."""
        positions, ok = self._portfolio_snapshot(db, username)
        if not ok or not positions:
            return {"error":"No positions"}

        tickers = [p["ticker"] for p in positions]
        w_map = {p["ticker"]: p["weight_frac"] for p in positions}

        # zwroty z ostatnich dni + SPY jako referencja
        lookback = STRESS_LIMITS["lookback_regime_days"] + 2
        needed = tickers + ["SPY"]
        ret_map = self._get_return_series_map(db, needed, lookback_days=lookback)

        # align on SPY instead of full intersection
        dates_ref, R, active = self._align_on_reference(ret_map, needed, ref_symbol="SPY", min_obs=30)
        if R.size == 0 or len(dates_ref) < 40:
            return {"error":"Insufficient data for regime"}

        # reweight on active names
        w = np.array([w_map.get(s, 0.0) for s in active], dtype=float)
        w = w / (w.sum() if w.sum() > 0 else 1.0)

        R = clamp(R, STRESS_LIMITS["clamp_return_abs"])
        window = STRESS_LIMITS["lookback_regime_days"]
        R_win = R[-window:, :]

        # Calculate regime metrics
        vol_ann, avg_corr, mom, radar, label = regime_metrics(R_win, w, REGIME_THRESH)

        return {
            "label": label,
            "volatility_pct": vol_ann * 100.0,
            "correlation": avg_corr,
            "momentum_pct": mom * 100.0,
            "radar": radar
        }

    def get_historical_scenarios(self, db: Session, username: str = "admin",
                                 scenarios: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Compute PnL/DD for historical scenarios; skip low-coverage/too-short ones."""
        positions, ok = self._portfolio_snapshot(db, username)
        if not ok or not positions:
            return {"error":"No positions"}

        tickers = [p["ticker"] for p in positions]
        w_map = {p["ticker"]: p["weight_frac"] for p in positions}

        scenarios = scenarios or STRESS_SCENARIOS
        analyzed, excluded = [], []

        for sc in scenarios:
            name, start_d, end_d = sc["name"], sc["start"], sc["end"]

            # pobierz zwroty w oknie + SPY jako referencja
            ret_map = {}
            included, w_cov = [], 0.0
            for t in tickers:
                dts, r = self._get_returns_between_dates(db, t, start_d, end_d)
                if len(r) >= 2:  # minimalnie
                    ret_map[t] = (dts, r)
                    included.append(t)
                    w_cov += w_map.get(t, 0.0)

            # add SPY as reference calendar
            d_spy, r_spy = self._get_returns_between_dates(db, "SPY", start_d, end_d)
            if len(r_spy) >= STRESS_LIMITS["scenario_min_days"]:
                ret_map["SPY"] = (d_spy, r_spy)

            if w_cov < STRESS_LIMITS["scenario_min_weight_coverage"]:
                excluded.append({"name": name, "reason": f"Low weight coverage ({w_cov*100:.0f}%)"})
                continue

            if not included:
                excluded.append({"name": name, "reason": "No overlapping data"})
                continue

            # align on SPY instead of full intersection
            dates_ref, R, active = self._align_on_reference(
                ret_map, included + ["SPY"], ref_symbol="SPY",
                min_obs=STRESS_LIMITS["scenario_min_days"]
            )
            if R.size == 0 or len(dates_ref) < STRESS_LIMITS["scenario_min_days"]:
                excluded.append({"name": name, "reason": "Too few aligned dates"})
                continue

            # build portfolio series with per-day weight renormalization + coverage
            dates_used, rp = self._portfolio_series_with_coverage(
                dates_ref, R, w_map, active,
                min_weight_cov=STRESS_LIMITS["scenario_min_weight_coverage"]
            )
            if len(rp) < STRESS_LIMITS["scenario_min_days"]:
                excluded.append({"name": name, "reason": "Coverage below threshold after alignment"})
                continue

            # compute PnL / DD from rp (log-returns)
            ret_pct = (np.exp(rp.sum()) - 1.0) * 100.0
            _, max_dd = drawdown(rp)
            max_dd *= 100.0

            analyzed.append({
                "name": name,
                "start": start_d.isoformat(),
                "end": end_d.isoformat(),
                "days": len(dates_used),
                "weight_coverage_pct": w_cov * 100.0,
                "return_pct": ret_pct,
                "max_drawdown_pct": max_dd
            })

        return {
            "scenarios_analyzed": len(analyzed),
            "scenarios_excluded": len(excluded),
            "results": analyzed,
            "excluded": excluded
        }

    def get_stress_testing(self, db: Session, username: str = "admin") -> Dict[str, Any]:
        """Frontend wrapper – combine Market Regime and Historical Scenarios."""
        regime = self.get_market_regime(db, username)
        scenarios = self.get_historical_scenarios(db, username)
        return {
            "market_regime": regime,
            "scenarios": scenarios
        } 

    def build_covariance_matrix(self, db: Session, tickers: List[str], vol_model: str = 'EWMA (5D)') -> np.ndarray:
        """Build covariance matrix Σ = D ρ D where D = diag(σ) and ρ is correlation matrix"""
        if not tickers:
            return np.empty((0, 0))
        
        print(f"[COV-MATRIX] Building for tickers: {tickers}")
        
        # Get volatility forecasts for each ticker
        vol_vec = []
        for ticker in tickers:
            metrics = self.calculate_volatility_metrics(db, ticker, vol_model)
            vol = metrics.get('volatility_pct', 8.0) / 100.0  # Convert to fraction
            vol_vec.append(max(vol, 0.005))  # Floor at 0.5%
        
        vol_vec = np.array(vol_vec)
        D = np.diag(vol_vec)  # D = diag(σ)
        
        # Get historical returns for correlation calculation
        ret_map = self._get_return_series_map(db, list(set(tickers + ["SPY"])), lookback_days=252)  # 1 year
        
        # Use _align_on_reference instead of _intersect_and_stack for better robustness
        dates, R, active = self._align_on_reference(ret_map, list(set(tickers + ["SPY"])), ref_symbol="SPY", min_obs=40)
        
        if R.size == 0 or len(dates) < 60:
            print("Warning: Insufficient data for correlation, using diagonal matrix")
            corr_matrix = np.eye(len(tickers))
        else:
            # pairwise corr z Pandas + PD-clip
            import pandas as pd
            df = pd.DataFrame(R, index=dates, columns=active)
            C_df = df.corr(min_periods=40)
            
            # reindex do pełnego porządku "tickers"
            C_df = C_df.reindex(index=tickers, columns=tickers)
            C_df = C_df.fillna(0.0)
            np.fill_diagonal(C_df.values, 1.0)
            C = C_df.values
            
            # zamień NaN na 0 (brak info) i napraw PD
            C = np.nan_to_num(C, nan=0.0)
            C = 0.5*(C + C.T)
            # PD-clip
            eigvals, eigvecs = np.linalg.eigh(C)
            eigvals = np.clip(eigvals, 1e-6, None)
            C = eigvecs @ np.diag(eigvals) @ eigvecs.T
            # normalizacja diagonali
            d = np.sqrt(np.clip(np.diag(C), 1e-12, None))
            C = C / np.outer(d, d)
            np.fill_diagonal(C, 1.0)
            corr_matrix = C
        
        # Build covariance matrix using quant.risk
        cov_matrix = build_cov(vol_vec, corr_matrix)
        print(f"[COV-MATRIX] Final covariance matrix shape: {cov_matrix.shape}")
        return cov_matrix

    # calculate_risk_contribution moved to quant.risk

    def get_forecast_risk_contribution(self, db: Session, username: str = "admin", 
                                      vol_model: str = 'EWMA (5D)', tickers: List[str] = None,
                                      include_portfolio_bar: bool = True) -> Dict[str, Any]:
        """Get Forecast Risk Contribution data for portfolio"""
        try:
            print(f"[FORECAST-RISK] Starting with tickers: {tickers}, include_portfolio_bar: {include_portfolio_bar}")
            
            # Get portfolio data
            conc = self.get_concentration_risk_data(db, username)
            if "error" in conc:
                return {"error": conc["error"]}

            portfolio_data = conc["portfolio_data"]
            if not portfolio_data:
                return {"error": "No portfolio data"}

            # Calculate FULL portfolio volatility (before filtering)
            all_positions = portfolio_data  # pełny portfel
            full_tickers = [p['ticker'] for p in all_positions]
            full_w = np.array([float(p['weight_frac']) for p in all_positions], dtype=float)
            full_w = full_w / full_w.sum()
            
            print(f"[FORECAST-RISK] Full portfolio - tickers: {full_tickers}, weights: {full_w}")
            
            # Build full covariance matrix and calculate full portfolio volatility
            cov_full = self.build_covariance_matrix(db, full_tickers, vol_model)
            if cov_full.size == 0:
                return {"error": "Failed to build full covariance matrix"}
            
            _, _, sigma_full = risk_contribution(full_w, cov_full)
            print(f"[FORECAST-RISK] Full portfolio volatility: {sigma_full}")

            # Extract tickers and weights for ALL portfolio positions (no filtering)
            tickers = [item['ticker'] for item in portfolio_data]
            weights = np.array([float(item['weight_frac']) for item in portfolio_data], dtype=float)
            
            # Sanityzacja wag
            weights[~np.isfinite(weights)] = 0.0
            s = float(weights.sum())
            if s <= 0:
                return {"error": "Invalid weights (sum <= 0)"}
            weights = weights / s  # renormalizacja
            
            print(f"[FORECAST-RISK] Using tickers: {tickers}, weights: {weights}")
            
            # Build covariance matrix
            cov_matrix = self.build_covariance_matrix(db, tickers, vol_model)
            if cov_matrix.size == 0:
                return {"error": "Failed to build covariance matrix"}
            
            print(f"[FORECAST-RISK] Covariance matrix shape: {cov_matrix.shape}")
            print(f"[FORECAST-RISK] Weights shape: {weights.shape}")
            
            # Calculate risk contributions using quant.risk
            try:
                mrc, pct_rc, sigma_p = risk_contribution(weights, cov_matrix)
                risk_data = {"marginal_rc": mrc, "total_rc_pct": pct_rc, "portfolio_vol": sigma_p}
                print(f"[FORECAST-RISK] Risk contributions calculated - MRC: {mrc}, Total RC: {pct_rc}, Portfolio Vol: {sigma_p}")
            except ValueError as e:
                print(f"[FORECAST-RISK] Error in risk_contribution: {e}")
                return {"error": str(e)}
            
            # Prepare response data
            marginal_rc = risk_data["marginal_rc"]
            total_rc_pct = risk_data["total_rc_pct"]
            
            # Create data for charts
            chart_data = []
            for i, ticker in enumerate(tickers):
                chart_data.append({
                    "ticker": ticker,
                    "marginal_rc_pct": marginal_rc[i] * 100,  # Convert to percentage
                    "total_rc_pct": total_rc_pct[i],
                    "weight_pct": weights[i] * 100
                })
            
            # Sort by marginal risk contribution (descending)
            chart_data.sort(key=lambda x: x["marginal_rc_pct"], reverse=True)
            
                        # Add synthetic PORTFOLIO row at the top (using FULL portfolio volatility)
            if include_portfolio_bar:
                portfolio_row = {
                    "ticker": "PORTFOLIO",
                    # Show FULL portfolio volatility (annualized) as "marginal_rc_pct"
                    # to have one comparable number on the chart
                    "marginal_rc_pct": float(sigma_full * 100.0),  # ZAWSZE pełny portfel
                    "total_rc_pct": 100.0,   # Portfolio share = 100%
                    "weight_pct": 100.0      # Portfolio weight = 100%
                }
                print(f"[FORECAST-RISK] Adding PORTFOLIO row (full portfolio): {portfolio_row}")
                chart_data.insert(0, portfolio_row)
            
            result = {
                "tickers": [item["ticker"] for item in chart_data],
                "marginal_rc_pct": [float(item["marginal_rc_pct"]) for item in chart_data],
                "total_rc_pct": [float(item["total_rc_pct"]) for item in chart_data],
                "weights_pct": [float(item["weight_pct"]) for item in chart_data],
                "portfolio_vol": float(risk_data["portfolio_vol"]),
                "vol_model": vol_model,
                # Convenient addition if frontend prefers percentages
                "portfolio_vol_pct": float(risk_data["portfolio_vol"] * 100.0)
            }
            
            print(f"[FORECAST-RISK] Final result - tickers: {result['tickers']}")
            print(f"[FORECAST-RISK] Final result - marginal_rc_pct: {result['marginal_rc_pct']}")
            return result
            
        except Exception as e:
            print(f"Error calculating forecast risk contribution: {e}")
            return {"error": str(e)} 

    def get_forecast_metrics(self, db: Session, username: str = "admin", 
                           conf_level: float = 0.95) -> Dict[str, Any]:
        """Get forecast metrics for all portfolio tickers"""
        print(f"[FORECAST-METRICS] Starting forecast metrics for user: {username}, conf_level: {conf_level}")
        try:
            # Get portfolio tickers
            print(f"[FORECAST-METRICS] Getting portfolio tickers...")
            tickers = self.get_user_portfolio_tickers(db, username)
            if not tickers:
                print(f"[FORECAST-METRICS] No portfolio tickers found")
                return {"error": "No portfolio tickers found"}
            print(f"[FORECAST-METRICS] Portfolio tickers: {tickers}")
            
            # Get shares map
            user_id = db.query(User.id).filter(User.username == username).scalar()
            if not user_id:
                return {"error": "User not found"}
            
            shares_map = {
                p.ticker_symbol: p.shares
                for p in db.query(Portfolio).filter(Portfolio.user_id == user_id).all()
            }
            
            metrics_data = []
            
            for ticker in tickers:
                # Get historical data
                print(f"[FORECAST-METRICS] Processing {ticker}...")
                dates, closes = self._get_close_series(db, ticker)
                if len(closes) < 250:  # min rok historii (250 dni)
                    print(f"[FORECAST-METRICS] {ticker}: Insufficient data ({len(closes)} < 250)")
                    continue
                
                # Calculate returns
                returns = np.diff(np.log(closes))
                if len(returns) < 250:
                    continue
                
                # Calculate forecast volatilities
                print(f"[FORECAST-METRICS] {ticker}: Calculating volatilities...")
                ewma5 = forecast_sigma(returns, "EWMA (5D)") * 100
                ewma20 = forecast_sigma(returns, "EWMA (20D)") * 100
                garch_vol = forecast_sigma(returns, "GARCH") * 100
                egarch_vol = forecast_sigma(returns, "EGARCH") * 100
                print(f"[FORECAST-METRICS] {ticker}: EWMA5={ewma5:.2f}%, EWMA20={ewma20:.2f}%, GARCH={garch_vol:.2f}%, EGARCH={egarch_vol:.2f}%")
                
                # Calculate basic stats for VaR/CVaR
                stats = basic_stats(returns)
                sigma_d = stats["std_daily"]
                mu_d = stats["mean_daily"]
                
                # Calculate VaR/CVaR
                var_pct, cvar_pct = var_cvar(sigma_d, mu_d, conf_level)
                
                # Calculate market value and dollar amounts
                last_price = closes[-1]
                shares = shares_map.get(ticker, 0)
                mv = shares * last_price
                var_usd = var_pct / 100 * mv
                cvar_usd = cvar_pct / 100 * mv
                
                metrics_data.append({
                    "ticker": ticker,
                    "ewma5_pct": round(ewma5, 2),
                    "ewma20_pct": round(ewma20, 2),
                    "garch_vol_pct": round(garch_vol, 2),
                    "egarch_vol_pct": round(egarch_vol, 2),
                    "var_pct": round(var_pct, 2),
                    "cvar_pct": round(cvar_pct, 2),
                    "var_usd": round(var_usd, 0),
                    "cvar_usd": round(cvar_usd, 0)
                })
            
            # Sort by ticker name
            metrics_data.sort(key=lambda x: x["ticker"])
            
            return {
                "metrics": metrics_data,
                "conf_level": conf_level
            }
            
        except Exception as e:
            print(f"Error calculating forecast metrics: {e}")
            return {"error": str(e)}

    def get_rolling_forecast(self, db: Session, tickers: List[str], model: str, 
                           window: int, username: str = "admin") -> List[Dict[str, Any]]:
        """
        Return list of dicts: {date, ticker, vol_pct}
        – gotowe do wykresu liniowego.
        """
        print(f"[ROLLING-FORECAST] Starting rolling forecast for user: {username}")
        print(f"[ROLLING-FORECAST] Tickers: {tickers}, model: {model}, window: {window}")
        try:
            if not tickers:
                return []
            
            # --- 1. Przygotuj zwroty ---
            lookback = 3*365      # 3 lata – wystarczy dla 252-rolling
            ret_map = self._get_return_series_map(db, tickers, lookback_days=lookback)

            # 2) find common dates for all tickers
            common_dates = None
            for tkr in tickers:
                if tkr == "PORTFOLIO":
                    continue
                dates, rets = ret_map.get(tkr, ([], np.array([])))
                if len(rets) >= window:
                    if common_dates is None:
                        common_dates = set(dates)
                    else:
                        common_dates = common_dates.intersection(set(dates))
            
            # jeśli tylko PORTFOLIO → seedujemy common_dates datami portfela
            if common_dates is None and "PORTFOLIO" in tickers:
                conc = self.get_concentration_risk_data(db, username)
                if "error" not in conc and conc["portfolio_data"]:
                    w_map = {p["ticker"]: p["weight_frac"] for p in conc["portfolio_data"]}
                    active = list(w_map.keys())
                    # doładuj brakujące serie
                    ret_map.update(self._get_return_series_map(db, list(set(active + ["SPY"])), lookback_days=lookback))
                    dates_ref, R, active_aligned = self._align_on_reference(ret_map, active, ref_symbol="SPY", min_obs=window)
                    dates_p, rp = self._portfolio_series_with_coverage(dates_ref, R, w_map, active_aligned, min_weight_cov=0.60)
                    common_dates = set(dates_p)  # ← seed
                    print(f"[ROLLING-FORECAST] Using portfolio dates as common_dates: {len(common_dates)} dates")
            
            if common_dates is None:
                return {"data": [], "model": model, "window": window}
            
            common_dates = sorted(list(common_dates))
            
            # 3) lines for individual tickers (common dates only)
            out = []
            for tkr in tickers:
                if tkr == "PORTFOLIO":
                    continue
                dates, rets = ret_map.get(tkr, ([], np.array([])))
                if len(rets) < window:          # not enough data
                    continue
                
                # Create date index for fast lookup
                date_idx = {d: i for i, d in enumerate(dates)}
                
                for date in common_dates:
                    if date in date_idx:
                        i = date_idx[date]
                        if i >= window:  # Ensure we have enough data for rolling window
                            σ = forecast_sigma(rets[i-window:i], model) * 100
                            out.append({
                                "date": date.isoformat() if hasattr(date, 'isoformat') else str(date),
                                "ticker": tkr,
                                "vol_pct": round(float(σ), 4)
                            })

            # 4) "PORTFOLIO" line (optional) - using _portfolio_series_with_coverage
            if "PORTFOLIO" in tickers:
                conc = self.get_concentration_risk_data(db, username)
                if "error" not in conc and conc["portfolio_data"]:
                    w_map = {p["ticker"]: p["weight_frac"] for p in conc["portfolio_data"]}
                    active = list(w_map.keys())
                    # fill ret_map if any active ticker missing
                    if any(a not in ret_map for a in active):
                        ret_map.update(self._get_return_series_map(db, list(set(active + ["SPY"])), lookback_days=lookback))

                    dates_ref, R, active_aligned = self._align_on_reference(ret_map, active, ref_symbol="SPY", min_obs=window)
                    if len(dates_ref) >= window:
                        # Use _portfolio_series_with_coverage for NaN-safe portfolio returns
                        dates_p, rp = self._portfolio_series_with_coverage(dates_ref, R, w_map, active_aligned, min_weight_cov=0.60)
                        
                        # Create date index for portfolio
                        portfolio_date_idx = {d: i for i, d in enumerate(dates_p)}
                        
                        for date in common_dates:
                            if date in portfolio_date_idx:
                                j = portfolio_date_idx[date]
                                if j >= window:  # Ensure we have enough data for rolling window
                                    σ = forecast_sigma(rp[j-window:j], model) * 100
                                    out.append({
                                        "date": date.isoformat() if hasattr(date, 'isoformat') else str(date),
                                        "ticker": "PORTFOLIO",
                                        "vol_pct": round(float(σ), 4)
                                    })

            # sort (frontend does not need to transform)
            out.sort(key=lambda d: (d["date"], d["ticker"]))
            
            # Get common date range for all tickers
            common_date_range = self._get_common_date_range(db, tickers)
            
            return {
                "data": out,
                "model": model,
                "window": window,
                "common_date_range": common_date_range
            }
            
        except Exception as e:
            print(f"Error calculating rolling forecast: {e}")
            return []

    def get_latest_factor_exposures(self, db: Session, username: str = "admin") -> Dict[str, Any]:
        """
        Return β matrix (ticker × factor) and dates, selecting latest entry for each (ticker,factor).
        """
        try:
            data = self.get_factor_exposure_data(db, username)
            exposures = data["factor_exposures"]      # ~100 k wierszy

            # 1) pack only necessary fields to save RAM
            latest_map: Dict[tuple, tuple] = {}
            for row in exposures:
                key = (row["ticker"], row["factor"])
                # replace if newer date found
                if key not in latest_map or row["date"] > latest_map[key][0]:
                    latest_map[key] = (row["date"], row["beta"])

            # --- pivot na potrzeby tabeli ---
            factors = data["available_factors"]
            tickers = data["available_tickers"] + ["PORTFOLIO"]

            # 2) portfolio betas - weighted sum of all user's stocks
            port_betas = {f: 0.0 for f in factors}
            try:
                # fetch user portfolio with weights
                conc = self.get_concentration_risk_data(db, username)
                if "error" not in conc and conc["portfolio_data"]:
                    w_map = {p["ticker"]: p["weight_frac"] for p in conc["portfolio_data"]}
                    
                    # weighted sum per factor (no normalization)
                    for factor in factors:
                        for ticker, weight in w_map.items():
                            if (ticker, factor) in latest_map:
                                beta = latest_map[(ticker, factor)][1]  # tuple[date, beta]
                                port_betas[factor] += weight * beta
            except Exception as e:
                print(f"Error calculating portfolio betas: {e}")
                pass

            # 3) arrange final list
            table = []
            for t in tickers:
                row = {"ticker": t}
                for f in factors:
                    if t == "PORTFOLIO":
                        row[f] = round(port_betas[f], 2)
                    else:
                        beta = latest_map.get((t, f), (None, 0.0))[1]  # tuple[date, beta]
                        row[f] = round(beta, 2)
                table.append(row)

            return {
                "as_of": max(d for d, _ in latest_map.values()) if latest_map else "",
                "factors": factors,
                "data": table
            }
            
        except Exception as e:
            print(f"Error getting latest factor exposures: {e}")
            return {"error": str(e)}

    def get_portfolio_summary(self, db: Session, username: str = "admin") -> Dict[str, Any]:
        """
        Zwraca agregowane dane dla Portfolio Summary dashboard.
        Combine outputs of risk_scoring, concentration_risk, forecast_metrics, forecast_risk_contribution.
        """
        print(f"[PORTFOLIO-SUMMARY] Starting portfolio summary for user: {username}")
        try:
            # 1) Risk Scoring
            print(f"[PORTFOLIO-SUMMARY] Getting risk scoring data...")
            risk_data = self.get_risk_scoring(db, username)
            if "error" in risk_data:
                print(f"[PORTFOLIO-SUMMARY] Warning: Risk scoring failed: {risk_data['error']}")
                risk_data = {
                    "component_scores": {"overall": 0.5},
                    "risk_contribution_pct": {"market": 25.0, "concentration": 25.0, "volatility": 25.0, "liquidity": 25.0}
                }
            
            # 2) Concentration Risk
            print(f"[PORTFOLIO-SUMMARY] Getting concentration risk data...")
            conc_data = self.get_concentration_risk_data(db, username)
            if "error" in conc_data:
                print(f"[PORTFOLIO-SUMMARY] Warning: Concentration risk failed: {conc_data['error']}")
                conc_data = {
                    "total_market_value": 0,
                    "portfolio_data": [],
                    "concentration_metrics": {"largest_position": 0, "top_3_concentration": 0}
                }
            
            # 3) Forecast Risk Contribution (EGARCH)
            print(f"[PORTFOLIO-SUMMARY] Getting forecast risk contribution (EGARCH)...")
            forecast_contribution = self.get_forecast_risk_contribution(db, username, vol_model="EGARCH")
            if "error" in forecast_contribution:
                print(f"[PORTFOLIO-SUMMARY] Warning: Forecast risk contribution failed: {forecast_contribution['error']}")
                forecast_contribution = {
                    "portfolio_vol": 0.15,
                    "tickers": ["N/A"],
                    "marginal_rc_pct": [0.0]
                }
            
            # 4) Forecast Metrics (dla CVaR)
            print(f"[PORTFOLIO-SUMMARY] Getting forecast metrics...")
            forecast_metrics = self.get_forecast_metrics(db, username)
            if "error" in forecast_metrics:
                print(f"[PORTFOLIO-SUMMARY] Warning: Forecast metrics failed: {forecast_metrics['error']}")
                forecast_metrics = {"metrics": []}
            
            # 5) Agregacja CVaR
            total_cvar_usd = sum(item.get("cvar_usd", 0) for item in forecast_metrics.get("metrics", []))
            total_market_value = conc_data.get("total_market_value", 1)
            total_cvar_pct = (total_cvar_usd / total_market_value * 100) if total_market_value > 0 else 0
            
            # 6) Risk Level mapping with validation
            overall_score = risk_data.get("component_scores", {}).get("overall", 0) * 100
            
            # Sanity check: ensure overall score is in valid range
            if not (0.0 <= overall_score <= 100.0):
                print(f"Warning: Overall score out of range: {overall_score}, clipping to [0,100]")
                overall_score = max(0, min(overall_score, 100))
            
            if overall_score <= 33:
                risk_level = "LOW"
            elif overall_score <= 66:
                risk_level = "MEDIUM"
            else:
                risk_level = "HIGH"
            
            # 7) Highest Risk Component
            risk_contribution = risk_data.get("risk_contribution_pct", {})
            highest_risk = max(risk_contribution.items(), key=lambda x: x[1]) if risk_contribution else ("", 0)
            high_risk_components = sum(1 for v in risk_contribution.values() if v > 25)
            
            # 8) Portfolio Positions dla wykresu
            portfolio_positions = conc_data.get("portfolio_data", [])
            
            # Validation and flags
            flags = {}
            volatility_egarch = forecast_contribution.get("portfolio_vol", 0)
            
            # Check for suspicious values
            if volatility_egarch > 3.0:  # > 300% annualized
                flags["high_vol"] = True
                print(f"Warning: EGARCH volatility {volatility_egarch*100:.1f}% > 300%")
            
            if overall_score > 1.0:
                flags["high_risk_score"] = True
                print(f"Warning: Risk score {overall_score:.1f}% > 100%")
            
            if total_cvar_pct < -10.0:  # < -10%
                flags["high_cvar"] = True
                print(f"Warning: CVaR {total_cvar_pct:.1f}% < -10%")
            
            return {
                "risk_score": {
                    "overall_score": round(overall_score, 1),
                    "risk_level": risk_level,
                    "highest_risk_component": highest_risk[0],
                    "highest_risk_percentage": round(highest_risk[1], 1),
                    "high_risk_components_count": high_risk_components
                },
                "portfolio_overview": {
                    "total_market_value": conc_data.get("total_market_value", 0),
                    "total_positions": len(portfolio_positions),
                    "largest_position": round(conc_data.get("concentration_metrics", {}).get("largest_position", 0), 1),
                    "top_3_concentration": round(conc_data.get("concentration_metrics", {}).get("top_3_concentration", 0), 1),
                    "volatility_egarch": round(forecast_contribution.get("portfolio_vol_pct", volatility_egarch * 100), 1),
                    "cvar_percentage": round(total_cvar_pct, 1),
                    "cvar_usd": round(total_cvar_usd, 0),
                    "top_risk_contributor": {
                        "ticker": self._get_top_risk_contributor(forecast_contribution)[0],
                        "vol_contribution_pct": self._get_top_risk_contributor(forecast_contribution)[1]
                    }
                },
                "portfolio_positions": portfolio_positions,
                "flags": flags
            }
            
        except Exception as e:
            print(f"Error getting portfolio summary: {e}")
            return {"error": str(e)}

    def _get_top_risk_contributor(self, forecast_contribution: Dict[str, Any]) -> tuple:
        """Get top risk contributor based on total_rc_pct, excluding PORTFOLIO row"""
        import numpy as np
        
        tickers = forecast_contribution.get("tickers", [])
        trc = forecast_contribution.get("total_rc_pct", [])
        
        # Skip PORTFOLIO row if it's first
        start = 1 if tickers and tickers[0] == "PORTFOLIO" else 0
        
        if trc and len(trc) > start:
            # Find max total risk contribution among real tickers
            idx_rel = int(np.argmax(trc[start:]))
            idx = start + idx_rel
            top_ticker = tickers[idx]
            top_pct = float(trc[idx])  # This is the risk contribution percentage
        else:
            top_ticker, top_pct = "N/A", 0.0
        
        return top_ticker, round(top_pct, 1)

    def get_realized_metrics(self, db: Session, username: str = "admin") -> Dict[str, Any]:
        """Get realized risk metrics for portfolio and individual tickers (NaN-tolerant, aligned to SPY)."""
        print(f"[REALIZED-METRICS] Starting realized metrics for user: {username}")
        try:
            import pandas as pd
            import numpy as np
            from quant.realized import compute_realized_metrics
            
            cache_key = self._get_cache_key("realized_metrics", username)
            cached = self._get_from_cache(cache_key)
            if cached:
                return cached
        
            # 1) snapshot portfela
            print(f"[REALIZED-METRICS] Getting portfolio snapshot...")
            portfolio_positions, ok = self._portfolio_snapshot(db, username)
            if not ok or not portfolio_positions:
                print(f"[REALIZED-METRICS] No portfolio positions found")
                return {"metrics": []}
            
            portfolio_tickers = [p["ticker"] for p in portfolio_positions]
            weights_map = {p["ticker"]: p["weight_frac"] for p in portfolio_positions}
            print(f"[REALIZED-METRICS] Portfolio tickers: {portfolio_tickers}")

            # 2) Zwroty – dłuższe okno i kalendarz SPY
            needed = portfolio_tickers + ["SPY"]
            print(f"[REALIZED-METRICS] Getting return series for: {needed}")
            ret_map = self._get_return_series_map(db, needed, lookback_days=252*2)  # 2 lata
            dates_ref, M, active = self._align_on_reference(ret_map, needed, ref_symbol="SPY", min_obs=30)
            print(f"[REALIZED-METRICS] Aligned data shape: {M.shape}, active symbols: {active}")
            if M.size == 0 or len(dates_ref) < 30 or "SPY" not in ret_map or len(ret_map["SPY"][0]) == 0:
                # brak sensownego pokrycia → demo
                print(f"[REALIZED-METRICS] Insufficient data, using sample metrics")
                return self._get_sample_realized_metrics(portfolio_tickers)
        
            # SPY w kalendarzu ref
            spy_dates, spy_ret = ret_map["SPY"]
            idx_spy = {d: i for i, d in enumerate(spy_dates)}
            spy_aligned = np.array([spy_ret[idx_spy[d]] if d in idx_spy else np.nan for d in dates_ref], dtype=float)

            metrics_frames = []

            # 3) Metryki dla każdego tickera vs SPY (bez twardego przecięcia całego koszyka)

            # mapowanie kolumn matrixu M do symboli (bez SPY)
            sym_cols = [s for s in active if s != "SPY"]
            if not sym_cols:
                return self._get_sample_realized_metrics(portfolio_tickers)

            for j, sym in enumerate(sym_cols):
                x = M[:, j]  # zwroty tickera w kalendarzu SPY (z NaN)
                m = np.isfinite(x) & np.isfinite(spy_aligned)
                if m.sum() < 30:
                    continue
                d_use = [dates_ref[k] for k in range(len(dates_ref)) if m[k]]
                df = pd.DataFrame({sym: x[m], "SPY": spy_aligned[m]}, index=d_use)

                # compute_realized_metrics oczekuje pełnego DataFrame z benchmarkiem
                try:
                    res = compute_realized_metrics(df, benchmark_ndx="SPY", R=df.values, active=[sym, "SPY"])
                    if not res.empty and sym in res.index:
                        metrics_frames.append(res.loc[[sym]])
                except Exception as e:
                    print(f"[realized] {sym} failed: {e}")
                    continue

            # 4) Metryki PORTFOLIO vs SPY – renormalizacja wag po dostępnych papierach w danym dniu
            dates_p, rp = self._portfolio_series_with_coverage(dates_ref, M, weights_map, sym_cols, min_weight_cov=0.60)
            if len(rp) >= 30:
                # dopasuj SPY do tych dni
                i_spy = {d: i for i, d in enumerate(dates_ref)}
                spy_p = []
                d_common = []
                for d in dates_p:
                    if d in i_spy and np.isfinite(spy_aligned[i_spy[d]]):
                        spy_p.append(spy_aligned[i_spy[d]])
                        d_common.append(d)
                spy_p = np.array(spy_p, dtype=float)
                rp = np.array([rp[dates_p.index(d)] for d in d_common], dtype=float)

                if len(rp) >= 30 and len(spy_p) >= 30:
                    dfp = pd.DataFrame({"PORTFOLIO": rp, "SPY": spy_p}, index=d_common)
                    try:
                        res_p = compute_realized_metrics(dfp, benchmark_ndx="SPY",
                                                         R=dfp.values, active=["PORTFOLIO", "SPY"])
                        if not res_p.empty and "PORTFOLIO" in res_p.index:
                            metrics_frames.append(res_p.loc[["PORTFOLIO"]])
                    except Exception as e:
                        print(f"[realized] PORTFOLIO failed: {e}")
                        pass

            # 5) Fallback jeżeli nic nie wyszło
            if not metrics_frames:
                return self._get_sample_realized_metrics(portfolio_tickers)
        
            # 6) Spakuj wyniki w listę dictów dla API
            out = []
            for df in metrics_frames:
                for sym in df.index:
                    row = df.loc[sym]
                    def safe(x, default=0.0):
                        try:
                            return float(x) if pd.notna(x) and np.isfinite(x) else default
                        except Exception:
                            return default
                    out.append({
                        "ticker": sym,
                        "ann_return_pct": safe(row.get("Ann.Return%", 0.0)),
                        "volatility_pct": safe(row.get("Ann.Volatility%", 0.0)),
                        "sharpe_ratio": safe(row.get("Sharpe", 0.0)),
                        "sortino_ratio": safe(row.get("Sortino", 0.0)),
                        "skewness": safe(row.get("Skew", 0.0)),
                        "kurtosis": safe(row.get("Kurtosis", 0.0)),
                        "max_drawdown_pct": safe(row.get("Max Drawdown%", 0.0)),
                        "var_95_pct": safe(row.get("VaR(5%)%", 0.0)),
                        "cvar_95_pct": safe(row.get("CVaR(95%)%", 0.0)),
                        "hit_ratio_pct": safe(row.get("Hit Ratio%", 0.0)),
                        "beta_ndx": safe(row.get("Beta (SPY)", 0.0)),
                        "up_capture_ndx_pct": safe(row.get("Up Capture (SPY)%", 0.0)),
                        "down_capture_ndx_pct": safe(row.get("Down Capture (SPY)%", 0.0)),
                        "tracking_error_pct": safe(row.get("Tracking Error%", 0.0)),
                        "information_ratio": safe(row.get("Information Ratio", 0.0)),
                    })

            result = {"metrics": out}
            self._set_cache(cache_key, result)
            return result
            
        except Exception as e:
            print(f"[realized] Global error: {e}")
            return self._get_sample_realized_metrics(portfolio_tickers if 'portfolio_tickers' in locals() else [])

    def get_rolling_metric(self, db: Session, metric: str = "vol", window: int = 21,
                          tickers: List[str] = None, username: str = "admin") -> Dict[str, Any]:
        """Get rolling metric data for charting"""
        print(f"[ROLLING-METRIC] Starting rolling metric calculation for user: {username}")
        print(f"[ROLLING-METRIC] Metric: {metric}, window: {window}, tickers: {tickers}")
        import numpy as np
        import pandas as pd
        from math import isfinite
        
        try:
            # Use provided tickers or default to PORTFOLIO
            if tickers is None:
                tickers = ["PORTFOLIO"]
            
            # Check cache first
            cache_key = self._get_cache_key("rolling_metric", username, metric=metric, window=window, tickers=tickers)
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                print(f"Using cached rolling metric for user: {username}")
                return cached_data
            
            print(f"Getting rolling metric for user: {username}, tickers: {tickers}")
            
            # Get all tickers including benchmarks
            portfolio_tickers = self.get_user_portfolio_tickers(db, username)
            static_tickers = self.get_static_tickers()
            all_tickers = portfolio_tickers + static_tickers + ["SPY"]  # Removed NDX, kept SPY
            
            # Get return series map
            ret_map = self._get_return_series_map(db, all_tickers, lookback_days=252*5)
            print(f"Ret map keys: {list(ret_map.keys())}")
            
            # Use new alignment method instead of old intersection
            dates, R, active = self._align_on_reference(ret_map, all_tickers, ref_symbol="SPY", min_obs=40)
            print(f"Align result - dates: {len(dates)}, R shape: {R.shape}, active: {active}")
            
            if R.size == 0 or len(dates) < 40:
                return {"error": "Insufficient overlapping history (vs SPY)"}
            
            # Create portfolio returns if needed
            ret_df = pd.DataFrame(R, index=dates, columns=active)
            print(f"ret_df shape: {ret_df.shape}")
            print(f"ret_df columns: {list(ret_df.columns)}")
            print(f"ret_df index type: {type(ret_df.index)}")

            # Add SPY column if needed for beta calculation
            if metric == "beta" and "SPY" not in ret_df.columns and "SPY" in ret_map:
                spy_dates, spy_returns = ret_map["SPY"]
                spy_series = pd.Series(index=dates, dtype=float)
                spy_idx = {d: i for i, d in enumerate(spy_dates)}
                for i, date in enumerate(dates):
                    if date in spy_idx:
                        spy_series.iloc[i] = spy_returns[spy_idx[date]]
                ret_df["SPY"] = spy_series.values
                print(f"Added SPY column to ret_df, columns: {list(ret_df.columns)}")

            if "PORTFOLIO" in tickers:
                # wagi portfela
                portfolio_weights = {
                    it["ticker"]: it["weight_frac"]
                    for it in self.get_concentration_risk_data(db, username).get("portfolio_data", [])
                }
                print(f"Portfolio weights: {portfolio_weights}")
                print(f"Active symbols: {active}")
                
                # sprawdź czy są wspólne symbole
                common_symbols = set(portfolio_weights.keys()) & set(active)
                print(f"Common symbols: {common_symbols}")

                # policz serię portfola z dzienną renormalizacją wag i progiem pokrycia
                try:
                    dates_p, rp = self._portfolio_series_with_coverage(
                        dates, R, portfolio_weights, active, min_weight_cov=0.60
                    )
                    print(f"Portfolio series - dates: {len(dates_p)}, returns: {len(rp)}")

                    # wstaw do pełnego kalendarza (NaN tam, gdzie pokrycie < 60%)
                    port = pd.Series(index=dates, dtype=float)
                    port.loc[dates_p] = rp
                    ret_df["PORTFOLIO"] = port.values
                except Exception as e:
                    print(f"Error in portfolio series calculation: {e}")
                    # fallback - użyj prostego podejścia
                    portfolio_returns = np.zeros(len(R))
                    for i, ticker_name in enumerate(active):
                        if ticker_name in portfolio_weights:
                            portfolio_returns += R[:, i] * portfolio_weights[ticker_name]
                    ret_df["PORTFOLIO"] = portfolio_returns
                    
                # sanityzacja inf -> nan
                ret_df = ret_df.replace([np.inf, -np.inf], np.nan)
            
            # Compute rolling metrics for all requested tickers
            from quant.rolling import rolling_metric
            
            datasets = []
            
            for ticker in tickers:
                try:
                    if ticker in ret_df.columns:
                        ser = rolling_metric(ret_df, metric, window, ticker)
                        # gwarancja Series + wyrzucenie inf do NaN
                        if not isinstance(ser, pd.Series):
                            ser = pd.Series(ser, index=ret_df.index)
                        ser = ser.replace([np.inf, -np.inf], np.nan)

                        dates = [str(d) for d in ser.index]
                        values = [None if pd.isna(v) or not isfinite(float(v)) else float(v) for v in ser.values]

                        datasets.append({
                            "ticker": ticker,
                            "dates": dates,
                            "values": values
                        })
                except Exception as e:
                    print(f"Error computing rolling metric for {ticker}: {e}")
                    continue
            
            # Get common date range for all tickers
            common_date_range = self._get_common_date_range(db, all_tickers)
            
            # Convert to JSON format
            result = {
                "datasets": datasets,
                "metric": metric,
                "window": window,
                "common_date_range": common_date_range
            }
            
            # Cache the result
            self._set_cache(cache_key, result)
            
            return result
            
        except Exception as e:
            print(f"Error getting rolling metric: {e}")
            return {"error": str(e)}

    # --- liquidity wrappers ------------------------------------------------
    def get_liquidity_metrics(self, db: Session, username: str = "admin") -> Dict[str, Any]:
        """Get comprehensive liquidity metrics for portfolio"""
        print(f"[LIQUIDITY-METRICS] Starting liquidity metrics for user: {username}")
        try:
            from quant.liquidity import liquidity_metrics
            return liquidity_metrics(db, username)
        except Exception as e:
            print(f"Error getting liquidity metrics: {e}")
            return {"error": str(e)}

    def get_volume_distribution(self, db: Session, username: str = "admin") -> Dict[str, Any]:
        """Get volume analysis data"""
        try:
            out = self.get_liquidity_metrics(db, username)
            if "error" in out:
                return out
            return out.get("volume_analysis", {})
        except Exception as e:
            print(f"Error getting volume distribution: {e}")
            return {"error": str(e)}

    def get_liquidity_alerts(self, db: Session, username: str = "admin") -> List[Dict[str, Any]]:
        """Get liquidity alerts for portfolio"""
        from quant.liquidity import liquidity_metrics
        result = liquidity_metrics(db, username)
        return result.get("alerts", [])
    
    def _get_sample_realized_metrics(self, portfolio_tickers: List[str]) -> Dict[str, Any]:
        """Fallback to sample data when insufficient historical data"""
        print(f"Debug: Using sample realized metrics for {portfolio_tickers}")
        
        metrics_list = []
        
        # Add PORTFOLIO metrics
        portfolio_metrics = {
            "ticker": "PORTFOLIO",
            "ann_return_pct": 38.89,
            "volatility_pct": 29.67,
            "sharpe_ratio": 0.94,
            "sortino_ratio": 1.55,
            "skewness": 4.38,
            "kurtosis": 52.47,
            "max_drawdown_pct": -35.08,
            "var_95_pct": -2.41,
            "cvar_95_pct": -3.44,
            "hit_ratio_pct": 47.75,
            "beta_ndx": 1.02,
            "up_capture_ndx_pct": 113.10,
            "down_capture_ndx_pct": 92.35,
            "tracking_error_pct": 1.39,
            "information_ratio": 0.98
        }
        metrics_list.append(portfolio_metrics)
        
        # Add metrics for each individual ticker
        for ticker in portfolio_tickers:
            # Generate realistic metrics for each ticker
            import random
            random.seed(hash(ticker) % 1000)  # Deterministic but varied
            
            ticker_metrics = {
                "ticker": ticker,
                "ann_return_pct": round(random.uniform(15, 60), 2),
                "volatility_pct": round(random.uniform(20, 50), 2),
                "sharpe_ratio": round(random.uniform(0.5, 2.0), 2),
                "sortino_ratio": round(random.uniform(0.8, 2.5), 2),
                "skewness": round(random.uniform(-2, 5), 2),
                "kurtosis": round(random.uniform(10, 60), 2),
                "max_drawdown_pct": round(random.uniform(-50, -15), 2),
                "var_95_pct": round(random.uniform(-4, -1), 2),
                "cvar_95_pct": round(random.uniform(-6, -2), 2),
                "hit_ratio_pct": round(random.uniform(40, 60), 2),
                "beta_ndx": round(random.uniform(0.5, 2.0), 2),
                "up_capture_ndx_pct": round(random.uniform(80, 130), 2),
                "down_capture_ndx_pct": round(random.uniform(70, 110), 2),
                "tracking_error_pct": round(random.uniform(1, 5), 2),
                "information_ratio": round(random.uniform(0.3, 1.5), 2)
            }
            metrics_list.append(ticker_metrics)
        
        return {
            "metrics": metrics_list,
            "common_date_range": {
                "start_date": "2024-01-01",
                "end_date": "2024-12-31",
                "total_days": 252
            }
        }

    def search_tickers(self, query: str) -> List[Dict[str, str]]:
        """Search for tickers using yfinance"""
        try:
            import yfinance as yf
            
            # Common ticker patterns to try
            patterns = [
                query.upper(),
                f"{query.upper()}.TO",  # Toronto
                f"{query.upper()}.L",   # London
                f"{query.upper()}.PA",  # Paris
                f"{query.upper()}.DE",  # Frankfurt
                f"{query.upper()}.SW",  # Swiss
                f"{query.upper()}.AS",  # Amsterdam
            ]
            
            suggestions = []
            seen_tickers = set()
            
            for pattern in patterns:
                try:
                    ticker = yf.Ticker(pattern)
                    info = ticker.info
                    
                    if info and 'symbol' in info and info['symbol'] not in seen_tickers:
                        seen_tickers.add(info['symbol'])
                        suggestions.append({
                            "symbol": info['symbol'],
                            "name": info.get('longName', info.get('shortName', 'Unknown')),
                            "exchange": info.get('exchange', 'Unknown'),
                            "type": info.get('quoteType', 'Unknown')
                        })
                        
                        # Limit to 10 suggestions
                        if len(suggestions) >= 10:
                            break
                            
                except Exception as e:
                    continue
            
            return suggestions
            
        except Exception as e:
            print(f"Error searching tickers: {e}")
            return []

    def check_ibkr_connection(self) -> bool:
        """Check if IBKR TWS is running and accessible"""
        try:
            # Create a temporary test script to check IBKR connection
            test_script = """
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from services.ibkr_service import IBKRService
    ibkr = IBKRService()
    connected = ibkr.connect(timeout=10)
    print(f"Connected: {connected}")
    if connected:
        ibkr.disconnect()
    sys.exit(0 if connected else 1)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
"""

            # Write the test script to a temporary file
            test_file = "test_ibkr_connection.py"
            with open(test_file, 'w') as f:
                f.write(test_script)

            try:
                # Run the test script
                import subprocess
                result = subprocess.run(
                    ["poetry", "run", "python", test_file],
                    shell=True, capture_output=True, text=True, timeout=15
                )

                # Clean up the test file
                if os.path.exists(test_file):
                    os.remove(test_file)

                if result.returncode == 0 and "Connected: True" in result.stdout:
                    return True
                else:
                    return False

            except subprocess.TimeoutExpired:
                return False
            finally:
                # Ensure test file is cleaned up
                if os.path.exists(test_file):
                    os.remove(test_file)

        except Exception as e:
            print(f"Error checking IBKR connection: {e}")
            return False

    def add_ticker_to_portfolio(self, db: Session, username: str, ticker: str, shares: int) -> Dict[str, Any]:
        """Add ticker to user's portfolio with intelligent data fetching"""
        try:
            # Normalize ticker
            ticker = ticker.upper().strip()
            
            # Check if ticker already exists in portfolio
            user = db.query(User).filter(User.username == username).first()
            if not user:
                return {"error": f"User {username} not found"}
            
            existing = db.query(Portfolio).filter(
                Portfolio.user_id == user.id,
                Portfolio.ticker_symbol == ticker
            ).first()
            
            if existing:
                return {"error": f"Ticker {ticker} already exists in portfolio"}
            
            # Check IBKR connection first
            ibkr_available = self.check_ibkr_connection()
            
            if ibkr_available:
                # Try to fetch from IBKR
                print(f"IBKR available, fetching data for {ticker}")
                success = self.fetch_and_store_historical_data(db, ticker)
                if success:
                    # Add to portfolio
                    portfolio_item = Portfolio(
                        user_id=user.id,
                        ticker_symbol=ticker,
                        shares=shares
                    )
                    db.add(portfolio_item)
                    db.commit()
                    
                    # Update JSON file
                    self._update_portfolio_json(username, db)
                    
                    # Clear cache for this user
                    self._clear_cache(f"*{username}*")
                    print(f"Cache cleared for user {username} after adding ticker {ticker}")
                    
                    return {
                        "success": True,
                        "message": f"Ticker {ticker} added successfully with {shares} shares (data from IBKR)",
                        "data_source": "IBKR",
                        "ticker": ticker,
                        "shares": shares
                    }
                else:
                    return {"error": f"Failed to fetch data for {ticker} from IBKR"}
            
            else:
                # IBKR not available, try fallback files
                print(f"IBKR not available, checking fallback files for {ticker}")
                
                # Check if fallback file exists
                data_dir = "data"
                if not os.path.exists(data_dir):
                    data_dir = "../data"
                
                json_file = os.path.join(data_dir, f"{ticker}.json")
                csv_file = os.path.join(data_dir, f"{ticker}.csv")
                
                if os.path.exists(json_file) or os.path.exists(csv_file):
                    # Import from fallback file
                    success = self.import_ticker_data_from_file(db, ticker)
                    if success:
                        # Add to portfolio
                        portfolio_item = Portfolio(
                            user_id=user.id,
                            ticker_symbol=ticker,
                            shares=shares
                        )
                        db.add(portfolio_item)
                        db.commit()
                        
                        # Update JSON file
                        self._update_portfolio_json(username, db)
                        
                        # Clear cache for this user
                        self._clear_cache(f"*{username}*")
                        print(f"Cache cleared for user {username} after adding ticker {ticker}")
                        
                        return {
                            "success": True,
                            "message": f"Ticker {ticker} added successfully with {shares} shares (data from fallback)",
                            "data_source": "fallback",
                            "ticker": ticker,
                            "shares": shares
                        }
                    else:
                        return {"error": f"Failed to import data for {ticker} from fallback file"}
                else:
                    return {
                        "error": f"Ticker {ticker} not available in fallback files and no IBKR connection"
                    }
                    
        except Exception as e:
            db.rollback()
            print(f"Error adding ticker to portfolio: {e}")
            return {"error": str(e)}

    def _update_portfolio_json(self, username: str, db: Session):
        """Update user's portfolio JSON file"""
        try:
            import json
            import os
            
            # Get user
            user = db.query(User).filter(User.username == username).first()
            if not user:
                return
            
            # Get all portfolio items
            all_items = db.query(Portfolio).filter(Portfolio.user_id == user.id).all()
            
            # Prepare data for JSON file
            json_data = []
            for item in all_items:
                json_data.append({
                    "ticker": item.ticker_symbol,
                    "shares": item.shares
                })
            
            # Write to JSON file
            json_file = f"../data/{username}_portfolio.json"
            if not os.path.exists(json_file):
                json_file = f"data/{username}_portfolio.json"
            
            with open(json_file, 'w') as f:
                json.dump(json_data, f, indent=2)
                
        except Exception as e:
            print(f"Error updating portfolio JSON: {e}")

    def remove_ticker_from_portfolio(self, db: Session, username: str, ticker: str) -> Dict[str, Any]:
        """Remove ticker from user's portfolio"""
        try:
            # Normalize ticker
            ticker = ticker.upper().strip()
            
            # Check if user exists
            user = db.query(User).filter(User.username == username).first()
            if not user:
                return {"error": f"User {username} not found"}
            
            # Check if ticker exists in portfolio
            portfolio_item = db.query(Portfolio).filter(
                Portfolio.user_id == user.id,
                Portfolio.ticker_symbol == ticker
            ).first()
            
            if not portfolio_item:
                return {"error": f"Ticker {ticker} not found in portfolio"}
            
            # Remove from database
            db.delete(portfolio_item)
            db.commit()
            
            # Update JSON file
            self._update_portfolio_json(username, db)
            
            # Clear cache for this user
            self._clear_cache(f"*{username}*")
            print(f"Cache cleared for user {username} after removing ticker {ticker}")
            
            return {
                "success": True,
                "message": f"Ticker {ticker} removed successfully from portfolio",
                "ticker": ticker
            }
                    
        except Exception as e:
            db.rollback()
            print(f"Error removing ticker from portfolio: {e}")
            return {"error": str(e)}