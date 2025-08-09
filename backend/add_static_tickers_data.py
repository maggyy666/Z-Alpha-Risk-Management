#!/usr/bin/env python3
"""
Add sample data for static tickers (SPY, MTUM, IWM, VLUE, QUAL)
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from database.database import SessionLocal
from database.models.ticker_data import TickerData
from services.data_service import DataService

def add_static_tickers_data():
    """Add sample data for static tickers"""
    print("Adding sample data for static tickers...")
    
    data_service = DataService()
    db = SessionLocal()
    
    try:
        static_tickers = data_service.get_static_tickers()
        print(f"Static tickers: {static_tickers}")
        
        for ticker in static_tickers:
            print(f"🔍 Processing {ticker}...")
            
            # Check if data already exists
            existing_count = db.query(TickerData).filter(TickerData.ticker_symbol == ticker).count()
            if existing_count > 0:
                print(f"✅ {ticker}: Already has {existing_count} records")
                continue
            
            # Add sample data
            success = data_service.inject_sample_data(db, ticker)
            if success:
                print(f"✅ Added sample data for {ticker}")
            else:
                print(f"Failed to add sample data for {ticker}")
        
        print("✅ Static tickers data added!")
        
    except Exception as e:
        print(f"Error adding static tickers data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    add_static_tickers_data() 