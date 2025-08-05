#!/usr/bin/env python3
"""
Complete database setup script
Creates database, user, portfolio, and generates all historical data
"""

import sys
import os
import time
import requests
import json
sys.path.append(os.path.dirname(__file__))

from database.database import engine, SessionLocal, Base
from database.models.user import User
from database.models.portfolio import Portfolio
from database.models.ticker_data import TickerData
from services.data_service import DataService
from sqlalchemy import Index

def setup_database():
    """Complete database setup"""
    print("🚀 Starting complete database setup...")
    
    # 0. Remove old database if exists
    print("\n🗑️  Step 0: Removing old database...")
    import os
    db_path = "portfolio.db"
    if os.path.exists(db_path):
        os.remove(db_path)
        print("✅ Old database removed")
    else:
        print("✅ No old database found")
    
    # 1. Create all tables
    print("\n📊 Step 1: Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    # Create composite index for ticker_data
    Index('idx_ticker_data_symbol_date', TickerData.ticker_symbol, TickerData.date)
    print("✅ Database tables created")
    
    db = SessionLocal()
    data_service = DataService()
    
    try:
        # 2. Create admin user
        print("\n👤 Step 2: Creating admin user...")
        admin_user = db.query(User).filter(User.username == "admin").first()
        
        if not admin_user:
            admin_user = User(
                username="admin",
                password="admin",
                email="admin@example.com"
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            print("✅ Admin user created")
        else:
            print("✅ Admin user already exists")
        
        # 3. Define portfolio tickers
        print("\n📈 Step 3: Setting up portfolio...")
        portfolio_tickers = [
            "AMD", "APP", "BRK-B", "BULL", "DOMO", "GOOGL", 
            "META", "QQQM", "RDDT", "SGOV", "SMCI", "SNOW", 
            "TSLA", "ULTY"
        ]
        
        # Add tickers to admin's portfolio
        for ticker in portfolio_tickers:
            existing = db.query(Portfolio).filter(
                Portfolio.user_id == admin_user.id,
                Portfolio.ticker_symbol == ticker
            ).first()
            
            if not existing:
                portfolio_item = Portfolio(
                    user_id=admin_user.id,
                    ticker_symbol=ticker,
                    shares=1000
                )
                db.add(portfolio_item)
                print(f"📈 Added {ticker} to admin portfolio")
        
        db.commit()
        print("✅ Portfolio initialized")
        
        # 4. Generate historical data for portfolio tickers
        print("\n📊 Step 4: Generating historical data for portfolio tickers...")
        for ticker in portfolio_tickers:
            existing_count = db.query(TickerData).filter(TickerData.ticker_symbol == ticker).count()
            if existing_count == 0:
                success = data_service.inject_sample_data(db, ticker)
                if success:
                    print(f"✅ Generated data for {ticker}")
                else:
                    print(f"❌ Failed to generate data for {ticker}")
            else:
                print(f"✅ {ticker}: Already has {existing_count} records")
        
        # 5. Generate historical data for static tickers
        print("\n📊 Step 5: Generating historical data for static tickers...")
        static_tickers = data_service.get_static_tickers()
        for ticker in static_tickers:
            existing_count = db.query(TickerData).filter(TickerData.ticker_symbol == ticker).count()
            if existing_count == 0:
                success = data_service.inject_sample_data(db, ticker)
                if success:
                    print(f"✅ Generated data for {ticker}")
                else:
                    print(f"❌ Failed to generate data for {ticker}")
            else:
                print(f"✅ {ticker}: Already has {existing_count} records")
        
        print("\n✅ All historical data generated!")
        
        # 6. Show summary
        print("\n📊 Step 6: Database summary...")
        total_tickers = db.query(TickerData.ticker_symbol).distinct().count()
        total_records = db.query(TickerData).count()
        portfolio_count = db.query(Portfolio).filter(Portfolio.user_id == admin_user.id).count()
        
        print(f"📈 Total tickers: {total_tickers}")
        print(f"📊 Total records: {total_records}")
        print(f"💼 Portfolio items: {portfolio_count}")
        
        # Show date range
        date_range = db.query(TickerData.date).distinct().order_by(TickerData.date).all()
        if date_range:
            min_date = date_range[0][0]
            max_date = date_range[-1][0]
            print(f"📅 Date range: {min_date} to {max_date}")
        
    except Exception as e:
        print(f"❌ Error during setup: {e}")
        db.rollback()
    finally:
        db.close()

def check_backend():
    """Check if backend is running and healthy"""
    print("\n🔍 Step 7: Checking backend health...")
    
    try:
        # Check if backend is running
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running")
        else:
            print("❌ Backend is not responding properly")
            return False
    except requests.exceptions.RequestException:
        print("❌ Backend is not running. Please start it with: poetry run python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000")
        return False
    
    return True

def test_endpoints():
    """Test all endpoints"""
    print("\n🧪 Step 8: Testing endpoints...")
    
    endpoints = [
        ("/concentration-risk-data?username=admin", "Concentration Risk"),
        ("/factor-exposure-data?username=admin", "Factor Exposure"),
        ("/volatility-data?username=admin", "Volatility Data"),
        ("/risk-scoring?username=admin", "Risk Scoring"),
        ("/stress-testing?username=admin", "Stress Testing"),
    ]
    
    for endpoint, name in endpoints:
        try:
            print(f"🔍 Testing {name}...")
            response = requests.get(f"http://localhost:8000{endpoint}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "error" in data:
                    print(f"❌ {name}: {data['error']}")
                else:
                    print(f"✅ {name}: OK")
            else:
                print(f"❌ {name}: HTTP {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {name}: Connection error - {e}")
        except json.JSONDecodeError:
            print(f"❌ {name}: Invalid JSON response")

def main():
    """Main setup function"""
    print("=" * 60)
    print("🚀 Z-ALPHA SECURITIES - DATABASE SETUP")
    print("=" * 60)
    
    # Setup database
    setup_database()
    
    # Check backend
    if check_backend():
        # Test endpoints
        test_endpoints()
    
    print("\n" + "=" * 60)
    print("✅ SETUP COMPLETE!")
    print("=" * 60)
    print("\n📋 Next steps:")
    print("1. Start backend: poetry run python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000")
    print("2. Start frontend: cd ../frontend && npm start")
    print("3. Open browser: http://localhost:3000")
    print("\n🎉 Enjoy your Z-Alpha Securities Dashboard!")

if __name__ == "__main__":
    main() 