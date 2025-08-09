#!/usr/bin/env python3
"""
Complete database setup for remaining tickers
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from database.database import SessionLocal
from database.models.portfolio import Portfolio
from database.models.ticker_data import TickerData
from services.data_service import DataService

def complete_setup():
    """Complete setup for remaining tickers"""
    print("=" * 60)
    print("COMPLETING DATABASE SETUP")
    print("=" * 60)
    
    db = SessionLocal()
    data_service = DataService()
    
    try:
        # Get all portfolio tickers
        portfolio_items = db.query(Portfolio).all()
        tickers = [item.ticker_symbol for item in portfolio_items]
        
        print(f"Portfolio tickers: {tickers}")
        
        # Check which tickers already have data
        tickers_with_data = set()
        for ticker in tickers:
            count = db.query(TickerData).filter(TickerData.ticker_symbol == ticker).count()
            if count > 0:
                tickers_with_data.add(ticker)
                print(f"{ticker}: {count} records")
            else:
                print(f"{ticker}: No data")
        
        # Get tickers without data
        tickers_needing_data = [t for t in tickers if t not in tickers_with_data]
        print(f"\nTickers needing data: {tickers_needing_data}")
        
        # Handle special symbols
        symbol_mapping = {
            'BULL': 'BULL',    # ETF
            'QQQM': 'QQQM',    # ETF
            'SGOV': 'SGOV',    # ETF
            'ULTY': 'ULTY'     # ETF
        }
        
        # Fetch data for remaining tickers
        for ticker in tickers_needing_data:
            print(f"\n🔍 Processing {ticker}...")
            
            # Use mapped symbol if available
            ibkr_symbol = symbol_mapping.get(ticker, ticker)
            
            try:
                success = data_service.fetch_and_store_historical_data(db, ibkr_symbol)
                if success:
                    count = db.query(TickerData).filter(TickerData.ticker_symbol == ibkr_symbol).count()
                    print(f"{ticker}: Added {count} records")
                else:
                    print(f"{ticker}: Failed to fetch data")
            except Exception as e:
                print(f"{ticker}: Error - {e}")
                continue
        
        # Show final summary
        print(f"\n" + "=" * 60)
        print("FINAL SUMMARY")
        print("=" * 60)
        
        for ticker in tickers:
            count = db.query(TickerData).filter(TickerData.ticker_symbol == ticker).count()
            if count > 0:
                latest = db.query(TickerData).filter(TickerData.ticker_symbol == ticker).order_by(TickerData.date.desc()).first()
                print(f"{ticker}: {count} records, latest: {latest.date} @ ${latest.close_price}")
            else:
                print(f"{ticker}: No data")
        
        print(f"\n Setup completed!")
        
    except Exception as e:
        print(f"Error in complete_setup: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    complete_setup()
