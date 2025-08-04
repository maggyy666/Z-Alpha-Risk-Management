import numpy as np
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from database.models.user import User
from database.models.portfolio import Portfolio
from database.models.ticker_data import TickerData
from services.ibkr_service import IBKRService
from datetime import datetime, timedelta
import random

class DataService:
    def __init__(self):
        self.ibkr_service = IBKRService()
        
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
            
            # Store historical data
            for bar in historical_data:
                # Convert date string to datetime
                date_str = bar['date']
                if len(date_str) == 8:  # YYYYMMDD format
                    date_obj = datetime.strptime(date_str, '%Y%m%d').date()
                else:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                
                # Check if data already exists
                existing_data = db.query(TickerData).filter(
                    TickerData.ticker_symbol == symbol,
                    TickerData.date == date_obj
                ).first()
                
                if not existing_data:
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
                                   forecast_model: str = 'EWMA (5D)') -> Dict[str, float]:
        """Calculate volatility metrics for a ticker using different forecast models"""
        try:
            # Get historical data for this ticker
            historical_data = (db.query(TickerData)
                                 .filter(TickerData.ticker_symbol == symbol)
                                 .order_by(TickerData.date.desc())
                                 .limit(500)
                                 .all())

            n = len(historical_data)
            print(f"📊 {symbol}: Found {n} historical records")
            if n < 30:
                print(f"❌ {symbol}: Not enough data ({n} < 30)")
                return {}

            # UWAGA: odwracamy na kolejność rosnącą dat
            historical_data = list(reversed(historical_data))

            prices = np.array([row.close_price for row in historical_data], dtype=float)
            # sanity check: brak/zero lub wartości ujemne
            prices = prices[np.isfinite(prices) & (prices > 0)]
            if len(prices) < 30:
                print(f"❌ {symbol}: Not enough clean prices")
                return {}

            # log-returns w poprawnej kolejności (t−1 -> t)
            returns = np.diff(np.log(prices))
            print(f"📊 {symbol}: Prices range: {min(prices):.2f} - {max(prices):.2f}")
            print(f"📊 {symbol}: Returns shape: {returns.shape}, mean: {np.mean(returns):.6f}")

            # Volatility (annual, w %)
            vol_pct = self._calculate_forecast_volatility(returns, forecast_model)
            print(f"📊 {symbol}: Calculated volatility: {vol_pct:.2f}%")

            # Inne metryki
            mean_daily = float(np.mean(returns))
            std_daily  = float(np.std(returns))
            mean_return_annual_pct = mean_daily * 252 * 100
            sharpe_ratio = (mean_daily * 252) / (std_daily * np.sqrt(252)) if std_daily > 0 else 0.0

            # last_price – fallback do ostatniego close
            last_close = float(prices[-1])
            last_price = last_close

            return {
                'volatility': vol_pct,                  # w %
                'mean_return': mean_return_annual_pct,  # w %
                'sharpe_ratio': sharpe_ratio,
                'last_price': last_price
            }
            
        except Exception as e:
            print(f"Error calculating volatility for {symbol}: {e}")
            return {}
    
    def _calculate_forecast_volatility(self, returns: np.ndarray, model: str) -> float:
        """Calculate forecast volatility using different models"""
        if len(returns) == 0:
            return 0.0
        
        print(f"🔍 Calculating {model} volatility for returns shape: {returns.shape}")
        
        try:
            if model == 'EWMA (5D)':
                result = self._ewma_volatility(returns, half_life=5)
            elif model == 'EWMA (30D)':
                result = self._ewma_volatility(returns, half_life=30)
            elif model == 'EWMA (200D)':
                result = self._ewma_volatility(returns, half_life=200)
            elif model == 'Garch Volatility':
                result = self._garch_volatility(returns)
            elif model == 'E-Garch Volatility':
                result = self._egarch_volatility(returns)
            else:
                # Default to simple historical volatility
                result = np.std(returns) * np.sqrt(252) * 100
            
            print(f"✅ {model} result: {result:.2f}%")
            return result
        except Exception as e:
            print(f"❌ Error in {model}: {e}")
            return np.std(returns) * np.sqrt(252) * 100
    
    def _ewma_volatility(self, returns: np.ndarray, half_life: int) -> float:
        """EWMA (RiskMetrics): vol w % rocznie"""
        if len(returns) < 2:
            return 0.0
        lam = float(np.exp(-np.log(2) / max(1, half_life)))
        var = float(returns[0] ** 2)
        for r in returns[1:]:
            var = lam * var + (1.0 - lam) * (float(r) ** 2)
        sigma_daily = np.sqrt(var)
        sigma_annual_pct = sigma_daily * np.sqrt(252.0) * 100.0
        return float(sigma_annual_pct)

    def _garch_volatility(self, returns: np.ndarray) -> float:
        """Simple GARCH(1,1) volatility forecast"""
        if len(returns) < 50:
            return np.std(returns) * np.sqrt(252) * 100

        omega = 0.000001
        alpha = 0.1
        beta = 0.8

        var = np.var(returns[:50])
        for i in range(50, len(returns)):
            var = omega + alpha * returns[i-1]**2 + beta * var
        return np.sqrt(var * 252) * 100

    def _egarch_volatility(self, returns: np.ndarray) -> float:
        """Simple EGARCH volatility forecast"""
        if len(returns) < 50:
            return np.std(returns) * np.sqrt(252) * 100

        omega = -0.1
        alpha = 0.1
        gamma = 0.1
        beta = 0.9

        log_var = np.log(np.var(returns[:50]))
        for i in range(50, len(returns)):
            z = returns[i-1] / np.sqrt(np.exp(log_var))
            log_var = omega + alpha * abs(z) + gamma * z + beta * log_var
        return np.sqrt(np.exp(log_var) * 252) * 100

    def get_portfolio_volatility_data(self, db: Session, username: str = "admin",
                                      forecast_model: str = 'EWMA (5D)',
                                      vol_floor_annual_pct: float = 8.0) -> List[Dict[str, Any]]:
        """Get volatility data for user's portfolio tickers"""
        portfolio_data = []

        # Get user's portfolio tickers
        tickers = self.get_user_portfolio_tickers(db, username)
        if not tickers:
            print(f"❌ No portfolio found for user {username}")
            return []

        # Get portfolio items with shares info
        user = db.query(User).filter(User.username == username).first()
        portfolio_items = db.query(Portfolio).filter(Portfolio.user_id == user.id).all()
        shares_map = {item.ticker_symbol: item.shares for item in portfolio_items}

        # 1) Zbierz metryki
        for symbol in tickers:
            print(f"🔍 Processing {symbol}...")
            m = self.calculate_volatility_metrics(db, symbol, forecast_model)
            print(f"🔍 {symbol} metrics: {m}")
            if m:
                portfolio_data.append({
                    'symbol': symbol,
                    'forecast_volatility_pct': float(m.get('volatility', 0.0)),
                    'last_price': float(m.get('last_price', 0.0)),
                    'sharpe_ratio': float(m.get('sharpe_ratio', 0.0)),
                    'shares': shares_map.get(symbol, 1000)
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

    def inject_sample_data(self, db: Session, symbol: str) -> bool:
        """Inject sample historical data for a ticker"""
        try:
            # Check if data already exists
            existing_count = db.query(TickerData).filter(TickerData.ticker_symbol == symbol).count()
            if existing_count > 0:
                print(f"📊 {symbol}: Already has {existing_count} records")
                return True

            # Generate sample data
            base_price = 100.0
            current_price = base_price
            data_points = []
            
            for i in range(252):  # 1 year of trading days
                date = datetime.now().date() - timedelta(days=252-i)
                
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
                    'date': date,
                    'open_price': round(open_price, 2),
                    'close_price': round(close_price, 2),
                    'high_price': round(high_price, 2),
                    'low_price': round(low_price, 2),
                    'volume': max(volume, 100000)
                })

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