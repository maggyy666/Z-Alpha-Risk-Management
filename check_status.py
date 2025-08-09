
"""
Check status of all components
"""

import requests
import json
import sqlite3
import os

def check_backend():
    """Check backend status"""
    print("Checking backend...")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("Backend is running")
            return True
        else:
            print("Backend is not responding properly")
            return False
    except requests.exceptions.RequestException:
        print("Backend is not running")
        return False

def check_frontend():
    """Check frontend status"""
    print("Checking frontend...")
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            print("Frontend is running")
            return True
        else:
            print("Frontend is not responding properly")
            return False
    except requests.exceptions.RequestException:
        print("Frontend is not running")
        return False

def check_database():
    """Check database status"""
    print("Checking database...")
    try:
        if not os.path.exists("portfolio.db"):
            print("Database file not found")
            return False
        
        conn = sqlite3.connect("portfolio.db")
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Database tables: {', '.join(tables)}")
        
        # Check data
        cursor.execute("SELECT COUNT(*) FROM ticker_data;")
        total_records = cursor.fetchone()[0]
        print(f"Total records: {total_records}")
        
        cursor.execute("SELECT COUNT(DISTINCT ticker_symbol) FROM ticker_data;")
        total_tickers = cursor.fetchone()[0]
        print(f"Total tickers: {total_tickers}")
        
        # Check date range
        cursor.execute("SELECT MIN(date), MAX(date) FROM ticker_data;")
        min_date, max_date = cursor.fetchone()
        print(f"Date range: {min_date} to {max_date}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Database error: {e}")
        return False

def test_endpoints():
    """Test all endpoints"""
    print("\nTesting endpoints...")
    
    endpoints = [
        ("/concentration-risk-data?username=admin", "Concentration Risk"),
        ("/factor-exposure-data?username=admin", "Factor Exposure"),
        ("/volatility-data?username=admin", "Volatility Data"),
        ("/risk-scoring?username=admin", "Risk Scoring"),
        ("/stress-testing?username=admin", "Stress Testing"),
    ]
    
    all_ok = True
    for endpoint, name in endpoints:
        try:
            response = requests.get(f"http://localhost:8000{endpoint}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "error" in data:
                    print(f"{name}: {data['error']}")
                    all_ok = False
                else:
                    print(f"{name}: OK")
            else:
                print(f"{name}: HTTP {response.status_code}")
                all_ok = False
                
        except requests.exceptions.RequestException as e:
            print(f"{name}: Connection error - {e}")
            all_ok = False
        except json.JSONDecodeError:
            print(f"{name}: Invalid JSON response")
            all_ok = False
    
    return all_ok

def main():
    """Main function"""
    print("=" * 60)
    print("Z-ALPHA SECURITIES - STATUS CHECK")
    print("=" * 60)
    
    backend_ok = check_backend()
    frontend_ok = check_frontend()
    database_ok = check_database()
    
    if backend_ok:
        endpoints_ok = test_endpoints()
    else:
        endpoints_ok = False
    
    print("\n" + "=" * 60)
    print("STATUS SUMMARY")
    print("=" * 60)
    print(f"Backend: {'OK' if backend_ok else 'FAILED'}")
    print(f"Frontend: {'OK' if frontend_ok else 'FAILED'}")
    print(f"Database: {'OK' if database_ok else 'FAILED'}")
    print(f"Endpoints: {'OK' if endpoints_ok else 'FAILED'}")
    
    if all([backend_ok, frontend_ok, database_ok, endpoints_ok]):
        print("\nEVERYTHING IS WORKING PERFECTLY!")
        print("Open http://localhost:3000 to use the dashboard")
    else:
        print("\nSome components are not working properly")
        print("Run 'python start_all.py' to restart everything")
    
    print("=" * 60)

if __name__ == "__main__":
    main() 