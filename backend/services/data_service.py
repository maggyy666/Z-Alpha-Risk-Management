import numpy as np
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from database.models.user import User
from database.models.portfolio import Portfolio
from database.models.ticker_data import TickerData
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
import threading
import time

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
    "scenario_min_weight_coverage": 0.70,  # min. 70% MV musi być objęte danymi
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
        # Stałe tickery które zawsze będą pobierane z IBKR
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
        """Clear cache entries matching pattern"""
        with self._cache_lock:
            if pattern:
                keys_to_remove = [k for k in self._cache.keys() if pattern in k]
            else:
                keys_to_remove = list(self._cache.keys())
            
            for key in keys_to_remove:
                if key in self._cache:
                    del self._cache[key]
                if key in self._cache_timestamps:
                    del self._cache_timestamps[key]
        
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
                print(f"❌ Not enough data for {symbol} ({len(historical_data)} records)")
                return {}
            
            print(f"📊 {symbol}: Found {len(historical_data)} historical records")
            
            # Sort by date ascending for calculations
            historical_data.sort(key=lambda x: x.date)
            
            # Extract prices and calculate returns
            prices = [row.close_price for row in historical_data]
            print(f"📊 {symbol}: Prices range: {min(prices):.2f} - {max(prices):.2f}")
            
            # Calculate log returns
            returns = np.diff(np.log(prices))
            print(f"📊 {symbol}: Returns shape: {returns.shape}, mean: {np.mean(returns):.6f}")
            
            if len(returns) < 30:
                print(f"❌ Not enough returns for {symbol}")
                return {}
            
            # Calculate metrics
            mean_daily = float(np.mean(returns))
            std_daily = float(np.std(returns, ddof=1))  # ddof=1 for estimation
            
            # Annualize
            mean_annual = mean_daily * 252
            std_annual = std_daily * np.sqrt(252)
            
            # Calculate forecast volatility using new math module
            print(f"🔍 Calculating {forecast_model} volatility for returns shape: {returns.shape}")
            forecast_vol = forecast_sigma(returns, forecast_model) * 100  # Convert to percentage
            print(f"📊 {symbol}: Calculated volatility: {forecast_vol:.2f}%")
            
            # Calculate Sharpe ratio
            sharpe_ratio = ((mean_daily * 252) - risk_free_annual) / (std_daily * np.sqrt(252)) if std_daily > 0 else 0.0
            
            # Get last price
            last_price = float(historical_data[-1].close_price)
            
            metrics = {
                'volatility_pct': forecast_vol,   # %
                'mean_return_annual': mean_annual,  # ułamek/rok
                'mean_return_pct': mean_annual * 100,  # %
                'sharpe_ratio': sharpe_ratio,
                'last_price': last_price
            }
            
            print(f"🔍 {symbol} metrics: {metrics}")
            return metrics
            
        except Exception as e:
            print(f"❌ Error calculating metrics for {symbol}: {e}")
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

            # Get all tickers: user portfolio + static tickers
            all_tickers = self.get_all_tickers(db, username)
            if not all_tickers:
                print(f"No tickers found for user {username}")
                result = []
                self._set_cache(cache_key, result)
                return result

            # Get portfolio items with shares info (only for user's portfolio)
            user = db.query(User).filter(User.username == username).first()
            portfolio_items = db.query(Portfolio).filter(Portfolio.user_id == user.id).all()
            shares_map = {item.ticker_symbol: item.shares for item in portfolio_items}

            # 1) Zbierz metryki dla wszystkich tickerów
            for symbol in all_tickers:
                print(f"Processing {symbol}...")
                m = self.calculate_volatility_metrics(db, symbol, forecast_model, risk_free_annual)
                print(f"{symbol} metrics: {m}")
                if m:
                    # Dla statycznych tickerów używamy domyślnej liczby shares
                    shares = shares_map.get(symbol, 1000) if symbol in shares_map else 1000
                    portfolio_data.append({
                        'symbol': symbol,
                        'forecast_volatility_pct': float(m.get('volatility_pct', 0.0)),
                        'last_price': float(m.get('last_price', 0.0)),
                        'sharpe_ratio': float(m.get('sharpe_ratio', 0.0)),
                        'shares': shares,
                        'is_static': symbol in self.STATIC_TICKERS
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
                print(f"📊 {symbol}: Already has {existing_count} records")
                return True

            # Generate sample data from 2016 to 2025
            base_price = 100.0
            current_price = base_price
            data_points = []
            
            # Generate dates from 2016 to 2025 (trading days only)
            start_date = datetime(2016, 1, 1)
            end_date = datetime(2025, 12, 31)
            
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
            print(f"❌ Error injecting sample data for {symbol}: {e}")
            db.rollback()
            return False 

    def _get_close_series(self, db: Session, symbol: str):
        """Zwraca (dates, closes) posortowane rosnąco, bez NaN/zer."""
        rows = (db.query(TickerData)
                  .filter(TickerData.ticker_symbol == symbol)
                  .order_by(TickerData.date)
                  .all())
        if not rows:
            return [], np.array([])
        dates = [r.date for r in rows]
        closes = np.array([float(r.close_price) for r in rows], dtype=float)
        mask = np.isfinite(closes) & (closes > 0)
        dates = [d for d, m in zip(dates, mask) if m]
        closes = closes[mask]
        return dates, closes

    def _log_returns_from_series(self, dates, closes):
        """Zwraca (ret_dates, log_returns) – dates skrócone o 1."""
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
                print("❌ No historical data found in database")
                return {"factor_exposures": [], "r2_data": [], "available_factors": available_factors, "available_tickers": all_tickers}
            
            print(f"📊 Found {len(dates)} dates from {min(dates)} to {max(dates)}")
            
            # Wczytaj serie ETF z bazy (real factor proxies)
            print("📊 Loading ETF data for factor proxies...")
            
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
            
            print(f"📊 ETF data loaded: SPY({len(spy_ret_dates)}), MTUM({len(mtum_ret_dates)}), IWM({len(iwm_ret_dates)}), VLUE({len(vlue_ret_dates)}), QUAL({len(qual_ret_dates)})")
            
            # Calculate factor exposures for each ticker and factor
            for ticker in all_tickers:
                print(f"🔍 Processing {ticker}...")
                
                # Get historical data for this ticker
                ticker_data = (db.query(TickerData)
                                 .filter(TickerData.ticker_symbol == ticker)
                                 .order_by(TickerData.date)
                                 .all())
                
                if len(ticker_data) < 30:
                    print(f"❌ Not enough data for {ticker} ({len(ticker_data)} records)")
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
                        if len(common) < 60:
                            print(f"❌ Not enough common dates for {ticker} vs SPY ({len(common)} records)")
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
                                print(f"❌ Error calculating MARKET beta for {ticker}: {e}")
                                continue
                    
                    elif factor == "MOMENTUM":
                        # Use real MTUM data (market-neutral)
                        common = [d for d in asset_ret_dates if d in mtum_ret_map and d in spy_ret_map]
                        if len(common) < 60:
                            print(f"❌ Not enough common dates for {ticker} vs MTUM ({len(common)} records)")
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
                                print(f"❌ Error calculating MOMENTUM beta for {ticker}: {e}")
                                continue
                    
                    elif factor == "SIZE":
                        # Use real IWM data (market-neutral)
                        common = [d for d in asset_ret_dates if d in iwm_ret_map and d in spy_ret_map]
                        if len(common) < 60:
                            print(f"❌ Not enough common dates for {ticker} vs IWM ({len(common)} records)")
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
                                print(f"❌ Error calculating SIZE beta for {ticker}: {e}")
                                continue
                    
                    elif factor == "VALUE":
                        # Use real VLUE data (market-neutral)
                        common = [d for d in asset_ret_dates if d in vlue_ret_map and d in spy_ret_map]
                        if len(common) < 60:
                            print(f"❌ Not enough common dates for {ticker} vs VLUE ({len(common)} records)")
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
                                print(f"❌ Error calculating VALUE beta for {ticker}: {e}")
                                continue
                    
                    elif factor == "QUALITY":
                        # Use real QUAL data (market-neutral)
                        common = [d for d in asset_ret_dates if d in qual_ret_map and d in spy_ret_map]
                        if len(common) < 60:
                            print(f"❌ Not enough common dates for {ticker} vs QUAL ({len(common)} records)")
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
                                print(f"❌ Error calculating QUALITY beta for {ticker}: {e}")
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
            
            result = {
                "factor_exposures": factor_exposures,
                "r2_data": r2_data,
                "available_factors": available_factors,
                "available_tickers": all_tickers
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
            
            # 2) Sort malejąco po wadze %
            portfolio_data.sort(key=lambda x: x['weight'], reverse=True)
            
            # 3) KPI koncentracji
            w_frac = np.array([it['weight_frac'] for it in portfolio_data])
            largest_position, top3, top5, top10, hhi, effective_positions = concentration_metrics(w_frac)
            
            # Mock sector and market cap data (wymuszony fallback)
            sector_data = {
                'ULTY': {'sector': 'Communication Services', 'market_cap': 27.70},
                'RDDT': {'sector': 'Communication Services', 'market_cap': 2349.31},
                'GOOGL': {'sector': 'Communication Services', 'market_cap': 1802.65},
                'META': {'sector': 'Communication Services', 'market_cap': 270.52},
                'AMD': {'sector': 'Technology', 'market_cap': 7.83},
                'BULL': {'sector': 'Technology', 'market_cap': 73.40},
                'SNOW': {'sector': 'Technology', 'market_cap': 123.27},
                'APP': {'sector': 'Communication Services', 'market_cap': 32.09},
                'SMCI': {'sector': 'Technology', 'market_cap': 1021.50},
                'TSLA': {'sector': 'Consumer Cyclical', 'market_cap': 1021.50},
                'BRK-B': {'sector': 'Financial Services', 'market_cap': 850.00},
                'DOMO': {'sector': 'Technology', 'market_cap': 15.00},
                'QQQM': {'sector': 'Technology', 'market_cap': 50.00},
                'SGOV': {'sector': 'Financial Services', 'market_cap': 25.00}
            }
            for item in portfolio_data:
                ticker = item['ticker']
                item['sector'] = sector_data.get(ticker, {}).get('sector', 'Unknown')
                item['market_cap'] = sector_data.get(ticker, {}).get('market_cap', 0.0)
            
            # 4) Sektor (agregacja po frakcjach!)
            from collections import defaultdict
            sector_w = defaultdict(float)
            for it in portfolio_data:
                s = it.get('sector', 'Unknown')
                sector_w[s] += it['weight_frac']
            
            sector_concentration = {
                'sectors': list(sector_w.keys()),
                'weights': [v*100.0 for v in sector_w.values()],   # %
            }
            hhi_sec = sum(v*v for v in sector_w.values())          # ✅ na ułamkach
            sector_concentration['hhi'] = hhi_sec
            sector_concentration['effective_sectors'] = 1.0/hhi_sec if hhi_sec>0 else 0.0
            
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
            dates, closes = self._get_close_series(db, s)
            if len(closes) < 2:
                ret_map[s] = ([], np.array([]))
                continue
            # przytnij końcówkę (ostatnie ~lookback dni)
            dates = dates[-(lookback_days+2):]
            closes = closes[-(lookback_days+2):]
            rd, r = self._log_returns_from_series(dates, closes)
            ret_map[s] = (rd, r)
        return ret_map

    def _intersect_and_stack(self, ret_map: Dict[str, Any], symbols: List[str]):
        """Wspólne daty i macierz R [T x N] w kolejności symbols."""
        return stack_common_returns(ret_map, symbols)

    def get_risk_scoring(self, db: Session, username: str = "admin") -> Dict[str, Any]:
        """MVP risk scoring: szybko i bez spiny."""
        # 1) wagi i lista tickerów usera
        conc = self.get_concentration_risk_data(db, username)
        if "error" in conc: 
            return {"error": conc["error"]}
        positions = conc["portfolio_data"]
        if not positions:
            return {"error":"No positions"}
        tickers = [p['ticker'] for p in positions]
        w = np.array([p['weight_frac'] for p in positions], dtype=float)  # sum ~1

        # 2) serie zwrotów: tickery + SPY + ETFy faktorowe
        factor_proxies = {"MOMENTUM":"MTUM","SIZE":"IWM","VALUE":"VLUE","QUALITY":"QUAL"}
        needed = list(set(tickers + ["SPY"] + list(factor_proxies.values())))
        ret_map = self._get_return_series_map(db, needed, lookback_days=180)

        # 3) macierz zwrotów pozycji, wspólne daty (ostatnie ~60)
        dates, R, active = self._intersect_and_stack(ret_map, tickers)
        if R.size == 0 or len(dates) < 40:
            return {"error":"Insufficient overlapping history"}
        
        # przeskaluj wagi tylko na aktywne tickery
        w_map = {p["ticker"]: p["weight_frac"] for p in positions}
        w = np.array([w_map[s] for s in active], dtype=float)
        w = w / w.sum()  # renormalizuj
        
        # portfelowe zwroty przy stałych wagach (snapshot) 
        R = clamp(R, STRESS_LIMITS["clamp_return_abs"])  # spójność z regime/scenariuszami
        rp = (R @ w)  # T x 1
        T = len(rp)
        # przytnij do 60dni
        window = min(60, T)
        dates_win = dates[-window:]

        # Build index maps
        idx_port = {d:i for i,d in enumerate(dates)}

        # SPY alignment
        d_spy, r_spy_full = ret_map.get("SPY", ([], np.array([])))
        spy_idx = {d:i for i,d in enumerate(d_spy)}
        dates_mkt = [d for d in dates_win if d in spy_idx]
        if len(dates_mkt) < 30:
            # degrade gracefully
            dates_mkt = dates_win  # fallback
            r_spy = np.zeros(len(dates_mkt))
        else:
            r_spy = np.array([r_spy_full[spy_idx[d]] for d in dates_mkt], dtype=float)
        rp_win = np.array([rp[idx_port[d]] for d in dates_mkt], dtype=float)

        # 4) metryki surowe
        # vol ann
        sigma_ann = annualized_vol(rp_win)
        # market beta
        beta_mkt = ols_beta(rp_win, r_spy)[0]

        # factors alignment
        betas = {}
        for fac, etf in factor_proxies.items():
            d_f, r_f_full = ret_map.get(etf, ([], np.array([])))
            f_idx = {d:i for i,d in enumerate(d_f)}
            dates_fac = [d for d in dates_mkt if d in f_idx]
            if len(dates_fac) < 30:
                betas[fac] = 0.0
                continue
            rf = np.array([r_f_full[f_idx[d]] for d in dates_fac], dtype=float)
            rs = np.array([r_spy[dates_mkt.index(d)] for d in dates_fac], dtype=float)
            rp_fac = np.array([rp_win[dates_mkt.index(d)] for d in dates_fac], dtype=float)
            f_mn = rf - rs
            betas[fac] = ols_beta(rp_fac, f_mn)[0]

        # correlations (NaN-safe, drop zero-variance columns)
        R_sub = R[-window:, :]
        avg_corr, pairs, high_pairs = avg_and_high_corr(R_sub, threshold=0.7)

        # max drawdown on rp_win
        _, max_dd = drawdown(rp_win)

        # 5) concentration (HHI i Neff)
        hhi = float(conc["concentration_metrics"]["herfindahl_index"])  # już w [0..1]
        neff = float(conc["concentration_metrics"]["effective_positions"])

        # 6) skoring (0..1)
        raw_metrics = {
            "hhi": hhi,
            "vol_ann_pct": sigma_ann * 100,
            "beta_market": beta_mkt,
            "avg_pair_corr": avg_corr,
            "max_drawdown_pct": max_dd * 100,
            "factor_l1": sum(abs(betas[k]) for k in betas)
        }
        
        WEIGHTS = {
            "concentration": 0.30,
            "volatility":    0.25,
            "factor":        0.20,
            "correlation":   0.15,
            "market":        0.10,
            "stress":        0.00,
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
            "score_weights": weights,
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
        """Zwraca (dates, log_returns) w [start_d, end_d] dla symbolu. Może zwrócić [] gdy brak danych."""
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
        """Zwraca listę pozycji (ticker, weight_frac)."""
        conc = self.get_concentration_risk_data(db, username)
        if "error" in conc: 
            return [], 0.0
        positions = conc["portfolio_data"]
        w_sum = sum(p.get("weight_frac", 0.0) for p in positions)
        if w_sum <= 0:
            return [], 0.0
        # normalizacja dla pewności
        for p in positions:
            p["weight_frac"] = float(p["weight_frac"]) / w_sum
        return positions, 1.0

    def get_market_regime(self, db: Session, username: str = "admin") -> Dict[str, Any]:
        """Regime = vol/corr/mom na ostatnich ~60d + etykieta."""
        positions, ok = self._portfolio_snapshot(db, username)
        if not ok or not positions:
            return {"error":"No positions"}

        tickers = [p["ticker"] for p in positions]
        w = np.array([p["weight_frac"] for p in positions], dtype=float)

        # zwroty z ostatnich dni
        lookback = STRESS_LIMITS["lookback_regime_days"] + 2
        ret_map = self._get_return_series_map(db, tickers, lookback_days=lookback)
        dates, R, active = self._intersect_and_stack(ret_map, tickers)
        if R.size == 0 or len(dates) < 40:
            return {"error":"Insufficient data for regime"}

        # przeskaluj wagi tylko na aktywne tickery
        w_map = {p["ticker"]: p["weight_frac"] for p in positions}
        w = np.array([w_map[s] for s in active], dtype=float)
        w = w / w.sum()  # renormalizuj

        R = clamp(R, STRESS_LIMITS["clamp_return_abs"])
        rp = R @ w
        window = min(STRESS_LIMITS["lookback_regime_days"], len(rp))
        rp = rp[-window:]

        # Calculate regime metrics
        vol_ann, avg_corr, mom, radar, label = regime_metrics(R, w, REGIME_THRESH)

        return {
            "label": label,
            "volatility_pct": vol_ann * 100.0,
            "correlation": avg_corr,
            "momentum_pct": mom * 100.0,
            "radar": radar
        }

    def get_historical_scenarios(self, db: Session, username: str = "admin",
                                 scenarios: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Wylicza PnL i DD dla historycznych scenariuszy. Pomija scenariusze z niskim pokryciem wag lub zbyt krótkie."""
        positions, ok = self._portfolio_snapshot(db, username)
        if not ok or not positions:
            return {"error":"No positions"}

        tickers = [p["ticker"] for p in positions]
        w_map = {p["ticker"]: p["weight_frac"] for p in positions}

        scenarios = scenarios or STRESS_SCENARIOS
        analyzed, excluded = [], []

        for sc in scenarios:
            name, start_d, end_d = sc["name"], sc["start"], sc["end"]

            # pobierz zwroty w oknie
            ret_map = {}
            included, w_cov = [], 0.0
            for t in tickers:
                dts, r = self._get_returns_between_dates(db, t, start_d, end_d)
                if len(r) >= 2:  # minimalnie
                    ret_map[t] = (dts, r)
                    included.append(t)
                    w_cov += w_map.get(t, 0.0)

            if w_cov < STRESS_LIMITS["scenario_min_weight_coverage"]:
                excluded.append({"name": name, "reason": f"Low weight coverage ({w_cov*100:.0f}%)"})
                continue

            if not included:
                excluded.append({"name": name, "reason": "No overlapping data"})
                continue

            # wspólne daty i macierz
            dates, R, active = self._intersect_and_stack(ret_map, included)
            if len(dates) < STRESS_LIMITS["scenario_min_days"]:
                excluded.append({"name": name, "reason": f"Too few common dates ({len(dates)})"})
                continue

            # przeskaluj wagi tylko na aktywne tickery
            w = np.array([w_map[t] for t in active], dtype=float)
            w = w / w.sum()

            R = clamp(R, STRESS_LIMITS["clamp_return_abs"])
            rp = R @ w

            # Calculate scenario PnL and drawdown
            ret_pct, max_dd = scenario_pnl(R, w)

            analyzed.append({
                "name": name,
                "start": start_d.isoformat(),
                "end": end_d.isoformat(),
                "days": len(rp),
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
        """Wrapper pod front – łączy Market Regime + Historical Scenarios."""
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
        
        # Get volatility forecasts for each ticker
        vol_vec = []
        for ticker in tickers:
            metrics = self.calculate_volatility_metrics(db, ticker, vol_model)
            vol = metrics.get('volatility_pct', 8.0) / 100.0  # Convert to fraction
            vol_vec.append(max(vol, 0.005))  # Floor at 0.5%
        
        vol_vec = np.array(vol_vec)
        D = np.diag(vol_vec)  # D = diag(σ)
        
        # Get historical returns for correlation calculation
        ret_map = self._get_return_series_map(db, tickers, lookback_days=252)  # 1 year
        dates, R, active = self._intersect_and_stack(ret_map, tickers)
        
        if R.size == 0 or len(dates) < 60:
            # Fallback to diagonal correlation if insufficient data
            print("⚠️ Insufficient data for correlation, using diagonal matrix")
            n = len(tickers)
            corr_matrix = np.eye(n)
        else:
            # Calculate EWMA correlation matrix
            print(f"Calculating EWMA correlation for {len(active)} tickers with {len(dates)} observations")
            corr_matrix = ewma_corr(R, lam=0.94)
        
        # Build covariance matrix using quant.risk
        return build_cov(vol_vec, corr_matrix)

    # calculate_risk_contribution moved to quant.risk

    def get_forecast_risk_contribution(self, db: Session, username: str = "admin", 
                                      vol_model: str = 'EWMA (5D)') -> Dict[str, Any]:
        """Get Forecast Risk Contribution data for portfolio"""
        try:
            # Get portfolio data
            conc = self.get_concentration_risk_data(db, username)
            if "error" in conc:
                return {"error": conc["error"]}
            
            portfolio_data = conc["portfolio_data"]
            if not portfolio_data:
                return {"error": "No portfolio data"}
            
            # Extract tickers and weights
            tickers = [item['ticker'] for item in portfolio_data]
            weights = [item['weight_frac'] for item in portfolio_data]  # Already 0-1
            
            # Build covariance matrix
            cov_matrix = self.build_covariance_matrix(db, tickers, vol_model)
            if cov_matrix.size == 0:
                return {"error": "Failed to build covariance matrix"}
            
            # Calculate risk contributions using quant.risk
            try:
                mrc, pct_rc, sigma_p = risk_contribution(weights, cov_matrix)
                risk_data = {"marginal_rc": mrc, "total_rc_pct": pct_rc, "portfolio_vol": sigma_p}
            except ValueError as e:
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
            
            return {
                "tickers": [item["ticker"] for item in chart_data],
                "marginal_rc_pct": [item["marginal_rc_pct"] for item in chart_data],
                "total_rc_pct": [item["total_rc_pct"] for item in chart_data],
                "weights_pct": [item["weight_pct"] for item in chart_data],
                "portfolio_vol": risk_data["portfolio_vol"],
                "vol_model": vol_model
            }
            
        except Exception as e:
            print(f"Error calculating forecast risk contribution: {e}")
            return {"error": str(e)} 