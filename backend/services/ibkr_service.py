import threading
import time
import random
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List, Optional, Any
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.common import TickerId
from ibapi.order import Order
from sqlalchemy.orm import Session
from database.models.ticker import Ticker, TickerInfo
from database.models.historical_data import HistoricalData
from datetime import datetime, timedelta

class IBKRConnection(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.data = {}  # Changed from [] to {}
        self.connected = False
        self.next_order_id = None
        self.historical_data = {}
        self.current_contract = None
        # Bid/Ask data storage
        self.bid_ask_data = {}
        self.market_data_requests = {}
        # Fundamental data storage
        self.fundamental_xml = {}
        self.fundamental_done = {}
        self.fundamental_error = {}
        
    def error(self, reqId, errorCode, errorString):
        print(f"Error {errorCode}: {errorString}")
        # Handle market data permission errors
        if errorCode == 354:
            print(f"Market data permission denied for reqId: {reqId}")
            if reqId in self.market_data_requests:
                self.market_data_requests[reqId]['error'] = True
        # Handle fundamental data errors
        elif errorCode in (200, 354):
            print(f"Fundamental data error {errorCode} for reqId: {reqId}")
            self.fundamental_error[reqId] = errorCode
        
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
        print(f"Historical data completed for reqId {reqId}: {start} to {end}")
        
    def contractDetails(self, reqId, contractDetails):
        """Handle contract details response"""
        print(f"Contract details received for reqId {reqId}")
        # Store contract details for later use
        if reqId not in self.data:
            self.data[reqId] = []
        self.data[reqId].append(contractDetails)
        
    def fundamentalData(self, reqId, data):
        """Handle fundamental data response (XML)"""
        print(f"Fundamental data received for reqId {reqId}")
        self.fundamental_xml[reqId] = data
        
    def fundamentalDataEnd(self, reqId):
        """Handle fundamental data end"""
        print(f"Fundamental data completed for reqId {reqId}")
        self.fundamental_done[reqId] = True
        
    def tickPrice(self, reqId, tickType, price, attrib):
        """Handle real-time price updates"""
        if reqId not in self.bid_ask_data:
            self.bid_ask_data[reqId] = {'bid': None, 'ask': None, 'spread_pct': None, 'volume': None}
        
        if tickType == 1:  # Real-time Bid
            self.bid_ask_data[reqId]['bid'] = price
            print(f"Real-time Bid for reqId {reqId}: {price}")
        elif tickType == 2:  # Real-time Ask
            self.bid_ask_data[reqId]['ask'] = price
            print(f"Real-time Ask for reqId {reqId}: {price}")
        
        # Check if we have both bid and ask
        if (self.bid_ask_data[reqId]['bid'] is not None and 
            self.bid_ask_data[reqId]['ask'] is not None):
            bid = self.bid_ask_data[reqId]['bid']
            ask = self.bid_ask_data[reqId]['ask']
            mid = (bid + ask) / 2
            spread_pct = ((ask - bid) / mid) * 100
            self.bid_ask_data[reqId]['spread_pct'] = spread_pct
            print(f"Spread calculated for reqId {reqId}: {spread_pct:.2f}%")
    
    def tickSize(self, reqId, tickType, size):
        """Handle tick size updates (volume)"""
        if reqId in self.bid_ask_data:
            # Handle delayed market data volume tick types
            if tickType == 69:  # Delayed Bid Size
                print(f"Delayed Bid Size for reqId {reqId}: {size}")
            elif tickType == 70:  # Delayed Ask Size
                print(f"Delayed Ask Size for reqId {reqId}: {size}")
            elif tickType == 8:  # Real-time Volume
                self.bid_ask_data[reqId]['volume'] = size
                print(f"Real-time Volume for reqId {reqId}: {size}")
            elif tickType == 71:  # Delayed Last Size (volume)
                self.bid_ask_data[reqId]['volume'] = size
                print(f"Delayed Volume for reqId {reqId}: {size}")
    
    def tickString(self, reqId, tickType, value):
        """Handle tick string updates"""
        pass  # Not needed for basic bid/ask
    
    def tickGeneric(self, reqId, tickType, value):
        """Handle generic tick updates"""
        pass  # Not needed for basic bid/ask

class IBKRService:
    def __init__(self):
        self.connection = None
        self._client_id_counter = 0
        
    def _get_next_client_id(self):
        """Get next unique client ID"""
        self._client_id_counter += 1
        return 1000 + self._client_id_counter
        
    def connect(self, host: str = '127.0.0.1', port: int = 7496, 
                client_id: int = None, timeout: int = 20) -> bool:
        """Connect to IBKR API"""
        try:
            # Use provided client_id or generate unique one
            if client_id is None:
                client_id = self._get_next_client_id()
                
            self.connection = IBKRConnection()
            print(f"Attempting to connect to IBKR at {host}:{port} with client_id {client_id}...")
            self.connection.connect(host, port, client_id)
            
            # 🔧 PĘTLA W OSOBNYM WĄTKU
            self._thread = threading.Thread(target=self.connection.run, daemon=True)
            self._thread.start()
            
            # Wait for connection AND nextValidId
            start_time = time.time()
            while (time.time() - start_time) < timeout:
                if self.connection.connected and self.connection.next_order_id is not None:
                    print("IBKR ready, nextValidId =", self.connection.next_order_id)
                    return True
                time.sleep(0.05)
            
            print("❌ Timeout connecting to IBKR or waiting for nextValidId")
            return False
            
        except Exception as e:
            print(f"❌ Error connecting to IBKR: {e}")
            return False
    
    def get_fundamentals(self, symbol: str, report_type: str = "ReportSnapshot") -> Optional[Dict[str, Any]]:
        """
        Get fundamental data for a symbol from IBKR - only check if STOCK or ETF
        Returns dict {'type': 'STOCK' or 'ETF', 'company_name': str} or None
        """
        # Bonus optymalizacja: pomijaj IBKR dla ETF-ów
        if self._looks_like_etf(symbol):
            print(f"🔎 {symbol} wygląda na ETF → skip IBKR")
            return {"type": "ETF", "company_name": symbol}
            
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
            
            # Generate unique request ID
            req_id = random.randint(5000, 9000)
            
            # Clear previous fundamental data
            self.connection.fundamental_xml = {}
            self.connection.fundamental_done = {}
            self.connection.fundamental_error = {}
            
            # Request fundamental data
            self.connection.reqFundamentalData(req_id, contract, report_type, [])
            print(f"Requested fundamental data for {symbol} with reqId: {req_id}")
            
            # Wait for fundamental data
            start_time = time.time()
            while (time.time() - start_time) < 8:  # shorter timeout
                if req_id in self.connection.fundamental_xml:
                    xml_data = self.connection.fundamental_xml[req_id]
                    if xml_data:
                        # Parse XML to get company name and determine type
                        result = self._parse_simple_xml(xml_data, symbol)
                        self.connection.fundamental_xml.pop(req_id)
                        return result
                elif req_id in self.connection.fundamental_error:
                    error_code = self.connection.fundamental_error[req_id]
                    if error_code == 430:  # fundamentals not available - likely ETF
                        print(f"⚠️ Fundamentals not available for {symbol} (error 430) - likely ETF")
                        self.connection.fundamental_xml.pop(req_id, None)
                        return {
                            'type': 'ETF',
                            'company_name': symbol
                        }
                    else:
                        print(f"⚠️ IBKR error {error_code} for {symbol}")
                        break
                time.sleep(0.1)
            
            # Timeout or error - cancel request and return None
            self.connection.cancelFundamentalData(req_id)
            print(f"❌ Timeout getting fundamentals for {symbol}")
            return None
            
        except Exception as e:
            print(f"❌ Error getting fundamentals for {symbol}: {e}")
            return None
    
    def _parse_simple_xml(self, xml: str, symbol: str) -> dict:
        """Simple XML parser - only extract company name and determine type"""
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml)
            
            # Get company name
            company_name = None
            for coid in root.findall('.//CoID[@Type="CompanyName"]'):
                if coid.text:
                    company_name = coid.text.strip()
                    break
            
            # If no company name found, use symbol
            if not company_name:
                company_name = symbol
            
            # Check if it looks like ETF based on company name
            if self._looks_like_etf(symbol) or (company_name and self._looks_like_etf(company_name)):
                return {
                    'type': 'ETF',
                    'company_name': company_name
                }
            else:
                return {
                    'type': 'STOCK',
                    'company_name': company_name
                }
                
        except Exception as e:
            print(f"❌ Error parsing XML for {symbol}: {e}")
            return {
                'type': 'STOCK',
                'company_name': symbol
            }
    
    def _looks_like_etf(self, symbol: str) -> bool:
        """Simple check if symbol looks like an ETF"""
        etf_hints = {"etf", "trust", "fund", "treasury", "ultra", "proshares", "ishares", "vanguard", "spy", "qqq", "iwm", "mtum", "vlue", "qual", "sgov", "ulty", "bull"}
        symbol_lower = symbol.lower()
        return any(hint in symbol_lower for hint in etf_hints)
    
    def _get_fundamentals_external_only(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get fundamental data using only external APIs (no IBKR)"""
        try:
            print(f"🌐 Using external API for {symbol}...")
            
            # Add delay to avoid rate limiting
            import time
            time.sleep(0.5)
            
            # Try to get market cap from external API
            market_cap = self._get_market_cap_external(symbol)
            
            # Try to get sector and industry from external API
            sector, industry = self._get_sector_industry_external(symbol)
            
            return {
                'industry': industry or 'Unknown',
                'sector': sector or 'Unknown',
                'market_cap': market_cap,
                'company_name': symbol
            }
            
        except Exception as e:
            print(f"❌ Error getting external data for {symbol}: {e}")
            return None
    
    def _get_sector_industry_external(self, symbol: str) -> tuple:
        """Get sector and industry from external API using yfinance"""
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            sector = info.get('sector', 'Unknown')
            industry = info.get('industry', 'Unknown')
            
            # If no sector/industry found, try to map ETFs based on their names and descriptions
            if sector == 'Unknown' and industry == 'Unknown':
                sector, industry = self._map_etf_to_sector_industry(symbol, info)
            
            print(f"yfinance data for {symbol}: sector={sector}, industry={industry}")
            return sector, industry
            
        except Exception as e:
            print(f"⚠️ Could not get sector/industry for {symbol} with yfinance: {e}")
        return None, None
    
    def _map_etf_to_sector_industry(self, symbol: str, info: dict) -> tuple:
        """Map ETF symbols to sector/industry based on their names and descriptions"""
        short_name = info.get('shortName', '').lower()
        long_name = info.get('longName', '').lower()
        business_summary = info.get('longBusinessSummary', '').lower()
        
        # QQQM - Invesco NASDAQ 100 ETF
        if 'qqqm' in symbol.lower() or 'nasdaq 100' in short_name or 'nasdaq 100' in long_name:
            return 'Technology', 'Technology ETF'
        
        # SGOV - iShares 0-3 Month Treasury Bond ETF
        if 'sgov' in symbol.lower() or 'treasury' in short_name or 'treasury' in long_name or 'treasury' in business_summary:
            return 'Financial Services', 'Government Bonds'
        
        # ULTY - YieldMax Ultra Option Income Strategy ETF
        if 'ulty' in symbol.lower() or 'yieldmax' in short_name or 'yieldmax' in long_name or 'option income' in business_summary:
            return 'Financial Services', 'Options Strategy ETF'
        
        # SPY - SPDR S&P 500 ETF
        if 'spy' in symbol.lower() or 's&p 500' in short_name or 's&p 500' in long_name:
            return 'Financial Services', 'Broad Market ETF'
        
        # IWM - iShares Russell 2000 ETF
        if 'iwm' in symbol.lower() or 'russell 2000' in short_name or 'russell 2000' in long_name:
            return 'Financial Services', 'Small Cap ETF'
        
        # MTUM - iShares MSCI USA Momentum Factor ETF
        if 'mtum' in symbol.lower() or 'momentum' in short_name or 'momentum' in long_name:
            return 'Financial Services', 'Factor ETF'
        
        # VLUE - iShares MSCI USA Value Factor ETF
        if 'vlue' in symbol.lower() or 'value' in short_name or 'value' in long_name:
            return 'Financial Services', 'Factor ETF'
        
        # QUAL - iShares MSCI USA Quality Factor ETF
        if 'qual' in symbol.lower() or 'quality' in short_name or 'quality' in long_name:
            return 'Financial Services', 'Factor ETF'
        
        # Generic ETF mapping based on business summary
        if 'etf' in short_name or 'etf' in long_name:
            if 'treasury' in business_summary or 'bond' in business_summary:
                return 'Financial Services', 'Government Bonds'
            elif 'technology' in business_summary or 'nasdaq' in business_summary:
                return 'Technology', 'Technology ETF'
            elif 's&p' in business_summary or '500' in business_summary:
                return 'Financial Services', 'Broad Market ETF'
            elif 'russell' in business_summary or 'small' in business_summary:
                return 'Financial Services', 'Small Cap ETF'
            elif 'momentum' in business_summary or 'factor' in business_summary:
                return 'Financial Services', 'Factor ETF'
            else:
                return 'Financial Services', 'ETF'
        
        return 'Unknown', 'Unknown'
    
    def _get_market_cap_external(self, symbol: str) -> Optional[float]:
        """Get market cap from external API using yfinance"""
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            market_cap = info.get('marketCap')
            if market_cap:
                print(f"yfinance market cap for {symbol}: {market_cap}")
                return float(market_cap)
            else:
                print(f"⚠️ No market cap data for {symbol} in yfinance")
                
        except Exception as e:
            print(f"⚠️ Could not get market cap for {symbol} with yfinance: {e}")
        return None

    def get_contract_details(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get contract details for a symbol"""
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
            
            req_id = random.randint(1000, 2000)
            self.connection.data[req_id] = []
            self.connection.reqContractDetails(req_id, contract)
            
            # Wait for contract details
            start_time = time.time()
            while (time.time() - start_time) < 10:
                if req_id in self.connection.data and self.connection.data[req_id]:
                    try:
                        contract_details = self.connection.data[req_id][0]
                        industry = getattr(contract_details, 'industry', None)
                        category = getattr(contract_details, 'category', None)
                        
                        # Try to get market cap from external API
                        market_cap = self._get_market_cap_external(symbol)
                        
                        result = {
                            "industry": industry or "Unknown",
                            "sector": category or "Unknown", 
                            "market_cap": market_cap,
                            "company_name": symbol
                        }
                        print(f"Contract details for {symbol}: {result}")
                        return result
                    except (IndexError, AttributeError) as e:
                        print(f"⚠️ Contract details parsing error for {symbol}: {e}")
                        break
                time.sleep(0.1)
            
            print(f"❌ Timeout getting contract details for {symbol}")
            return None
            
        except Exception as e:
            print(f"❌ Error getting contract details for {symbol}: {e}")
            return None

    def get_historical_data(self, symbol: str, duration: str = "9 Y", 
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
            
            # Generate unique request ID
            req_id = len(self.connection.historical_data) + 100
            
            # Request historical data
            self.connection.reqHistoricalData(req_id, contract, "", duration, bar_size, "TRADES", 1, 1, False, [])
            print(f"Requested historical data for {symbol} with reqId: {req_id}")
            
            # Wait for data
            start_time = time.time()
            while (time.time() - start_time) < 30:  # 30 second timeout
                if req_id in self.connection.historical_data:
                    data = self.connection.historical_data.pop(req_id)
                    print(f"Historical data received for {symbol}: {len(data)} bars")
                    return data
                time.sleep(0.1)
            
            print(f"❌ Timeout getting historical data for {symbol}")
            return None
            
        except Exception as e:
            print(f"❌ Error getting historical data for {symbol}: {e}")
            return None

    def get_bid_ask_spread(self, symbol: str, timeout: int = 15) -> Optional[Dict[str, Any]]:
        """Get current bid/ask spread for a symbol"""
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
            
            # Generate unique request ID
            req_id = len(self.connection.bid_ask_data) + 1000  # Use 1000+ for market data
            
            # Store request info
            self.connection.market_data_requests[req_id] = {
                'symbol': symbol,
                'error': False,
                'start_time': time.time()
            }
            
            # Request market data
            self.connection.reqMktData(req_id, contract, "", False, False, [])
            print(f"Requested market data for {symbol} with reqId: {req_id}")
            
            # Wait for data with longer timeout for delayed data
            start_time = time.time()
            while (time.time() - start_time) < timeout:
                if req_id in self.connection.bid_ask_data:
                    data = self.connection.bid_ask_data[req_id]
                    # Check if we have at least one price (bid or ask)
                    if data.get('bid') is not None or data.get('ask') is not None:
                        # Cancel the market data request
                        self.connection.cancelMktData(req_id)
                        
                        # If we only have one price, use it for both bid and ask
                        bid = data.get('bid')
                        ask = data.get('ask')
                        if bid is None and ask is not None:
                            bid = ask  # Use ask as bid
                        elif ask is None and bid is not None:
                            ask = bid  # Use bid as ask
                        elif bid is None and ask is None:
                            print(f"No price data received for {symbol}")
                            return None
                        
                        spread_pct = ((ask - bid) / ((ask + bid) / 2)) * 100 if ask != bid else 0.0
                        
                        return {
                            'symbol': symbol,
                            'bid': bid,
                            'ask': ask,
                            'spread_pct': spread_pct,
                            'volume': data.get('volume', 0),
                            'timestamp': datetime.now()
                        }
                
                # Check for errors
                if req_id in self.connection.market_data_requests:
                    if self.connection.market_data_requests[req_id].get('error'):
                        print(f"Market data error for {symbol}")
                        self.connection.cancelMktData(req_id)
                        return None
                
                time.sleep(0.1)
            
            # Timeout - cancel request
            self.connection.cancelMktData(req_id)
            print(f"Timeout getting bid/ask for {symbol} (no data received)")
            return None
            
        except Exception as e:
            print(f"Error getting bid/ask for {symbol}: {e}")
            return None
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        1️⃣ spróbuj IBKR (snapshot)
        2️⃣ jeżeli brak subskrypcji / błąd → yfinance
        """
        if not self.connection or not self.connection.connected:
            self.connect(timeout=10)

        try:
            # -- IBKR snapshot ----------------------------
            contract = Contract()
            contract.symbol   = symbol
            contract.secType  = "STK"
            contract.exchange = "SMART"
            contract.currency = "USD"

            req_id = random.randint(10000, 20000)
            self.connection.reqMarketDataType(4)          # 1=live,4=delayed
            self.connection.reqMktData(req_id, contract, "", False, False, [])

            start = time.time()
            while time.time() - start < 5:                # max 5 s
                tick = self.connection.bid_ask_data.get(req_id)
                if tick and tick.get("bid") and tick.get("ask"):
                    self.connection.cancelMktData(req_id)
                    return (tick["bid"] + tick["ask"]) / 2
                time.sleep(0.05)
            self.connection.cancelMktData(req_id)
        except Exception as e:
            print("⚠️ IBKR snapshot failed:", e)

        # -- fallback: yfinance --------------------------
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            price = ticker.info.get("regularMarketPrice")
            if price:
                print(f"yfinance price for {symbol}: ${price}")
                return price
            else:
                print(f"⚠️ No price data for {symbol} in yfinance")
        except Exception as e:
            print(f"⚠️ yfinance failed for {symbol}: {e}")
        return None
    
    def disconnect(self):
        """Disconnect from IBKR"""
        if self.connection:
            self.connection.disconnect()
            if hasattr(self, "_thread") and self._thread.is_alive():
                self._thread.join(timeout=2)  # porządek przy zamykaniu 