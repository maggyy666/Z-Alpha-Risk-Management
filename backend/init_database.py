#!/usr/bin/env python3
"""
Initialize database with admin user and portfolio
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from database.database import engine, SessionLocal, Base
from database.models.user import User
from database.models.portfolio import Portfolio
from database.models.ticker_data import TickerData
from sqlalchemy import Index

def init_database():
    """Initialize database with tables and admin user"""
    print("🗄️  Initializing database...")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create composite index for ticker_data
    Index('idx_ticker_data_symbol_date', TickerData.ticker_symbol, TickerData.date)
    
    db = SessionLocal()
    
    try:
        # Check if admin user exists
        admin_user = db.query(User).filter(User.username == "admin").first()
        
        if not admin_user:
            print("👤 Creating admin user...")
            admin_user = User(
                username="admin",
                password="admin",  # In production, this should be hashed
                email="admin@example.com"
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            print("✅ Admin user created")
        else:
            print("✅ Admin user already exists")
        
        # Define portfolio tickers
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
        
        # Show portfolio
        portfolio_items = db.query(Portfolio).filter(Portfolio.user_id == admin_user.id).all()
        print(f"📊 Admin portfolio: {len(portfolio_items)} tickers")
        for item in portfolio_items:
            print(f"   {item.ticker_symbol}: {item.shares} shares")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_database()
    print("✅ Database initialization complete!") 