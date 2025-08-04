#!/usr/bin/env python3
"""
Script to update BULL historical data with realistic high volatility
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from database.database import SessionLocal
from database.models.ticker import Ticker
from database.models.historical_data import HistoricalData
from datetime import datetime, timedelta
import numpy as np
import random

def update_bull_historical_data():
    """Update BULL historical data with realistic high volatility"""
    db = SessionLocal()
    
    try:
        # Get BULL ticker
        bull_ticker = db.query(Ticker).filter(Ticker.symbol == 'BULL').first()
        if not bull_ticker:
            print("❌ BULL ticker not found")
            return
        
        print(f"📊 Updating BULL historical data...")
        
        # Delete existing historical data for BULL
        db.query(HistoricalData).filter(HistoricalData.ticker_id == bull_ticker.id).delete()
        db.commit()
        print("✅ Deleted old historical data")
        
        # Generate new historical data with high volatility (like a 2x leveraged ETF)
        current_price = 190.0  # Current price
        high_volatility = 0.08  # 8% daily volatility (very high for leveraged ETF)
        
        data_points = []
        for i in range(252):  # 1 year of trading days
            date = datetime.now() - timedelta(days=252-i)
            
            # Generate price with high volatility
            daily_return = np.random.normal(0, high_volatility)
            current_price *= (1 + daily_return)
            
            # Generate OHLC
            open_price = current_price * (1 + np.random.normal(0, 0.02))
            high_price = max(open_price, current_price) * (1 + abs(np.random.normal(0, 0.03)))
            low_price = min(open_price, current_price) * (1 - abs(np.random.normal(0, 0.03)))
            close_price = current_price
            
            volume = int(np.random.normal(2000000, 1000000))
            
            data_points.append({
                'ticker_id': bull_ticker.id,
                'date': date.date(),
                'open_price': round(open_price, 2),
                'close_price': round(close_price, 2),
                'high_price': round(high_price, 2),
                'low_price': round(low_price, 2),
                'volume': max(volume, 500000)
            })
        
        # Insert new historical data
        for data_point in data_points:
            hist_record = HistoricalData(**data_point)
            db.add(hist_record)
        
        db.commit()
        print(f"✅ Added {len(data_points)} new historical records for BULL")
        
        # Update current price
        bull_ticker.last_price = 190.0
        db.commit()
        print("✅ Updated BULL current price to $190.00")
        
    except Exception as e:
        print(f"❌ Error updating BULL data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("=== BULL Historical Data Updater ===")
    update_bull_historical_data()
    print("✅ Done!") 