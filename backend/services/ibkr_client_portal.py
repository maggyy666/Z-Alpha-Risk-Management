import requests
import json
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import numpy as np

class IBKRClientPortalAPI:
    """IBKR Client Portal Web API integration"""
    
    def __init__(self, base_url: str = "https://localhost:5000/v1/portal"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.verify = False  # For localhost SSL
        self.authenticated = False
        
    def authenticate(self) -> bool:
        """Authenticate with IBKR Client Portal"""
        try:
            # Step 1: Initiate session
            response = self.session.post(f"{self.base_url}/iserver/auth/ssodh/init")
            if response.status_code != 200:
                print(f"Failed to initiate session: {response.status_code}")
                return False
                
            # Step 2: Validate session
            response = self.session.post(f"{self.base_url}/iserver/auth/ssodh/validate")
            if response.status_code != 200:
                print(f"Failed to validate session: {response.status_code}")
                return False
                
            # Step 3: Reauthenticate
            response = self.session.post(f"{self.base_url}/iserver/reauthenticate")
            if response.status_code != 200:
                print(f"Failed to reauthenticate: {response.status_code}")
                return False
                
            self.authenticated = True
            print("Successfully authenticated with IBKR Client Portal")
            return True
            
        except Exception as e:
            print(f"Authentication error: {e}")
            return False
    
    def get_accounts(self) -> List[Dict[str, Any]]:
        """Get list of accounts"""
        try:
            response = self.session.get(f"{self.base_url}/portfolio/accounts")
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to get accounts: {response.status_code}")
                return []
        except Exception as e:
            print(f"Error getting accounts: {e}")
            return []
    
    def get_positions(self, account_id: str) -> List[Dict[str, Any]]:
        """Get portfolio positions"""
        try:
            response = self.session.get(f"{self.base_url}/portfolio/{account_id}/positions/0")
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to get positions: {response.status_code}")
                return []
        except Exception as e:
            print(f"Error getting positions: {e}")
            return []
    
    def get_market_data_snapshot(self, conids: List[str], fields: List[str] = ["31"]) -> Dict[str, Any]:
        """Get market data snapshot for conids"""
        try:
            conids_str = ",".join(conids)
            fields_str = ",".join(fields)
            url = f"{self.base_url}/iserver/marketdata/snapshot?conids={conids_str}&fields={fields_str}"
            
            response = self.session.get(url)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to get market data: {response.status_code}")
                return {}
        except Exception as e:
            print(f"Error getting market data: {e}")
            return {}
    
    def get_historical_data(self, conid: str, period: str = "1y", bar: str = "1d") -> List[Dict[str, Any]]:
        """Get historical data for a conid"""
        try:
            url = f"{self.base_url}/iserver/marketdata/history"
            params = {
                "conid": conid,
                "period": period,
                "bar": bar
            }
            
            response = self.session.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                return data.get("data", [])
            else:
                print(f"Failed to get historical data for {conid}: {response.status_code}")
                return []
        except Exception as e:
            print(f"Error getting historical data for {conid}: {e}")
            return []
    
    def get_contract_info(self, conid: str) -> Optional[Dict[str, Any]]:
        """Get contract information"""
        try:
            response = self.session.get(f"{self.base_url}/iserver/contract/{conid}/info")
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to get contract info for {conid}: {response.status_code}")
                return None
        except Exception as e:
            print(f"Error getting contract info for {conid}: {e}")
            return None

class PortfolioDataService:
    """Service for calculating portfolio volatility and weights"""
    
    def __init__(self):
        self.ibkr_api = IBKRClientPortalAPI()
        
    def calculate_ewma_volatility(self, returns: List[float], half_life: int = 30) -> float:
        """Calculate EWMA volatility"""
        if len(returns) < 2:
            return 0.0
            
        # Calculate lambda
        lambda_param = np.exp(-np.log(2) / half_life)
        
        # Initialize variance
        variance = np.var(returns)
        
        # EWMA recursion
        for i in range(1, len(returns)):
            variance = lambda_param * variance + (1 - lambda_param) * returns[i-1]**2
        
        # Annualize
        daily_vol = np.sqrt(variance)
        annual_vol = daily_vol * np.sqrt(252)
        
        return annual_vol * 100  # Convert to percentage
    
    def calculate_portfolio_metrics(self, positions: List[Dict], prices: Dict[str, float]) -> List[Dict[str, Any]]:
        """Calculate portfolio metrics for volatility-based sizing"""
        portfolio_data = []
        
        for position in positions:
            conid = str(position.get('conid', ''))
            symbol = position.get('symbol', '')
            quantity = position.get('position', 0)
            currency = position.get('currency', 'USD')
            
            if not conid or not symbol or quantity == 0:
                continue
                
            # Get current price
            current_price = prices.get(conid, 0)
            if current_price == 0:
                continue
                
            # Calculate current market value
            current_mv = quantity * current_price
            
            # Get historical data for volatility calculation
            historical_data = self.ibkr_api.get_historical_data(conid)
            if len(historical_data) < 30:
                continue
                
            # Calculate returns
            closes = [float(bar.get('c', 0)) for bar in historical_data if bar.get('c')]
            if len(closes) < 2:
                continue
                
            # Calculate log returns
            returns = np.diff(np.log(closes))
            
            # Calculate volatility
            volatility = self.calculate_ewma_volatility(returns)
            
            # Apply volatility floor (8% annual)
            volatility = max(volatility, 8.0)
            
            portfolio_data.append({
                'symbol': symbol,
                'conid': conid,
                'quantity': quantity,
                'current_price': current_price,
                'current_mv': current_mv,
                'forecast_volatility': volatility,
                'currency': currency
            })
        
        return portfolio_data
    
    def calculate_volatility_weights(self, portfolio_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate volatility-adjusted weights"""
        if not portfolio_data:
            return []
            
        # Calculate total market value
        total_mv = sum(item['current_mv'] for item in portfolio_data)
        
        # Calculate inverse volatility weights
        inverse_vols = [1.0 / item['forecast_volatility'] for item in portfolio_data]
        sum_inverse_vols = sum(inverse_vols)
        
        # Calculate target weights
        for i, item in enumerate(portfolio_data):
            target_weight = inverse_vols[i] / sum_inverse_vols
            current_weight = item['current_mv'] / total_mv if total_mv > 0 else 0
            
            # Calculate target market value
            target_mv = target_weight * total_mv
            
            # Calculate deltas
            delta_mv = target_mv - item['current_mv']
            delta_shares = round(delta_mv / item['current_price']) if item['current_price'] > 0 else 0
            
            item.update({
                'current_weight': current_weight * 100,  # Convert to percentage
                'adj_volatility_weight': target_weight * 100,  # Convert to percentage
                'target_mv': target_mv,
                'delta_mv': delta_mv,
                'delta_shares': delta_shares
            })
        
        return portfolio_data
    
    def get_portfolio_volatility_data(self) -> List[Dict[str, Any]]:
        """Get complete portfolio volatility data"""
        try:
            # Authenticate
            if not self.ibkr_api.authenticate():
                print("Failed to authenticate with IBKR")
                return []
            
            # Get accounts
            accounts = self.ibkr_api.get_accounts()
            if not accounts:
                print("No accounts found")
                return []
            
            account_id = accounts[0].get('accountId')  # Use first account
            
            # Get positions
            positions = self.ibkr_api.get_positions(account_id)
            if not positions:
                print("No positions found")
                return []
            
            # Filter for stocks/ETFs only
            stock_positions = [p for p in positions if p.get('assetClass') in ['STK', 'ETF']]
            
            if not stock_positions:
                print("No stock/ETF positions found")
                return []
            
            # Get conids for market data
            conids = [str(p.get('conid')) for p in stock_positions if p.get('conid')]
            
            # Get market data snapshot
            market_data = self.ibkr_api.get_market_data_snapshot(conids)
            
            # Extract prices
            prices = {}
            for item in market_data:
                conid = str(item.get('conid', ''))
                if conid:
                    # Get last price (field 31)
                    price_data = item.get('31', {})
                    if price_data:
                        prices[conid] = float(price_data)
            
            # Calculate portfolio metrics
            portfolio_data = self.calculate_portfolio_metrics(stock_positions, prices)
            
            # Calculate volatility weights
            final_data = self.calculate_volatility_weights(portfolio_data)
            
            return final_data
            
        except Exception as e:
            print(f"Error getting portfolio data: {e}")
            return [] 