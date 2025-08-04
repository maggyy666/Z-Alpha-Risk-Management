import time
import threading
from typing import Optional, Dict, Any
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import Order
from sqlalchemy.orm import Session
from database.models.ticker import Ticker
from database.models.historical_data import HistoricalData
from datetime import datetime, timedelta

class IBKRConnection(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.data = []
        self.connected = False
        self.next_order_id = None
        self.historical_data = {}
        self.current_contract = None
        
    def error(self, reqId, errorCode, errorString):
        print(f"Error {errorCode}: {errorString}")
        
    def nextValidId(self, orderId):
        self.next_order_id = orderId
        print(f"Next valid order ID: {orderId}")
        
    def connectAck(self):
        self.connected = True
        print("Successfully connected to IBKR!")
        
    def connectionClosed(self):
        self.connected = False
        print("Connection to IBKR closed")
        
    def historicalData(self, reqId, bar):
        if reqId not in self.historical_data:
            self.historical_data[reqId] = []
        self.historical_data[reqId].append({
            'date': bar.date,
            'open': bar.open,
            'high': bar.high,
            'low': bar.low,
            'close': bar.close,
            'volume': bar.volume
        })
        
    def historicalDataEnd(self, reqId, start, end):
        print(f"Historical data received for reqId: {reqId}")
        
    def contractDetails(self, reqId, contractDetails):
        print(f"Contract details for {contractDetails.contract.symbol}")

class IBKRService:
    def __init__(self):
        self.connection = None
        
    def connect(self, host: str = '127.0.0.1', port: int = 7497, 
                client_id: int = 1, timeout: int = 20) -> bool:
        """Connect to IBKR API"""
        try:
            self.connection = IBKRConnection()
            print(f"Attempting to connect to IBKR at {host}:{port}...")
            self.connection.connect(host, port, client_id)
            
            # Start the message processing thread
            self.connection.run()
            
            # Wait for connection
            start_time = time.time()
            while not self.connection.connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)
                
            return self.connection.connected
                
        except Exception as e:
            print(f"Error connecting to IBKR: {e}")
            return False
    
    def get_historical_data(self, symbol: str, duration: str = "1 Y", 
                          bar_size: str = "1 day") -> Optional[list]:
        """Get historical data for a symbol"""
        if not self.connection or not self.connection.connected:
            print("Not connected to IBKR")
            return None
            
        try:
            # Create contract
            contract = Contract()
            contract.symbol = symbol
            contract.secType = "STK"
            contract.exchange = "SMART"
            contract.currency = "USD"
            
            # Request historical data
            req_id = len(self.connection.historical_data) + 1
            self.connection.reqHistoricalData(
                req_id, contract, "", duration, bar_size, 
                "TRADES", 1, 1, False, []
            )
            
            # Wait for data
            time.sleep(2)
            
            return self.connection.historical_data.get(req_id, [])
            
        except Exception as e:
            print(f"Error getting historical data for {symbol}: {e}")
            return None
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol"""
        if not self.connection or not self.connection.connected:
            print("Not connected to IBKR")
            return None
            
        try:
            # Create contract
            contract = Contract()
            contract.symbol = symbol
            contract.secType = "STK"
            contract.exchange = "SMART"
            contract.currency = "USD"
            
            # For now, return None - we'll implement real-time data later
            return None
            
        except Exception as e:
            print(f"Error getting current price for {symbol}: {e}")
            return None
    
    def disconnect(self):
        """Disconnect from IBKR"""
        if self.connection:
            self.connection.disconnect() 