#!/usr/bin/env python3
"""
Import database from JSON export file
"""

import json
import os
import sys
from datetime import datetime
from sqlalchemy.orm import Session
from database.database import SessionLocal, engine, Base
from database.models.user import User
from database.models.portfolio import Portfolio
from database.models.ticker import Ticker
from database.models.historical_data import HistoricalData
from database.models.ticker_data import TickerData

def parse_datetime(date_string):
    """Parse ISO datetime string"""
    if not date_string:
        return None
    try:
        return datetime.fromisoformat(date_string)
    except:
        return None

def parse_date(date_string):
    """Parse ISO date string"""
    if not date_string:
        return None
    try:
        return datetime.fromisoformat(date_string).date()
    except:
        return None

def import_users(db: Session, users_data):
    """Import users data"""
    print(f"Importing {len(users_data)} users...")
    
    for user_data in users_data:
        user = User(
            id=user_data['id'],
            username=user_data['username'],
            password=user_data['password'],
            email=user_data.get('email'),
            created_at=parse_datetime(user_data.get('created_at')),
            updated_at=parse_datetime(user_data.get('updated_at'))
        )
        db.merge(user)  # Use merge to handle existing records
    
    db.commit()
    print(f"Users imported successfully")

def import_portfolios(db: Session, portfolios_data):
    """Import portfolios data"""
    print(f"Importing {len(portfolios_data)} portfolios...")
    
    for portfolio_data in portfolios_data:
        portfolio = Portfolio(
            id=portfolio_data['id'],
            user_id=portfolio_data['user_id'],
            ticker_symbol=portfolio_data['ticker_symbol'],
            shares=portfolio_data['shares'],
            created_at=parse_datetime(portfolio_data.get('created_at')),
            updated_at=parse_datetime(portfolio_data.get('updated_at'))
        )
        db.merge(portfolio)
    
    db.commit()
    print(f"Portfolios imported successfully")

def import_tickers(db: Session, tickers_data):
    """Import tickers data"""
    print(f"Importing {len(tickers_data)} tickers...")
    
    for ticker_data in tickers_data:
        ticker = Ticker(
            id=ticker_data['id'],
            symbol=ticker_data['symbol'],
            company_name=ticker_data.get('company_name'),
            sector=ticker_data.get('sector'),
            market_cap=ticker_data.get('market_cap'),
            last_price=ticker_data.get('last_price'),
            volume=ticker_data.get('volume'),
            created_at=parse_datetime(ticker_data.get('created_at')),
            updated_at=parse_datetime(ticker_data.get('updated_at'))
        )
        db.merge(ticker)
    
    db.commit()
    print(f"Tickers imported successfully")

def import_historical_data(db: Session, historical_data):
    """Import historical data"""
    print(f"Importing {len(historical_data)} historical data records...")
    
    # Import in batches for better performance
    batch_size = 1000
    for i in range(0, len(historical_data), batch_size):
        batch = historical_data[i:i + batch_size]
        
        for data_record in batch:
            historical_record = HistoricalData(
                id=data_record['id'],
                ticker_id=data_record['ticker_id'],
                date=parse_date(data_record.get('date')),
                open_price=data_record.get('open_price'),
                close_price=data_record.get('close_price'),
                high_price=data_record.get('high_price'),
                low_price=data_record.get('low_price'),
                volume=data_record.get('volume'),
                created_at=parse_datetime(data_record.get('created_at'))
            )
            db.merge(historical_record)
        
        db.commit()
        print(f"  Batch {i//batch_size + 1}/{(len(historical_data) + batch_size - 1)//batch_size} imported...")
    
    print(f"Historical data imported successfully")

def import_ticker_data(db: Session, ticker_data):
    """Import ticker_data table data"""
    print(f"Importing {len(ticker_data)} ticker data records...")
    
    # Import in batches for better performance
    batch_size = 1000
    for i in range(0, len(ticker_data), batch_size):
        batch = ticker_data[i:i + batch_size]
        
        for data_record in batch:
            ticker_record = TickerData(
                id=data_record['id'],
                ticker_symbol=data_record['ticker_symbol'],
                date=parse_date(data_record.get('date')),
                open_price=data_record.get('open_price'),
                close_price=data_record.get('close_price'),
                high_price=data_record.get('high_price'),
                low_price=data_record.get('low_price'),
                volume=data_record.get('volume'),
                created_at=parse_datetime(data_record.get('created_at'))
            )
            db.merge(ticker_record)
        
        db.commit()
        print(f"  Batch {i//batch_size + 1}/{(len(ticker_data) + batch_size - 1)//batch_size} imported...")
    
    print(f"Ticker data imported successfully")

def import_database(import_file):
    """Import database from JSON file"""
    print("=" * 60)
    print("Z-ALPHA SECURITIES - DATABASE IMPORT")
    print("=" * 60)
    
    # Check if import file exists
    if not os.path.exists(import_file):
        print(f"Error: Import file {import_file} not found!")
        return False
    
    print(f"Importing from: {import_file}")
    
    # Load JSON data
    try:
        with open(import_file, 'r', encoding='utf-8') as f:
            import_data = json.load(f)
    except Exception as e:
        print(f"Error reading import file: {e}")
        return False
    
    # Validate data structure
    required_keys = ['metadata', 'users', 'portfolios', 'tickers', 'historical_data', 'ticker_data']
    for key in required_keys:
        if key not in import_data:
            print(f"Error: Missing required key '{key}' in import file")
            return False
    
    # Display import info
    metadata = import_data['metadata']
    print(f"\nImport Information:")
    print(f"  Export timestamp: {metadata.get('export_timestamp', 'Unknown')}")
    print(f"  Users: {len(import_data['users'])}")
    print(f"  Portfolios: {len(import_data['portfolios'])}")
    print(f"  Tickers: {len(import_data['tickers'])}")
    print(f"  Historical Data: {len(import_data['historical_data'])}")
    print(f"  Ticker Data: {len(import_data['ticker_data'])}")
    
    # Create database tables
    print("\nCreating database tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Import all data
        print("\nImporting data...")
        
        import_users(db, import_data['users'])
        import_portfolios(db, import_data['portfolios'])
        import_tickers(db, import_data['tickers'])
        import_historical_data(db, import_data['historical_data'])
        import_ticker_data(db, import_data['ticker_data'])
        
        print(f"\n" + "=" * 60)
        print("IMPORT COMPLETE!")
        print("=" * 60)
        print("Database has been successfully populated with sample data!")
        
        # Verify import
        print("\nVerifying import...")
        users_count = db.query(User).count()
        portfolios_count = db.query(Portfolio).count()
        tickers_count = db.query(Ticker).count()
        historical_count = db.query(HistoricalData).count()
        ticker_data_count = db.query(TickerData).count()
        
        print(f"  Users in database: {users_count}")
        print(f"  Portfolios in database: {portfolios_count}")
        print(f"  Tickers in database: {tickers_count}")
        print(f"  Historical data in database: {historical_count}")
        print(f"  Ticker data in database: {ticker_data_count}")
        
        return True
        
    except Exception as e:
        print(f"Error during import: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def main():
    """Main import function"""
    import_file = "z_alpha_sample_database.json"
    
    # Allow custom import file as argument
    if len(sys.argv) > 1:
        import_file = sys.argv[1]
    
    try:
        if not import_database(import_file):
            print("Import failed!")
            sys.exit(1)
        
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()