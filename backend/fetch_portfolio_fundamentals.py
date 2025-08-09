#!/usr/bin/env python3
"""
Fetch fundamental data from IBKR for all portfolio tickers
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.ibkr_service import IBKRService
from database.database import SessionLocal
from database.models.ticker import TickerInfo
from database.models.user import User
from database.models.portfolio import Portfolio
from datetime import datetime, timezone

def fetch_portfolio_fundamentals():
    """Fetch fundamental data from IBKR for all portfolio tickers"""
    print("=" * 60)
    print("FETCHING PORTFOLIO FUNDAMENTALS FROM IBKR")
    print("=" * 60)
    
    # Initialize IBKR service
    ibkr_service = IBKRService()
    
    # Get database session
    db = SessionLocal()
    
    try:
        # Get admin user
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            print("❌ Admin user not found")
            return False
        
        # Get portfolio tickers
        portfolio_items = db.query(Portfolio).filter(Portfolio.user_id == admin_user.id).all()
        if not portfolio_items:
            print("❌ No portfolio items found")
            return False
        
        tickers = [item.ticker_symbol for item in portfolio_items]
        print(f"Found {len(tickers)} portfolio tickers: {', '.join(tickers)}")
        
        # Connect to IBKR
        print("🔌 Connecting to IBKR...")
        if not ibkr_service.connect():
            print("❌ Failed to connect to IBKR")
            return False
        
        print("Connected to IBKR successfully")
        
        # Fetch fundamental data for each ticker
        success_count = 0
        total_count = len(tickers)
        
        for i, ticker in enumerate(tickers, 1):
            print(f"\n[{i}/{total_count}] 🔍 Fetching fundamental data for {ticker}...")
            
            try:
                # Get fundamental data
                fundamental_data = ibkr_service.get_fundamentals(ticker)
                
                if fundamental_data:
                    print(f"Fundamental data received for {ticker}:")
                    print(f"   Industry: {fundamental_data.get('industry')}")
                    print(f"   Sector: {fundamental_data.get('sector')}")
                    print(f"   Market Cap: {fundamental_data.get('market_cap')}")
                    print(f"   Company Name: {fundamental_data.get('company_name')}")
                    
                    # Update or create ticker info
                    ticker_info = db.query(TickerInfo).filter(TickerInfo.symbol == ticker).first()
                    if not ticker_info:
                        ticker_info = TickerInfo(symbol=ticker)
                        db.add(ticker_info)
                    
                    ticker_info.industry = fundamental_data.get("industry")
                    ticker_info.sector = fundamental_data.get("sector")
                    ticker_info.market_cap = fundamental_data.get("market_cap")
                    ticker_info.company_name = fundamental_data.get("company_name")
                    ticker_info.updated_at = datetime.now(timezone.utc)
                    
                    print(f"Updated ticker info for {ticker}")
                    success_count += 1
                    
                else:
                    print(f"❌ No fundamental data received for {ticker}")
                    
            except Exception as e:
                print(f"❌ Error fetching data for {ticker}: {e}")
        
        # Commit all changes
        db.commit()
        print(f"\nSuccessfully processed {success_count}/{total_count} tickers")
        
        # Show summary
        print("\nDATABASE SUMMARY:")
        all_tickers = db.query(TickerInfo).all()
        print(f"Total ticker_info records: {len(all_tickers)}")
        
        # Show tickers with market cap data
        tickers_with_market_cap = [t for t in all_tickers if t.market_cap and t.market_cap > 0]
        print(f"Tickers with market cap data: {len(tickers_with_market_cap)}")
        
        for ticker in tickers_with_market_cap:
            print(f"  {ticker.symbol}: {ticker.sector} → {ticker.industry} (${ticker.market_cap:,.0f})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        return False
        
    finally:
        # Disconnect from IBKR
        print("🔌 Disconnecting from IBKR...")
        ibkr_service.disconnect()
        
        # Close database session
        db.close()

if __name__ == "__main__":
    success = fetch_portfolio_fundamentals()
    
    print("=" * 60)
    if success:
        print("Portfolio fundamentals fetch completed successfully")
    else:
        print("❌ Portfolio fundamentals fetch failed")
    print("=" * 60)
