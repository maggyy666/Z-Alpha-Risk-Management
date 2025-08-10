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
import sqlite3
from pathlib import Path
from typing import List
sys.path.append(os.path.dirname(__file__))

from database.database import engine, SessionLocal, Base
from database.models.user import User
from database.models.portfolio import Portfolio
from database.models.ticker_data import TickerData
from database.models.ticker import TickerInfo
from services.data_service import DataService
from sqlalchemy import Index, inspect, text

def check_required_modules():
    """Check if all required modules can be imported"""
    print("Checking required modules...")
    
    required_modules = [
        'sqlalchemy',
        'requests',
        'numpy',
        'pandas'
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print(f"Missing required modules: {missing_modules}")
        print("Please install them with: pip install " + " ".join(missing_modules))
        return False
    
    print("All required modules found")
    return True

def check_database_connection():
    """Check if database can be created and accessed"""
    print("Checking database connection...")
    
    try:
        # Test SQLite connection
        db_path = "portfolio.db"
        conn = sqlite3.connect(db_path)
        conn.close()
        print("Database connection test successful")
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

def check_file_permissions():
    """Check if we have write permissions in current directory"""
    print("Checking file permissions...")
    
    try:
        test_file = "test_write_permission.tmp"
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        print("Write permissions OK")
        return True
    except Exception as e:
        print(f"Write permission check failed: {e}")
        return False

def remove_old_database():
    """Remove old database if exists"""
    print("Removing old database...")
    
    try:
        db_path = "portfolio.db"
        if os.path.exists(db_path):
            os.remove(db_path)
            print("Old database removed successfully")
        else:
            print("No old database found")
        return True
    except Exception as e:
        print(f"Error removing old database: {e}")
        return False

def create_database_tables():
    """Create all database tables"""
    print("Creating database tables...")
    
    try:
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully")
        return True
    except Exception as e:
        print(f"Error creating database tables: {e}")
        return False

def migrate_database_schema():
    """Migrate database schema if needed"""
    print("Checking database schema...")
    
    try:
        # Schema migration is handled by SQLAlchemy models
        print("Database schema is up to date")
        return True
    except Exception as e:
        print(f"Error migrating database schema: {e}")
        return False

def create_admin_user(db):
    """Create admin user"""
    print("Creating admin user...")
    
    try:
        # Check if admin user already exists
        admin_user = db.query(User).filter(User.username == "admin").first()
        if admin_user:
            print("Admin user already exists")
            return admin_user
        
        # Create new admin user
        admin_user = User(
            username="admin",
            password="admin123",  # In production, this should be hashed
            email="admin@zalpha.com"
        )
        db.add(admin_user)
        db.commit()
        print("Admin user created successfully")
        return admin_user
        
    except Exception as e:
        print(f"Error creating admin user: {e}")
        db.rollback()
        return None

def get_default_portfolio(username: str) -> List[str]:
    """Get default portfolio for a user from JSON file"""
    # Handle both cases: running from project root or from backend/
    portfolio_file = f"../data/{username}_portfolio.json"
    if not os.path.exists(portfolio_file):
        portfolio_file = f"data/{username}_portfolio.json"
    
    try:
        if not os.path.exists(portfolio_file):
            print(f"Portfolio file {portfolio_file} not found")
            return []
        
        with open(portfolio_file, 'r') as f:
            portfolio_data = json.load(f)
        
        if not isinstance(portfolio_data, list):
            print(f"Invalid portfolio format: expected list of ticker objects")
            return []
        
        # Extract just ticker symbols for backward compatibility
        tickers = [item.get('ticker') for item in portfolio_data if 'ticker' in item]
        return tickers
        
    except Exception as e:
        print(f"Error reading portfolio file for {username}: {e}")
        return []

def import_portfolio_from_file(db, user, portfolio_file: str):
    """Import portfolio from JSON file"""
    try:
        if not os.path.exists(portfolio_file):
            print(f"Portfolio file {portfolio_file} not found")
            return False
        
        with open(portfolio_file, 'r') as f:
            portfolio_data = json.load(f)
        
        if not isinstance(portfolio_data, list):
            print(f"Invalid portfolio format: expected list of ticker objects")
            return False
        
        added_count = 0
        for item in portfolio_data:
            if 'ticker' not in item or 'shares' not in item:
                print(f"Invalid portfolio item: missing ticker or shares")
                continue
            
            ticker = item['ticker']
            shares = int(item['shares'])
            
            existing = db.query(Portfolio).filter(
                Portfolio.user_id == user.id,
                Portfolio.ticker_symbol == ticker
            ).first()
            
            if not existing:
                portfolio_item = Portfolio(
                    user_id=user.id,
                    ticker_symbol=ticker,
                    shares=shares
                )
                db.add(portfolio_item)
                added_count += 1
        
        db.commit()
        print(f"Imported portfolio for {user.username} with {added_count} tickers from {portfolio_file}")
        return True
    except Exception as e:
        print(f"Error importing portfolio for {user.username}: {e}")
        db.rollback()
        return False

def setup_portfolio(db, user, use_file_data=False):
    """Setup portfolio for user from JSON file"""
    print(f"Setting up portfolio for {user.username}...")
    
    # Always use portfolio file (JSON-based approach)
    # Handle both cases: running from project root or from backend/
    portfolio_file = f"../data/{user.username}_portfolio.json"
    if not os.path.exists(portfolio_file):
        portfolio_file = f"data/{user.username}_portfolio.json"
    return import_portfolio_from_file(db, user, portfolio_file)

def generate_ticker_data(db, ticker, start_date, end_date, use_file_data=False):
    """Fetch real historical data from IBKR for a ticker, or import from file if IBKR unavailable"""
    data_service = DataService()
    
    if use_file_data:
        print(f"Importing data for {ticker} from file (IBKR unavailable)")
        return data_service.import_ticker_data_from_file(db, ticker)
    else:
        print(f"Fetching real data for {ticker} from IBKR")
        return data_service.fetch_and_store_historical_data(db, ticker)

def generate_historical_data(db, data_service, tickers, data_type, use_file_data=False):
    """Generate historical data for tickers"""
    print(f"Generating historical data for {data_type}...")
    
    try:
        success_count = 0
        for ticker in tickers:
            try:
                existing_count = db.query(TickerData).filter(TickerData.ticker_symbol == ticker).count()
                if existing_count == 0:
                    # Generate historical data for this ticker
                    generate_ticker_data(db, ticker, None, None, use_file_data=use_file_data)
                    print(f"Generated data for {ticker}")
                    
                    # Note: Using proxy spread (high-low) for liquidity calculations
                    # Real bid/ask data not available - using proxy spread instead
                    
                    success_count += 1
                else:
                    print(f"{ticker}: Already has {existing_count} records")
                    success_count += 1
                
                # Ensure ticker info exists (sector, industry, market_cap)
                try:
                    info = data_service._ensure_ticker_info(db, ticker)
                    if info:
                        print(f"Ticker info for {ticker}: sector={info.sector}, industry={info.industry}")
                    else:
                        print(f"Warning: No ticker info for {ticker}")
                except Exception as e:
                    print(f"Error ensuring ticker info for {ticker}: {e}")
                
            except Exception as e:
                print(f"Error generating data for {ticker}: {e}")
        
        print(f"Successfully processed {success_count}/{len(tickers)} {data_type}")
        return True
    except Exception as e:
        print(f"Error generating historical data: {e}")
        return False

def fetch_fundamental_data(db, data_service, tickers):
    """Fetch fundamental data for tickers from IBKR"""
    print("Fetching fundamental data for tickers...")
    
    try:
        # Connect once for all tickers
        print("Connecting to IBKR...")
        if not data_service.ibkr_service.connect():
            print("Failed to connect to IBKR - skipping fundamental data")
            return False
        
        success_count = 0
        for ticker in tickers:
            try:
                print(f"Fetching data for {ticker}...")
                
                # Single request per ticker - get fundamental data
                fundamental_data = data_service.ibkr_service.get_fundamentals(ticker)
                
                # Save to database using preloaded data
                info = data_service._ensure_ticker_info(db, ticker, preloaded=fundamental_data)
                
                if info:
                    success_count += 1
                    print(f"Successfully processed {ticker}")
                else:
                    print(f"Failed to process {ticker}")
                    
            except Exception as e:
                print(f"Error processing {ticker}: {e}")
                continue
        
        print(f"Successfully processed {success_count}/{len(tickers)} tickers")
        return True
        
    except Exception as e:
        print(f"Error in fetch_fundamental_data: {e}")
        return False
    finally:
        data_service.ibkr_service.disconnect()
        print("Disconnected from IBKR")

def show_database_summary(db, admin_user):
    """Show database summary"""
    print("Database summary...")
    
    try:
        total_tickers = db.query(TickerData.ticker_symbol).distinct().count()
        total_records = db.query(TickerData).count()
        portfolio_count = db.query(Portfolio).filter(Portfolio.user_id == admin_user.id).count()
        ticker_info_count = db.query(TickerInfo).count()
        
        print(f"Total tickers: {total_tickers}")
        print(f"Total records: {total_records}")
        print(f"Portfolio items: {portfolio_count}")
        print(f"Ticker info records: {ticker_info_count}")
        
        # Show date range
        date_range = db.query(TickerData.date).distinct().order_by(TickerData.date).all()
        if date_range:
            min_date = date_range[0][0]
            max_date = date_range[-1][0]
            print(f"Date range: {min_date} to {max_date}")
        
        return True
    except Exception as e:
        print(f"Error showing database summary: {e}")
        return False

def setup_database(use_file_data=False):
    """Complete database setup"""
    print("Starting complete database setup...")
    
    if use_file_data:
        print("⚠ Using imported data from files (IBKR TWS not available)")
    else:
        print("✓ Using real market data from IBKR TWS")
    
    # Step 1: Check prerequisites
    if not check_required_modules():
        return False
    
    if not check_database_connection():
        return False
    
    if not check_file_permissions():
        return False
    
    # Step 2: Remove old database
    if not remove_old_database():
        return False
    
    # Step 3: Create database tables
    if not create_database_tables():
        return False
    
    # Step 4: Migrate schema
    if not migrate_database_schema():
        return False
    
    # Step 5: Create database session
    db = SessionLocal()
    try:
        # Step 6: Create admin user
        admin_user = create_admin_user(db)
        if not admin_user:
            return False
        
        # Step 7: Create user account
        user = db.query(User).filter(User.username == "user").first()
        if not user:
            user = User(username="user", password="user123", email="user@external-zalpha.com")
            db.add(user)
            db.commit()
            print("Created user account")
        
        # Step 8: Setup portfolio for admin
        if not setup_portfolio(db, admin_user, use_file_data=use_file_data):
            return False
        
        # Step 9: Setup portfolio for user
        if not setup_portfolio(db, user, use_file_data=use_file_data):
            return False
        
        # Step 10: Initialize data service
        data_service = DataService()
        
        # Step 11: Get ALL unique tickers from both users (ONE POOL)
        all_tickers = set()
        for username in ["admin", "user"]:
            all_tickers.update(get_default_portfolio(username))
        
        # Add static tickers
        static_tickers = ['SPY', 'MTUM', 'IWM', 'VLUE', 'QUAL']
        all_tickers.update(static_tickers)
        
        print(f"Total unique tickers to process: {len(all_tickers)}")
        print(f"Tickers: {sorted(all_tickers)}")
        
        # Step 12: Generate historical data for ALL tickers
        if not generate_historical_data(db, data_service, list(all_tickers), "all tickers", use_file_data=use_file_data):
            return False
        
        # Step 13: Fetch fundamental data for all tickers (skip if using file data)
        if not use_file_data:
            if not fetch_fundamental_data(db, data_service, list(all_tickers)):
                print("Warning: Some fundamental data may be missing")
        else:
            print("Skipping fundamental data fetch (using imported data)")
        
        # Step 14: Show database summary
        if not show_database_summary(db, admin_user):
            return False
        
        print("Database setup completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error during database setup: {e}")
        return False
    finally:
        db.close()

def main():
    """Main function"""
    import sys
    
    print("=" * 60)
    print("Z-ALPHA SECURITIES - DATABASE SETUP")
    print("=" * 60)
    
    # Check if --import-files flag is provided
    use_file_data = "--import-files" in sys.argv
    
    success = setup_database(use_file_data=use_file_data)
    
    if success:
        print("\nSetup completed successfully!")
        print("You can now run the application with:")
        print("  python start_all.py")
    else:
        print("\nSetup failed!")
        print("Please check the error messages above.")
    
    return success

if __name__ == "__main__":
    main() 