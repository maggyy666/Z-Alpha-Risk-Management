#!/usr/bin/env python3
"""
Script to inject sample portfolio data into SQLite database
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from database.database import SessionLocal, engine, Base
from database.models.ticker import Ticker
from database.models.historical_data import HistoricalData
from datetime import datetime, timedelta
import numpy as np
import random

# Sample portfolio data
SAMPLE_PORTFOLIO = [
    {'symbol': 'AMD', 'company_name': 'Advanced Micro Devices', 'sector': 'Technology', 'market_cap': 200000000000, 'last_price': 162.12, 'volatility': 29.22},
    {'symbol': 'APP', 'company_name': 'AppLovin Corp', 'sector': 'Technology', 'market_cap': 32000000000, 'last_price': 45.67, 'volatility': 35.45},
    {'symbol': 'BRK-B', 'company_name': 'Berkshire Hathaway', 'sector': 'Financial Services', 'market_cap': 800000000000, 'last_price': 350.25, 'volatility': 18.33},
    {'symbol': 'BULL', 'company_name': 'Direxion Daily S&P 500 Bull 2X', 'sector': 'ETF', 'market_cap': 73400000000, 'last_price': 73.40, 'volatility': 45.67},
    {'symbol': 'DOMO', 'company_name': 'Domo Inc', 'sector': 'Technology', 'market_cap': 453000000, 'last_price': 4.53, 'volatility': 42.18},
    {'symbol': 'GOOGL', 'company_name': 'Alphabet Inc', 'sector': 'Communication Services', 'market_cap': 1800000000000, 'last_price': 156.28, 'volatility': 25.67},
    {'symbol': 'META', 'company_name': 'Meta Platforms', 'sector': 'Communication Services', 'market_cap': 270000000000, 'last_price': 135.04, 'volatility': 28.91},
    {'symbol': 'QQQM', 'company_name': 'Invesco NASDAQ 100 ETF', 'sector': 'ETF', 'market_cap': 45000000000, 'last_price': 156.28, 'volatility': 22.45},
    {'symbol': 'RDDT', 'company_name': 'Reddit Inc', 'sector': 'Communication Services', 'market_cap': 2349000000000, 'last_price': 22.45, 'volatility': 38.92},
    {'symbol': 'SGOV', 'company_name': 'iShares 0-3 Month Treasury Bond ETF', 'sector': 'ETF', 'market_cap': 15000000000, 'last_price': 100.15, 'volatility': 8.00},
    {'symbol': 'SMCI', 'company_name': 'Super Micro Computer', 'sector': 'Technology', 'market_cap': 1021000000000, 'last_price': 1021.50, 'volatility': 52.34},
    {'symbol': 'SNOW', 'company_name': 'Snowflake Inc', 'sector': 'Technology', 'market_cap': 123000000000, 'last_price': 123.27, 'volatility': 41.23},
    {'symbol': 'TSLA', 'company_name': 'Tesla Inc', 'sector': 'Consumer Cyclical', 'market_cap': 106000000000, 'last_price': 106.44, 'volatility': 48.76},
    {'symbol': 'ULTY', 'company_name': 'Unity Software Inc', 'sector': 'Communication Services', 'market_cap': 27700000000, 'last_price': 6.26, 'volatility': 12.68}
]

def generate_historical_data(ticker_id: int, base_price: float, volatility: float, days: int = 252) -> list:
    """Generate sample historical data"""
    data = []
    current_price = base_price
    
    for i in range(days):
        date = datetime.now() - timedelta(days=days-i)
        
        # Generate price movement
        daily_return = np.random.normal(0, volatility/100/np.sqrt(252))
        current_price *= (1 + daily_return)
        
        # Generate OHLC
        open_price = current_price * (1 + np.random.normal(0, 0.01))
        high_price = max(open_price, current_price) * (1 + abs(np.random.normal(0, 0.02)))
        low_price = min(open_price, current_price) * (1 - abs(np.random.normal(0, 0.02)))
        close_price = current_price
        
        volume = int(np.random.normal(1000000, 500000))
        
        data.append({
            'ticker_id': ticker_id,
            'date': date.date(),
            'open_price': round(open_price, 2),
            'close_price': round(close_price, 2),
            'high_price': round(high_price, 2),
            'low_price': round(low_price, 2),
            'volume': max(volume, 100000)
        })
    
    return data

def inject_sample_data():
    """Inject sample data into database"""
    db = SessionLocal()
    
    try:
        print("🗄️  Injecting sample portfolio data...")
        
        # Create tickers
        tickers = []
        for item in SAMPLE_PORTFOLIO:
            ticker = Ticker(
                symbol=item['symbol'],
                company_name=item['company_name'],
                sector=item['sector'],
                market_cap=item['market_cap'],
                last_price=item['last_price'],
                volume=random.randint(1000000, 10000000)
            )
            db.add(ticker)
            tickers.append(ticker)
        
        db.commit()
        print(f"✅ Created {len(tickers)} tickers")
        
        # Generate historical data for each ticker
        for ticker in tickers:
            print(f"📊 Generating historical data for {ticker.symbol}...")
            
            # Find volatility for this ticker
            volatility = next(item['volatility'] for item in SAMPLE_PORTFOLIO if item['symbol'] == ticker.symbol)
            
            # Generate historical data
            historical_data = generate_historical_data(ticker.id, ticker.last_price, volatility)
            
            # Insert historical data
            for data_point in historical_data:
                hist_record = HistoricalData(**data_point)
                db.add(hist_record)
            
            db.commit()
            print(f"✅ Added {len(historical_data)} historical records for {ticker.symbol}")
        
        print("\n🎉 Sample data injection completed!")
        print(f"📈 Total tickers: {len(tickers)}")
        print(f"📊 Total historical records: {len(tickers) * 252}")
        
    except Exception as e:
        print(f"❌ Error injecting data: {e}")
        db.rollback()
    finally:
        db.close()

def show_database_stats():
    """Show database statistics"""
    db = SessionLocal()
    
    try:
        ticker_count = db.query(Ticker).count()
        historical_count = db.query(HistoricalData).count()
        
        print("\n📊 Database Statistics:")
        print(f"   Tickers: {ticker_count}")
        print(f"   Historical records: {historical_count}")
        
        if ticker_count > 0:
            print("\n📈 Sample tickers:")
            tickers = db.query(Ticker).limit(5).all()
            for ticker in tickers:
                print(f"   {ticker.symbol}: ${ticker.last_price:.2f} ({ticker.sector})")
        
    except Exception as e:
        print(f"❌ Error reading database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("=== IBKR Portfolio Sample Data Injector ===")
    
    # Inject sample data
    inject_sample_data()
    
    # Show statistics
    show_database_stats()
    
    print("\n✅ Done! You can now test the application with sample data.") 