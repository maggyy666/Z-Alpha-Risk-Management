#!/usr/bin/env python3
"""
Export current database to JSON format for easy distribution
"""

import json
import os
import sys
from datetime import datetime, date
from sqlalchemy.orm import Session
from database.database import SessionLocal, engine
from database.models.user import User
from database.models.portfolio import Portfolio
from database.models.ticker import Ticker
from database.models.historical_data import HistoricalData
from database.models.ticker_data import TickerData

def serialize_datetime(obj):
    """JSON serializer for datetime objects"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

def export_users(db: Session):
    """Export all users data"""
    users = db.query(User).all()
    return [
        {
            "id": user.id,
            "username": user.username,
            "password": user.password,
            "email": user.email,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None
        }
        for user in users
    ]

def export_portfolios(db: Session):
    """Export all portfolio data"""
    portfolios = db.query(Portfolio).all()
    return [
        {
            "id": portfolio.id,
            "user_id": portfolio.user_id,
            "ticker_symbol": portfolio.ticker_symbol,
            "shares": portfolio.shares,
            "created_at": portfolio.created_at.isoformat() if portfolio.created_at else None,
            "updated_at": portfolio.updated_at.isoformat() if portfolio.updated_at else None
        }
        for portfolio in portfolios
    ]

def export_tickers(db: Session):
    """Export all ticker data"""
    tickers = db.query(Ticker).all()
    return [
        {
            "id": ticker.id,
            "symbol": ticker.symbol,
            "company_name": ticker.company_name,
            "sector": ticker.sector,
            "market_cap": ticker.market_cap,
            "last_price": ticker.last_price,
            "volume": ticker.volume,
            "created_at": ticker.created_at.isoformat() if ticker.created_at else None,
            "updated_at": ticker.updated_at.isoformat() if ticker.updated_at else None
        }
        for ticker in tickers
    ]

def export_historical_data(db: Session):
    """Export all historical data"""
    historical_data = db.query(HistoricalData).all()
    return [
        {
            "id": data.id,
            "ticker_id": data.ticker_id,
            "date": data.date.isoformat() if data.date else None,
            "open_price": data.open_price,
            "close_price": data.close_price,
            "high_price": data.high_price,
            "low_price": data.low_price,
            "volume": data.volume,
            "created_at": data.created_at.isoformat() if data.created_at else None
        }
        for data in historical_data
    ]

def export_ticker_data(db: Session):
    """Export all ticker_data table data"""
    ticker_data = db.query(TickerData).all()
    return [
        {
            "id": data.id,
            "ticker_symbol": data.ticker_symbol,
            "date": data.date.isoformat() if data.date else None,
            "open_price": data.open_price,
            "close_price": data.close_price,
            "high_price": data.high_price,
            "low_price": data.low_price,
            "volume": data.volume,
            "created_at": data.created_at.isoformat() if data.created_at else None
        }
        for data in ticker_data
    ]

def get_database_stats(db: Session):
    """Get database statistics"""
    stats = {
        "users_count": db.query(User).count(),
        "portfolios_count": db.query(Portfolio).count(),
        "tickers_count": db.query(Ticker).count(),
        "historical_data_count": db.query(HistoricalData).count(),
        "ticker_data_count": db.query(TickerData).count(),
        "export_timestamp": datetime.now().isoformat()
    }
    return stats

def export_database():
    """Export entire database to JSON file"""
    print("=" * 60)
    print("Z-ALPHA SECURITIES - DATABASE EXPORT")
    print("=" * 60)
    
    # Check if database exists
    db_path = "portfolio.db"
    if not os.path.exists(db_path):
        print(f"Error: Database file {db_path} not found!")
        return False
    
    print(f"Exporting database: {db_path}")
    
    db = SessionLocal()
    try:
        # Get database stats first
        stats = get_database_stats(db)
        print(f"\nDatabase Statistics:")
        print(f"  Users: {stats['users_count']}")
        print(f"  Portfolios: {stats['portfolios_count']}")
        print(f"  Tickers: {stats['tickers_count']}")
        print(f"  Historical Data Records: {stats['historical_data_count']}")
        print(f"  Ticker Data Records: {stats['ticker_data_count']}")
        
        # Export all data
        print("\nExporting data...")
        
        export_data = {
            "metadata": stats,
            "users": export_users(db),
            "portfolios": export_portfolios(db),
            "tickers": export_tickers(db),
            "historical_data": export_historical_data(db),
            "ticker_data": export_ticker_data(db)
        }
        
        # Save to JSON file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"z_alpha_database_export_{timestamp}.json"
        
        print(f"Saving to: {output_file}")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, default=serialize_datetime)
        
        # Get file size
        file_size = os.path.getsize(output_file)
        file_size_mb = file_size / (1024 * 1024)
        
        print(f"\n" + "=" * 60)
        print("EXPORT COMPLETE!")
        print("=" * 60)
        print(f"Export file: {output_file}")
        print(f"File size: {file_size_mb:.2f} MB")
        print(f"Total records exported: {sum([
            len(export_data['users']),
            len(export_data['portfolios']),
            len(export_data['tickers']),
            len(export_data['historical_data']),
            len(export_data['ticker_data'])
        ])}")
        
        # Also create a copy with a standard name for distribution
        standard_name = "z_alpha_sample_database.json"
        with open(standard_name, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, default=serialize_datetime)
        
        print(f"Standard copy created: {standard_name}")
        
        return True
        
    except Exception as e:
        print(f"Error during export: {e}")
        return False
    finally:
        db.close()

def main():
    """Main export function"""
    try:
        if not export_database():
            print("Export failed!")
            sys.exit(1)
        
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()