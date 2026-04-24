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
    """Verify Postgres is reachable via SQLAlchemy engine."""
    print("Checking database connection...")
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("Database connection OK")
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

def drop_all_tables():
    """Drop all tables for a clean re-seed. Volume wipe is handled by start_all."""
    print("Dropping existing tables...")
    try:
        Base.metadata.drop_all(bind=engine)
        print("Tables dropped")
        return True
    except Exception as e:
        print(f"Error dropping tables: {e}")
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

SEED_USERS = [
    {
        "slot": "ADMIN",
        "default_username": "admin",
        "default_email": "admin@zalpha.local",
        "portfolio_fixture": "admin_portfolio.json",
    },
    {
        "slot": "USER",
        "default_username": "user",
        "default_email": "user@zalpha.local",
        "portfolio_fixture": "user_portfolio.json",
    },
]


def _read_seed_credentials(slot: str, default_username: str, default_email: str) -> dict:
    """Read {SLOT}_USERNAME / {SLOT}_EMAIL / {SLOT}_PASSWORD from env.
    Username/email fall back to sane defaults; password has no default and must be set."""
    username = os.environ.get(f"{slot}_USERNAME", default_username)
    email = os.environ.get(f"{slot}_EMAIL", default_email)
    password = os.environ.get(f"{slot}_PASSWORD")
    if not password:
        raise RuntimeError(
            f"{slot}_PASSWORD is not set. Copy config.env.example to .env and set a password."
        )
    if len(password) < 8:
        raise RuntimeError(f"{slot}_PASSWORD must be at least 8 characters.")
    return {"username": username, "email": email, "password": password}


def seed_users(db) -> dict:
    """Create admin + user from env (idempotent). Returns {slot: User} map."""
    from auth.passwords import hash_password

    print("Seeding users from environment...")
    created = {}
    for entry in SEED_USERS:
        slot = entry["slot"]
        creds = _read_seed_credentials(slot, entry["default_username"], entry["default_email"])

        user = db.query(User).filter(User.username == creds["username"]).first()
        if user:
            print(f"  {slot}: user '{creds['username']}' already exists -- skipping")
        else:
            user = User(
                username=creds["username"],
                email=creds["email"],
                password_hash=hash_password(creds["password"]),
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"  {slot}: created user '{creds['username']}' (id={user.id})")
        created[slot] = user
    return created

def _resolve_fixture_path(filename: str) -> str:
    """Locate a fixture file whether script runs from project root or backend/."""
    candidates = [f"../data/{filename}", f"data/{filename}"]
    for path in candidates:
        if os.path.exists(path):
            return path
    return candidates[0]  # return primary for error messages


def get_tickers_from_fixture(fixture_filename: str) -> List[str]:
    """Return list of ticker symbols from a portfolio fixture file."""
    portfolio_file = _resolve_fixture_path(fixture_filename)
    try:
        if not os.path.exists(portfolio_file):
            print(f"Portfolio fixture {portfolio_file} not found")
            return []
        with open(portfolio_file, 'r') as f:
            portfolio_data = json.load(f)
        if not isinstance(portfolio_data, list):
            print(f"Invalid portfolio format in {portfolio_file}: expected list")
            return []
        return [item.get('ticker') for item in portfolio_data if 'ticker' in item]
    except Exception as e:
        print(f"Error reading {portfolio_file}: {e}")
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

def setup_portfolio(db, user, fixture_filename: str):
    """Import a portfolio fixture file into the DB for the given user."""
    print(f"Setting up portfolio for {user.username} from {fixture_filename}...")
    portfolio_file = _resolve_fixture_path(fixture_filename)
    return import_portfolio_from_file(db, user, portfolio_file)

def generate_ticker_data(db, ticker):
    """Fetch real historical data from IBKR for a ticker"""
    data_service = DataService()
    print(f"Fetching real data for {ticker} from IBKR")
    return data_service.fetch_and_store_historical_data(db, ticker)

def generate_historical_data(db, data_service, tickers, data_type):
    """Generate historical data for tickers"""
    print(f"Generating historical data for {data_type}...")

    try:
        success_count = 0
        for ticker in tickers:
            try:
                existing_count = db.query(TickerData).filter(TickerData.ticker_symbol == ticker).count()
                if existing_count == 0:
                    # Generate historical data for this ticker
                    generate_ticker_data(db, ticker)
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

def setup_database():
    """Complete database setup"""
    print("Starting complete database setup...")
    print("Using real market data from IBKR TWS")

    # Step 1: Check prerequisites
    if not check_required_modules():
        return False

    if not check_database_connection():
        return False

    # Step 2: Drop existing tables for clean re-seed
    if not drop_all_tables():
        return False

    # Step 3: Create database tables
    if not create_database_tables():
        return False
    
    # Step 5: Create database session
    db = SessionLocal()
    try:
        # Step 6: Seed users (admin + user) from env
        try:
            users_by_slot = seed_users(db)
        except RuntimeError as e:
            print(f"User seeding failed: {e}")
            return False

        # Step 7-8: Import portfolio fixture for each seeded user
        for entry in SEED_USERS:
            user = users_by_slot[entry["slot"]]
            if not setup_portfolio(db, user, entry["portfolio_fixture"]):
                return False

        # Step 10: Initialize data service
        data_service = DataService()

        # Step 11: Collect all unique tickers across both portfolios
        all_tickers = set()
        for entry in SEED_USERS:
            all_tickers.update(get_tickers_from_fixture(entry["portfolio_fixture"]))
        
        # Add static tickers
        static_tickers = ['SPY', 'MTUM', 'IWM', 'VLUE', 'QUAL']
        all_tickers.update(static_tickers)
        
        print(f"Total unique tickers to process: {len(all_tickers)}")
        print(f"Tickers: {sorted(all_tickers)}")
        
        # Step 12: Generate historical data for ALL tickers
        if not generate_historical_data(db, data_service, list(all_tickers), "all tickers"):
            return False

        # Step 13: Fetch fundamental data for all tickers
        if not fetch_fundamental_data(db, data_service, list(all_tickers)):
            print("Warning: Some fundamental data may be missing")
        
        # Step 14: Show database summary (use admin slot as reference for portfolio count)
        if not show_database_summary(db, users_by_slot["ADMIN"]):
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
    print("=" * 60)
    print("Z-ALPHA SECURITIES - DATABASE SETUP")
    print("=" * 60)

    success = setup_database()

    if success:
        print("\nSetup completed successfully!")
        print("You can now run the application with:")
        print("  python start_all.py")
    else:
        print("\nSetup failed!")
        print("Please check the error messages above.")

    return success


if __name__ == "__main__":
    import sys as _sys
    _sys.exit(0 if main() else 1)
