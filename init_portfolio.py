#!/usr/bin/env python3
"""
Script to initialize portfolio data and fetch historical data from IBKR
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from database.database import SessionLocal, engine, Base
from services.data_service import DataService
from database.models.ticker import Ticker
from database.models.historical_data import HistoricalData

# Portfolio symbols
PORTFOLIO_SYMBOLS = [
    'AMD', 'APP', 'BRK-B', 'BULL', 'DOMO', 'GOOGL', 'META', 
    'QQQM', 'RDDT', 'SGOV', 'SMCI', 'SNOW', 'TSLA', 'ULTY'
]

def init_database():
    """Initialize database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

def init_portfolio():
    """Initialize portfolio tickers"""
    db = SessionLocal()
    data_service = DataService()
    
    try:
        print("Initializing portfolio tickers...")
        tickers = data_service.initialize_tickers(db, PORTFOLIO_SYMBOLS)
        print(f"Initialized {len(tickers)} tickers: {[t.symbol for t in tickers]}")
        
        # Fetch historical data for each ticker
        print("\nFetching historical data from IBKR...")
        for symbol in PORTFOLIO_SYMBOLS:
            print(f"Fetching data for {symbol}...")
            success = data_service.fetch_and_store_historical_data(db, symbol)
            if success:
                print(f"✅ Successfully fetched data for {symbol}")
            else:
                print(f"❌ Failed to fetch data for {symbol}")
        
        print("\nPortfolio initialization completed!")
        
    except Exception as e:
        print(f"Error during initialization: {e}")
    finally:
        db.close()

def show_portfolio_data():
    """Show current portfolio data"""
    db = SessionLocal()
    data_service = DataService()
    
    try:
        print("\nCurrent portfolio volatility data:")
        portfolio_data = data_service.get_portfolio_volatility_data(db, PORTFOLIO_SYMBOLS)
        
        for item in portfolio_data:
            print(f"{item['symbol']}: Volatility={item['forecast_volatility']:.2f}%, "
                  f"Price=${item['last_price']:.2f}, Sharpe={item['sharpe_ratio']:.2f}")
        
    except Exception as e:
        print(f"Error showing portfolio data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("=== IBKR Portfolio Initialization ===")
    
    # Initialize database
    init_database()
    
    # Initialize portfolio
    init_portfolio()
    
    # Show results
    show_portfolio_data()
    
    print("\n=== Initialization Complete ===") 