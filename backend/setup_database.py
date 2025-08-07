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
sys.path.append(os.path.dirname(__file__))

from database.database import engine, SessionLocal, Base
from database.models.user import User
from database.models.portfolio import Portfolio
from database.models.ticker_data import TickerData
from services.data_service import DataService
from sqlalchemy import Index

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
        
        # Create composite index for ticker_data
        Index('idx_ticker_data_symbol_date', TickerData.ticker_symbol, TickerData.date)
        print("Database tables created successfully")
        return True
    except Exception as e:
        print(f"Error creating database tables: {e}")
        return False

def create_admin_user(db):
    """Create admin user"""
    print("Creating admin user...")
    
    try:
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
            print("Admin user created successfully")
        else:
            print("Admin user already exists")
        
        return admin_user
    except Exception as e:
        print(f"Error creating admin user: {e}")
        db.rollback()
        return None

def setup_portfolio(db, admin_user):
    """Setup portfolio with tickers"""
    print("Setting up portfolio...")
    
    try:
        portfolio_tickers = [
            "AMD", "APP", "BRK-B", "BULL", "DOMO", "GOOGL", 
            "META", "QQQM", "RDDT", "SGOV", "SMCI", "SNOW", 
            "TSLA", "ULTY"
        ]
        
        added_count = 0
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
                added_count += 1
        
        db.commit()
        print(f"Portfolio initialized with {added_count} new tickers")
        return True
    except Exception as e:
        print(f"Error setting up portfolio: {e}")
        db.rollback()
        return False

def generate_historical_data(db, data_service, tickers, data_type):
    """Generate historical data for tickers"""
    print(f"Generating historical data for {data_type}...")
    
    try:
        success_count = 0
        for ticker in tickers:
            try:
                existing_count = db.query(TickerData).filter(TickerData.ticker_symbol == ticker).count()
                if existing_count == 0:
                    success = data_service.inject_sample_data(db, ticker)
                    if success:
                        print(f"Generated data for {ticker}")
                        success_count += 1
                    else:
                        print(f"Failed to generate data for {ticker}")
                else:
                    print(f"{ticker}: Already has {existing_count} records")
                    success_count += 1
            except Exception as e:
                print(f"Error generating data for {ticker}: {e}")
        
        print(f"Successfully processed {success_count}/{len(tickers)} {data_type}")
        return True
    except Exception as e:
        print(f"Error generating historical data: {e}")
        return False

def show_database_summary(db, admin_user):
    """Show database summary"""
    print("Database summary...")
    
    try:
        total_tickers = db.query(TickerData.ticker_symbol).distinct().count()
        total_records = db.query(TickerData).count()
        portfolio_count = db.query(Portfolio).filter(Portfolio.user_id == admin_user.id).count()
        
        print(f"Total tickers: {total_tickers}")
        print(f"Total records: {total_records}")
        print(f"Portfolio items: {portfolio_count}")
        
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
    """Complete database setup with error handling"""
    print("Starting complete database setup...")
    
    # Sanity checks
    print("\nPerforming sanity checks...")
    
    if not check_required_modules():
        print("Sanity check failed: Missing modules")
        return False
    
    if not check_database_connection():
        print("Sanity check failed: Database connection")
        return False
    
    if not check_file_permissions():
        print("Sanity check failed: File permissions")
        return False
    
    print("All sanity checks passed!")
    
    # Remove old database
    if not remove_old_database():
        return False
    
    # Create tables
    if not create_database_tables():
        return False
    
    db = SessionLocal()
    data_service = DataService()
    
    try:
        # Create admin user
        admin_user = create_admin_user(db)
        if not admin_user:
            return False
        
        # Setup portfolio
        if not setup_portfolio(db, admin_user):
            return False
        
        # Generate historical data for portfolio tickers
        portfolio_tickers = [
            "AMD", "APP", "BRK-B", "BULL", "DOMO", "GOOGL", 
            "META", "QQQM", "RDDT", "SGOV", "SMCI", "SNOW", 
            "TSLA", "ULTY"
        ]
        
        if not generate_historical_data(db, data_service, portfolio_tickers, "portfolio tickers"):
            return False
        
        # Generate historical data for static tickers
        static_tickers = data_service.get_static_tickers()
        if not generate_historical_data(db, data_service, static_tickers, "static tickers"):
            return False
        
        print("\nAll historical data generated successfully!")
        
        # Show summary
        if not show_database_summary(db, admin_user):
            return False
        
        return True
        
    except Exception as e:
        print(f"Unexpected error during setup: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def main():
    """Main setup function"""
    print("=" * 60)
    print("Z-ALPHA SECURITIES - DATABASE SETUP")
    print("=" * 60)
    
    try:
        # Setup database
        if not setup_database():
            print("Database setup failed!")
            return
        
        print("\n" + "=" * 60)
        print("SETUP COMPLETE!")
        print("=" * 60)
        print("\nDatabase is ready for Docker deployment!")
        print("Run start_all.py to start the application.")
        
    except Exception as e:
        print(f"Unexpected error in main: {e}")
        return

if __name__ == "__main__":
    main() 