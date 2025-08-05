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
        
        # Create admin user
        from database.models.user import User
        from database.models.portfolio import Portfolio
        
        # Check if admin user exists
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            admin_user = User(username="admin", password="admin", email="admin@example.com")
            db.add(admin_user)
            db.commit()
            print("✅ Created admin user")
        
        # Add tickers to admin's portfolio
        for symbol in PORTFOLIO_SYMBOLS:
            # Check if portfolio item already exists
            existing = db.query(Portfolio).filter(
                Portfolio.user_id == admin_user.id,
                Portfolio.ticker_symbol == symbol
            ).first()
            
            if not existing:
                portfolio_item = Portfolio(
                    user_id=admin_user.id,
                    ticker_symbol=symbol,
                    shares=1000
                )
                db.add(portfolio_item)
                print(f"✅ Added {symbol} to admin portfolio")
        
        db.commit()
        print(f"✅ Initialized {len(PORTFOLIO_SYMBOLS)} tickers in admin portfolio")
        
        # Generate sample data for each ticker
        print("\nGenerating sample historical data...")
        for symbol in PORTFOLIO_SYMBOLS:
            print(f"Generating data for {symbol}...")
            success = data_service.inject_sample_data(db, symbol)
            if success:
                print(f"✅ Successfully generated data for {symbol}")
            else:
                print(f"❌ Failed to generate data for {symbol}")
        
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
        portfolio_data = data_service.get_portfolio_volatility_data(db, "admin")
        
        for item in portfolio_data:
            print(f"{item['symbol']}: Volatility={item['forecast_volatility_pct']:.2f}%, "
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