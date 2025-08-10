#!/usr/bin/env python3
"""
One-time script to download historical data for fallback use
Downloads data for all tickers used in the application and saves as JSON files
Uses IBKR TWS API for data fetching
"""

import os
import sys
import json
import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# Add backend to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Import IBKR service
from services.ibkr_service import IBKRService

# List of all tickers used in the application
TICKERS = [
    # Admin portfolio
    "AMD", "APP", "BULL", "DOMO", "GOOGL", "META", "QQQM", "RDDT", "SGOV", "SMCI", "SNOW", "TSLA", "ULTY",
    # User portfolio  
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "NFLX", "ADBE", "CRM", "ORCL", "INTC",
    # Static tickers
    "SPY", "MTUM", "IWM", "VLUE", "QUAL"
]

# Remove duplicates and sort
TICKERS = sorted(list(set(TICKERS)))

# Portfolio definitions
ADMIN_PORTFOLIO = [
    {"ticker": "AMD", "shares": 100},
    {"ticker": "APP", "shares": 200},
    {"ticker": "BULL", "shares": 150},
    {"ticker": "DOMO", "shares": 300},
    {"ticker": "GOOGL", "shares": 50},
    {"ticker": "META", "shares": 80},
    {"ticker": "QQQM", "shares": 100},
    {"ticker": "RDDT", "shares": 250},
    {"ticker": "SGOV", "shares": 500},
    {"ticker": "SMCI", "shares": 75},
    {"ticker": "SNOW", "shares": 120},
    {"ticker": "TSLA", "shares": 60},
    {"ticker": "ULTY", "shares": 100}
]

USER_PORTFOLIO = [
    {"ticker": "AAPL", "shares": 100},
    {"ticker": "MSFT", "shares": 80},
    {"ticker": "GOOGL", "shares": 60},
    {"ticker": "AMZN", "shares": 70},
    {"ticker": "NVDA", "shares": 50},
    {"ticker": "META", "shares": 90},
    {"ticker": "TSLA", "shares": 40},
    {"ticker": "NFLX", "shares": 120},
    {"ticker": "ADBE", "shares": 85},
    {"ticker": "CRM", "shares": 110},
    {"ticker": "ORCL", "shares": 95},
    {"ticker": "INTC", "shares": 130}
]

def download_historical_data_ibkr(symbol: str, ibkr_service: IBKRService) -> Optional[List[Dict[str, Any]]]:
    """Download historical data using IBKR TWS"""
    try:
        print(f"Downloading {symbol} data from IBKR TWS...")
        
        # Get historical data from IBKR
        historical_data = ibkr_service.get_historical_data(symbol, duration="9 Y", bar_size="1 day")
        
        if not historical_data:
            print(f"No data received for {symbol}")
            return None
        
        # Convert to standardized format
        data = []
        for bar in historical_data:
            data.append({
                'date': bar['date'],
                'open': float(bar['open']),
                'high': float(bar['high']),
                'low': float(bar['low']),
                'close': float(bar['close']),
                'volume': int(bar['volume'])
            })
        
        print(f"Downloaded {len(data)} records for {symbol}")
        return data
        
    except Exception as e:
        print(f"Error downloading {symbol}: {e}")
        return None

def download_fundamental_data_complete(symbol: str, ibkr_service: IBKRService) -> Optional[Dict[str, Any]]:
    """Download complete fundamental data using IBKR + external APIs"""
    try:
        print(f"Getting fundamental data for {symbol}...")
        
        # Step 1: Get basic data from IBKR
        ibkr_data = ibkr_service.get_fundamentals(symbol)
        
        # Step 2: Get sector/industry from external API
        sector, industry = ibkr_service._get_sector_industry_external(symbol)
        
        # Step 3: Get market cap from external API
        market_cap = ibkr_service._get_market_cap_external(symbol)
        
        # Combine all data
        fundamental_data = {
            'symbol': symbol,
            'company_name': ibkr_data.get('company_name', symbol) if ibkr_data else symbol,
            'sector': sector or 'Unknown',
            'industry': industry or 'Unknown',
            'market_cap': market_cap,
            'type': ibkr_data.get('type', 'Unknown') if ibkr_data else 'Unknown'
        }
        
        # Clean up None values
        fundamental_data = {k: v for k, v in fundamental_data.items() if v is not None}
        
        print(f"Fundamental data for {symbol}: {fundamental_data.get('sector', 'Unknown')} / {fundamental_data.get('industry', 'Unknown')}")
        return fundamental_data
        
    except Exception as e:
        print(f"Error getting fundamental data for {symbol}: {e}")
        return None

def save_combined_data(fundamental_data: Dict[str, Any], historical_data: List[Dict[str, Any]], filename: str):
    """Save combined fundamental and historical data to JSON file"""
    try:
        combined_data = {
            "fundamental": fundamental_data,
            "stock": historical_data
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(combined_data, f, indent=2, ensure_ascii=False)
        print(f"Saved combined data to {filename}")
    except Exception as e:
        print(f"Error saving {filename}: {e}")

def save_portfolio_data(portfolio_data: List[Dict[str, Any]], filename: str):
    """Save portfolio data to JSON file"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(portfolio_data, f, indent=2, ensure_ascii=False)
        print(f"Saved portfolio data to {filename}")
    except Exception as e:
        print(f"Error saving {filename}: {e}")

def create_data_directory():
    """Create data directory if it doesn't exist"""
    data_dir = "data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"Created directory: {data_dir}")
    return data_dir

def check_ibkr_connection(ibkr_service: IBKRService) -> bool:
    """Check if IBKR TWS is connected"""
    print("Checking IBKR TWS connection...")
    
    if ibkr_service.connect():
        print("Connected to IBKR TWS successfully")
        return True
    else:
        print("Failed to connect to IBKR TWS")
        print("   Please ensure:")
        print("   1. IBKR TWS is running")
        print("   2. API connections are enabled in TWS")
        print("   3. Socket port is set to 7497 (paper) or 7496 (live)")
        return False

def check_existing_files(data_dir: str, symbol: str) -> bool:
    """Check if combined data file already exists"""
    combined_file = os.path.join(data_dir, f"{symbol}.json")
    return os.path.exists(combined_file)

def main():
    """Main function"""
    print("=" * 60)
    print("Z-ALPHA SECURITIES - FALLBACK DATA DOWNLOADER")
    print("=" * 60)
    print(f"Processing {len(TICKERS)} tickers: {', '.join(TICKERS)}")
    print()
    
    # Create data directory
    data_dir = create_data_directory()
    
    # Initialize IBKR service
    ibkr_service = IBKRService()
    
    try:
        # Check IBKR connection
        if not check_ibkr_connection(ibkr_service):
            print("\nCannot proceed without IBKR TWS connection")
            print("   Please start IBKR TWS and try again")
            return False
        
        # Track statistics
        stats = {
            'success': 0,
            'failed': 0,
            'skipped': 0
        }
        
        # Process each ticker
        for i, symbol in enumerate(TICKERS, 1):
            print(f"\n[{i}/{len(TICKERS)}] Processing {symbol}...")
            
            # Check if file already exists
            if check_existing_files(data_dir, symbol):
                print(f"Skipping {symbol} (already exists)")
                stats['skipped'] += 1
                continue
            
            # Download both fundamental and historical data
            fundamental_data = download_fundamental_data_complete(symbol, ibkr_service)
            historical_data = download_historical_data_ibkr(symbol, ibkr_service)
            
            if fundamental_data and historical_data:
                # Save combined data
                combined_file = os.path.join(data_dir, f"{symbol}.json")
                save_combined_data(fundamental_data, historical_data, combined_file)
                stats['success'] += 1
            else:
                print(f"Failed to get complete data for {symbol}")
                stats['failed'] += 1
            
            # Rate limiting - be nice to IBKR API
            time.sleep(1.0)
        
        # Save portfolio files
        print("\nSaving portfolio files...")
        admin_portfolio_file = os.path.join(data_dir, "admin_portfolio.json")
        user_portfolio_file = os.path.join(data_dir, "user_portfolio.json")
        
        save_portfolio_data(ADMIN_PORTFOLIO, admin_portfolio_file)
        save_portfolio_data(USER_PORTFOLIO, user_portfolio_file)
        
        # Summary
        print("\n" + "=" * 60)
        print("DOWNLOAD SUMMARY")
        print("=" * 60)
        print(f"Combined data: {stats['success']} success, {stats['failed']} failed, {stats['skipped']} skipped")
        print(f"Files saved to: {data_dir}/")
        print(f"Portfolio files: admin_portfolio.json, user_portfolio.json")
        print()
        
        if stats['success'] > 0 or stats['skipped'] > 0:
            print("Fallback data ready! You can now use:")
            print("   python start_all.py")
            print("   (When IBKR TWS is not available, select 'Import from files')")
            return True
        else:
            print("No data was downloaded successfully")
            print("   Check your IBKR TWS connection and try again")
            return False
            
    finally:
        # Clean up IBKR connection
        print("Disconnecting from IBKR TWS...")
        ibkr_service.disconnect()
        print("Disconnected from IBKR TWS")

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
