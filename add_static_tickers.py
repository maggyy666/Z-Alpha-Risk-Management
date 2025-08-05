#!/usr/bin/env python3
"""
Script to add static tickers (like SPY) to the database
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from database.database import SessionLocal, engine, Base
from services.data_service import DataService

# Static tickers to add
STATIC_TICKERS = ['SPY']

def add_static_tickers():
    """Add static tickers to database"""
    db = SessionLocal()
    data_service = DataService()
    
    try:
        print("=== Adding Static Tickers ===")
        
        for symbol in STATIC_TICKERS:
            print(f"Processing {symbol}...")
            
            # Check if data already exists
            existing_data = db.query(TickerData).filter(TickerData.ticker_symbol == symbol).first()
            if existing_data:
                print(f"✅ {symbol} already has data in database")
                continue
            
            # Generate sample data for static ticker
            print(f"Generating sample data for {symbol}...")
            success = data_service.inject_sample_data(db, symbol)
            if success:
                print(f"✅ Successfully generated data for {symbol}")
            else:
                print(f"❌ Failed to generate data for {symbol}")
        
        print("\n=== Static Tickers Added ===")
        
    except Exception as e:
        print(f"Error adding static tickers: {e}")
    finally:
        db.close()

def show_static_tickers_data():
    """Show data for static tickers"""
    db = SessionLocal()
    data_service = DataService()
    
    try:
        print("\n=== Static Tickers Data ===")
        
        for symbol in STATIC_TICKERS:
            print(f"\n{symbol} metrics:")
            metrics = data_service.calculate_volatility_metrics(db, symbol)
            if metrics:
                print(f"  Volatility: {metrics.get('volatility', 0):.2f}%")
                print(f"  Last Price: ${metrics.get('last_price', 0):.2f}")
                print(f"  Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}")
            else:
                print(f"  ❌ No data available")
        
    except Exception as e:
        print(f"Error showing static tickers data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    # Import here to avoid circular imports
    from database.models.ticker_data import TickerData
    
    add_static_tickers()
    show_static_tickers_data() 