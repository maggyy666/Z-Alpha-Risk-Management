import numpy as np
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from database.models.user import User
from database.models.portfolio import Portfolio
from database.models.ticker_data import TickerData
from services.ibkr_service import IBKRService
from datetime import datetime, timedelta

class DataService:
    def __init__(self):
        self.ibkr_service = IBKRService()
        # Stałe tickery które zawsze będą pobierane z IBKR
        self.STATIC_TICKERS = ['SPY']
        
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
        
    def _lambda_from_half_life(self, h: int) -> float:
        """Calculate λ from half-life: λ = 2^(-1/h)"""
        return float(np.exp(-np.log(2) / max(1, h)))
        
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
            
            # Calculate forecast volatility
            print(f"🔍 Calculating {forecast_model} volatility for returns shape: {returns.shape}")
            forecast_vol = self._calculate_forecast_volatility(returns, forecast_model)
            print(f"📊 {symbol}: Calculated volatility: {forecast_vol:.2f}%")
            
            # Calculate Sharpe ratio
            sharpe_ratio = ((mean_daily * 252) - risk_free_annual) / (std_daily * np.sqrt(252)) if std_daily > 0 else 0.0
            
            # Get last price
            last_price = float(historical_data[-1].close_price)
            
            metrics = {
                'volatility': forecast_vol,
                'mean_return': mean_annual,
                'sharpe_ratio': sharpe_ratio,
                'last_price': last_price
            }
            
            print(f"🔍 {symbol} metrics: {metrics}")
            return metrics
            
        except Exception as e:
            print(f"❌ Error calculating metrics for {symbol}: {e}")
            return {}
    
    def _calculate_forecast_volatility(self, returns: np.ndarray, model: str) -> float:
        """Calculate forecast volatility using different models"""
        if len(returns) == 0:
            return 0.0
        
        print(f"🔍 Calculating {model} volatility for returns shape: {returns.shape}")
        
        try:
            name = model.upper()
            if name.startswith('EWMA'):
                if '5D' in name:
                    lam = self._lambda_from_half_life(5)  # λ ≈ 0.8706
                elif '30D' in name:
                    lam = self._lambda_from_half_life(30)  # λ ≈ 0.9772
                elif '200D' in name:
                    lam = self._lambda_from_half_life(200)  # λ ≈ 0.9965
                else:
                    lam = 0.94  # fallback
                return self._ewma_volatility(returns, lambda_param=lam)
            elif 'GARCH' in name and 'E' not in name:
                return self._garch_volatility(returns)
            elif 'E-GARCH' in name or 'EGARCH' in name:
                return self._egarch_volatility(returns)
            else:
                # Default to simple historical volatility
                return np.std(returns, ddof=1) * np.sqrt(252) * 100
            
        except Exception as e:
            print(f"❌ Error in {model}: {e}")
            return np.std(returns, ddof=1) * np.sqrt(252) * 100
    
    def _ewma_volatility(self, returns: np.ndarray, lambda_param: float = 0.94) -> float:
        """EWMA (RiskMetrics): vol w % rocznie z λ"""
        if len(returns) < 2:
            return 0.0
        
        # Użyj podanego λ
        lam = lambda_param
        var = float(returns[0] ** 2)
        for r in returns[1:]:
            var = lam * var + (1.0 - lam) * (float(r) ** 2)
        sigma_daily = np.sqrt(var)
        sigma_annual_pct = sigma_daily * np.sqrt(252.0) * 100.0
        return float(sigma_annual_pct)

    def _garch_volatility(self, returns: np.ndarray) -> float:
        """Simple GARCH(1,1) volatility forecast - fixed parameters (not calibrated)"""
        if len(returns) < 100:  # Zwiększone z 50 na 100
            return np.std(returns, ddof=1) * np.sqrt(252) * 100

        # Fixed parameters (α + β < 1 for stationarity)
        omega = 0.000001
        alpha = 0.1
        beta = 0.8

        # Użyj pierwszych 100 obserwacji do inicjalizacji
        var = np.var(returns[:100])
        for i in range(100, len(returns)):  # Zwiększone z 50 na 100
            var = omega + alpha * returns[i-1]**2 + beta * var
        return np.sqrt(var * 252) * 100

    def _egarch_volatility(self, returns: np.ndarray) -> float:
        """Simple EGARCH volatility forecast - fixed parameters (not calibrated)"""
        if len(returns) < 100:  # Zwiększone z 50 na 100
            return np.std(returns, ddof=1) * np.sqrt(252) * 100

        # Fixed parameters
        omega = -0.1
        alpha = 0.1
        gamma = 0.1
        beta = 0.9

        # Użyj pierwszych 100 obserwacji do inicjalizacji
        log_var = np.log(np.var(returns[:100]))
        for i in range(100, len(returns)):  # Zwiększone z 50 na 100
            z = returns[i-1] / np.sqrt(np.exp(log_var))
            log_var = omega + alpha * abs(z) + gamma * z + beta * log_var
        return np.sqrt(np.exp(log_var) * 252) * 100

    def get_portfolio_volatility_data(self, db: Session, username: str = "admin",
                                      forecast_model: str = 'EWMA (5D)',
                                      vol_floor_annual_pct: float = 8.0,
                                      risk_free_annual: float = 0.0) -> List[Dict[str, Any]]:
        """Get volatility data for user's portfolio tickers + static tickers"""
        portfolio_data = []

        # Get all tickers: user portfolio + static tickers
        all_tickers = self.get_all_tickers(db, username)
        if not all_tickers:
            print(f"❌ No tickers found for user {username}")
            return []

        # Get portfolio items with shares info (only for user's portfolio)
        user = db.query(User).filter(User.username == username).first()
        portfolio_items = db.query(Portfolio).filter(Portfolio.user_id == user.id).all()
        shares_map = {item.ticker_symbol: item.shares for item in portfolio_items}

        # 1) Zbierz metryki dla wszystkich tickerów
        for symbol in all_tickers:
            print(f"🔍 Processing {symbol}...")
            m = self.calculate_volatility_metrics(db, symbol, forecast_model, risk_free_annual)
            print(f"🔍 {symbol} metrics: {m}")
            if m:
                # Dla statycznych tickerów używamy domyślnej liczby shares
                shares = shares_map.get(symbol, 1000) if symbol in shares_map else 1000
                portfolio_data.append({
                    'symbol': symbol,
                    'forecast_volatility_pct': float(m.get('volatility', 0.0)),
                    'last_price': float(m.get('last_price', 0.0)),
                    'sharpe_ratio': float(m.get('sharpe_ratio', 0.0)),
                    'shares': shares,
                    'is_static': symbol in self.STATIC_TICKERS
                })
            else:
                print(f"❌ No metrics for {symbol}")

        if not portfolio_data:
            return []

        # 2) Current MV (przed liczeniem wag)
        for item in portfolio_data:
            lp = item['last_price']
            shares = item['shares']
            item['current_mv'] = float(lp) * float(shares)

        total_portfolio_value = float(sum(d['current_mv'] for d in portfolio_data)) if portfolio_data else 0.0
        if total_portfolio_value <= 0:
            return portfolio_data

        # 3) Current weights (po policzeniu totalu)
        for item in portfolio_data:
            item['current_weight_pct'] = 100.0 * item['current_mv'] / total_portfolio_value

        # 4) Inverse-vol weights – vol jako ułamek + floor
        vols_frac = [
            max(d['forecast_volatility_pct'] / 100.0, vol_floor_annual_pct / 100.0)
            for d in portfolio_data
        ]
        inv = [1.0 / v for v in vols_frac]
        denom = float(sum(inv)) if inv else 1.0

        for item, inv_i in zip(portfolio_data, inv):
            item['adj_volatility_weight_pct'] = 100.0 * inv_i / denom

        # 5) Target MV i delty
        for item in portfolio_data:
            target_w = item['adj_volatility_weight_pct'] / 100.0
            item['target_mv'] = total_portfolio_value * target_w
            item['delta_mv'] = item['target_mv'] - item['current_mv']
            lp = item['last_price']
            item['delta_shares'] = int(np.floor(item['delta_mv'] / lp)) if lp > 0 else 0

        return portfolio_data

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
        """Get factor exposure data for portfolio analysis"""
        try:
            print(f"🔍 Getting factor exposure data for user: {username}")
            
            # Get all tickers: user portfolio + static tickers
            all_tickers = self.get_all_tickers(db, username)
            print(f"📊 All tickers: {all_tickers}")
            
            if not all_tickers:
                print("❌ No tickers found")
                return {"factor_exposures": [], "r2_data": [], "available_factors": [], "available_tickers": []}

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
            
            # Wczytaj serię SPY z bazy (MARKET proxy)
            print("📊 Loading SPY data for MARKET factor...")
            spy_dates, spy_closes = self._get_close_series(db, "SPY")
            spy_ret_dates, spy_rets = self._log_returns_from_series(spy_dates, spy_closes)
            spy_ret_map = dict(zip(spy_ret_dates, spy_rets))  # date -> r_SPY
            print(f"📊 SPY data: {len(spy_ret_dates)} return dates from {min(spy_ret_dates)} to {max(spy_ret_dates)}")
            
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
                        # Find common dates between asset and SPY
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
                        
                        # Already calculated MARKET - go to next factor
                        continue
                    
                    else:
                        # Mock data for other factors (MOMENTUM, SIZE, VALUE, QUALITY)
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
                                beta = np.linalg.lstsq(x_with_const, y, rcond=None)[0][1]
                                
                                factor_exposures.append({
                                    "date": date.isoformat(),
                                    "ticker": ticker,
                                    "factor": factor,
                                    "beta": round(beta, 3)
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
            
            print(f"✅ Generated {len(factor_exposures)} factor exposures and {len(r2_data)} R² records")
            
            return {
                "factor_exposures": factor_exposures,
                "r2_data": r2_data,
                "available_factors": available_factors,
                "available_tickers": all_tickers
            }
            
        except Exception as e:
            print(f"Error getting factor exposure data: {e}")
            return {"factor_exposures": [], "r2_data": [], "available_factors": [], "available_tickers": []} 