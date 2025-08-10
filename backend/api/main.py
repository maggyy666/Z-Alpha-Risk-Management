"""FastAPI application exposing portfolio risk analytics endpoints.

This API provides authentication, portfolio initialization, and read-only
analytics (volatility, factor exposures, concentration, stress tests,
covariance matrices, rolling metrics, liquidity, and summary). It relies on
database-backed services and is intended for local development/testing.
"""

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database.database import get_db, engine, Base
from services.data_service import DataService
from database.models.user import User
from database.models.portfolio import Portfolio
from database.models.ticker_data import TickerData
from database.models.ticker import TickerInfo
from typing import List, Dict, Any
from pydantic import BaseModel
import uvicorn

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    message: str
    username: str = None

class PortfolioRequest(BaseModel):
    username: str
    tickers: List[str]

class PortfolioResponse(BaseModel):
    success: bool
    message: str
    tickers: List[str] = []

class SessionResponse(BaseModel):
    logged_in: bool
    username: str = None
    email: str = None

Base.metadata.create_all(bind=engine)

app = FastAPI(title="IBKR Portfolio API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

data_service = DataService()


@app.get("/")
def read_root():
    return {"message": "IBKR Portfolio API"}

@app.post("/login", response_model=LoginResponse)
def login(login_request: LoginRequest, db: Session = Depends(get_db)):
    """Login endpoint for landing page"""
    try:
        # Check if user exists by username OR email
        user = db.query(User).filter(
            (User.username == login_request.username) | 
            (User.email == login_request.username)
        ).first()
        
        if not user:
            return LoginResponse(
                success=False,
                message="Invalid email or password"
            )
        
        # Check password (simple comparison for now)
        if user.password != login_request.password:
            return LoginResponse(
                success=False,
                message="Invalid email or password"
            )
        
        return LoginResponse(
            success=True,
            message="Login successful",
            username=user.username
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/session", response_model=SessionResponse)
def get_session(username: str = "admin", db: Session = Depends(get_db)):
    """Get current session info"""
    try:
        user = db.query(User).filter(User.username == username).first()
        
        if not user:
            return SessionResponse(
                logged_in=False,
                username=None,
                email=None
            )
        
        return SessionResponse(
            logged_in=True,
            username=user.username,
            email=user.email
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/initialize-portfolio")
def initialize_portfolio(db: Session = Depends(get_db)):
    """Initialize portfolio with sample data for admin user"""
    try:
        # Get admin user's portfolio tickers
        tickers = data_service.get_user_portfolio_tickers(db, "admin")
        
        if not tickers:
            raise HTTPException(status_code=404, detail="Admin user or portfolio not found")
        
        # Inject sample data for each ticker
        for symbol in tickers:
            success = data_service.inject_sample_data(db, symbol)
            if success:
                print(f"Injected sample data for {symbol}")
            else:
                print(f"Failed to inject sample data for {symbol}")
        
        return {
            "message": f"Initialized {len(tickers)} tickers",
            "tickers": tickers
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/fetch-data/{symbol}")
def fetch_historical_data(symbol: str, db: Session = Depends(get_db)):
    """Fetch historical data for a specific symbol"""
    try:
        success = data_service.fetch_and_store_historical_data(db, symbol)
        if success:
            return {"message": f"Successfully fetched data for {symbol}"}
        else:
            raise HTTPException(status_code=400, detail=f"Failed to fetch data for {symbol}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/volatility-data")
def get_volatility_data(
    forecast_model: str = 'EWMA (5D)',
    vol_floor_annual_pct: float = 8.0,
    risk_free_annual: float = 0.0,
    username: str = "admin",
    db: Session = Depends(get_db)
):
    """Get volatility data for user's portfolio tickers"""
    try:
        # Use database data directly (IBKR Client Portal not available)
        portfolio_data = data_service.get_portfolio_volatility_data(
            db, username, forecast_model, vol_floor_annual_pct, risk_free_annual
        )
        return {"portfolio_data": portfolio_data, "source": "database"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/factor-exposure-data")
def get_factor_exposure_data(username: str = "admin", db: Session = Depends(get_db)):
    """Get factor exposure data for portfolio analysis"""
    try:
        # Get factor exposure data from database
        factor_data = data_service.get_factor_exposure_data(db, username)
        return factor_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/concentration-risk-data")
def get_concentration_risk_data(username: str = "admin", db: Session = Depends(get_db)):
    """Get concentration risk data for portfolio analysis"""
    try:
        # Get concentration risk data from database
        concentration_data = data_service.get_concentration_risk_data(db, username)
        return concentration_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/risk-scoring")
def risk_scoring(username: str = "admin", db: Session = Depends(get_db)):
    """Get risk scoring data for portfolio analysis"""
    try:
        data = data_service.get_risk_scoring(db, username)
        if "error" in data:
            raise HTTPException(status_code=400, detail=data["error"])
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stress-testing")
def stress_testing(username: str = "admin", db: Session = Depends(get_db)):
    """Get stress testing data for portfolio analysis"""
    try:
        data = data_service.get_stress_testing(db, username)
        if "error" in data:
            raise HTTPException(status_code=400, detail=data["error"])
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/covariance-matrix")
def get_covariance_matrix(
    tickers: str = Query(..., description="Comma-separated list of tickers"),
    vol_model: str = 'EWMA (5D)',
    username: str = "admin",
    db: Session = Depends(get_db)
):
    """Get covariance matrix for specified tickers"""
    try:
        ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]
        if not ticker_list:
            raise HTTPException(status_code=400, detail="No tickers specified")
        
        cov_matrix = data_service.build_covariance_matrix(db, ticker_list, vol_model)
        return {"cov_matrix": cov_matrix.tolist()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/forecast-risk-contribution")
def get_forecast_risk_contribution(
    vol_model: str = 'EWMA (5D)',
    tickers: str = Query("", description="Comma-separated list of tickers (empty = all portfolio)"),
    include_portfolio_bar: bool = Query(True, description="Include PORTFOLIO as first bar in charts"),
    username: str = "admin",
    db: Session = Depends(get_db)
):
    """Get Forecast Risk Contribution data for portfolio"""
    try:
        # Parse tickers from comma-separated string
        ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()] if tickers else []
        
        data = data_service.get_forecast_risk_contribution(db, username, vol_model, ticker_list, include_portfolio_bar)
        if "error" in data:
            raise HTTPException(status_code=400, detail=data["error"])
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.post("/clear-cache")
def clear_cache(pattern: str = None):
    """Clear cache entries matching pattern"""
    try:
        data_service._clear_cache(pattern)
        return {"message": f"Cache cleared for pattern: {pattern or 'all'}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/invalidate-user/{username}")
def invalidate_user(username: str):
    """Invalidate all cache entries for a specific user"""
    try:
        data_service._clear_cache(f"*{username}*")
        return {"ok": True, "message": f"Cache invalidated for user: {username}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/forecast-metrics")
def get_forecast_metrics(
    conf_level: float = 0.95,
    username: str = "admin",
    db: Session = Depends(get_db)
):
    """Get forecast metrics for all portfolio tickers"""
    try:
        data = data_service.get_forecast_metrics(db, username, conf_level)
        if "error" in data:
            raise HTTPException(status_code=400, detail=data["error"])
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rolling-forecast")
def get_rolling_forecast(
    model: str = Query("EWMA (5D)"),
    window: int = Query(21, ge=5, le=252),
    tickers: str = Query("PORTFOLIO"),   # CSV in URL
    username: str = "admin",
    db: Session = Depends(get_db)
):
    """Get rolling forecast data for selected tickers"""
    try:
        # Parse tickers from comma-separated string
        ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]
        if not ticker_list:
            raise HTTPException(status_code=400, detail="No tickers specified")
        
        data = data_service.get_rolling_forecast(db, ticker_list, model, window, username)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/latest-factor-exposures")
def get_latest_factor_exposures(username: str = "admin", db: Session = Depends(get_db)):
    """Get latest factor exposures table data"""
    try:
        data = data_service.get_latest_factor_exposures(db, username)
        if "error" in data:
            raise HTTPException(status_code=400, detail=data["error"])
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/portfolio-summary")
def get_portfolio_summary(username: str = "admin", db: Session = Depends(get_db)):
    """Get portfolio summary data"""
    try:
        data = data_service.get_portfolio_summary(db, username)
        if "error" in data:
            raise HTTPException(status_code=400, detail=data["error"])
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/user-portfolio/{username}")
def get_user_portfolio(username: str, db: Session = Depends(get_db)):
    """Get user's portfolio data"""
    try:
        # Get user first
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(status_code=404, detail=f"User {username} not found")
        
        # Get portfolio from database
        portfolio_items = db.query(Portfolio).filter(Portfolio.user_id == user.id).all()
        
        # Get ticker info for each item
        portfolio_data = []
        total_market_value = 0
        
        for item in portfolio_items:
            ticker_info = db.query(TickerInfo).filter(TickerInfo.symbol == item.ticker_symbol).first()
            ticker_data = db.query(TickerData).filter(TickerData.ticker_symbol == item.ticker_symbol).order_by(TickerData.date.desc()).first()
            
            if ticker_data:
                market_value = ticker_data.close_price * item.shares  # Use actual shares from database
                total_market_value += market_value
                
                portfolio_data.append({
                    "ticker": item.ticker_symbol,
                    "shares": item.shares,  # Use actual shares from database
                    "price": ticker_data.close_price,
                    "market_value": market_value,
                    "sector": ticker_info.sector if ticker_info else "Unknown",
                    "industry": ticker_info.industry if ticker_info else "Unknown"
                })
        
        return {
            "username": username,
            "portfolio_items": portfolio_data,
            "total_market_value": total_market_value,
            "total_positions": len(portfolio_data)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/user-portfolio/{username}")
def update_user_portfolio(username: str, portfolio_data: List[dict], db: Session = Depends(get_db)):
    """Update user's portfolio data"""
    try:
        # Get user first
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(status_code=404, detail=f"User {username} not found")
        
        # Get existing portfolio items
        existing_items = db.query(Portfolio).filter(Portfolio.user_id == user.id).all()
        existing_tickers = {item.ticker_symbol: item for item in existing_items}
        
        updated_count = 0
        new_count = 0
        
        # Update or add portfolio items
        for item in portfolio_data:
            if 'ticker' in item and 'shares' in item:
                ticker = item['ticker']
                shares = int(item['shares'])
                
                if ticker in existing_tickers:
                    # Update existing item
                    existing_tickers[ticker].shares = shares
                    updated_count += 1
                else:
                    # Add new item
                    portfolio_item = Portfolio(
                        user_id=user.id,
                        ticker_symbol=ticker,
                        shares=shares
                    )
                    db.add(portfolio_item)
                    new_count += 1
        
        db.commit()
        
        # Clear cache for this user's portfolio data
        print(f"🔄 Clearing cache for user {username} after portfolio update...")
        data_service._clear_cache(f"*{username}*")
        print(f"✅ Cache cleared for user {username} after portfolio update")
        
        # Update JSON file
        import json
        import os
        
        # Handle both cases: running from project root or from backend/
        json_file = f"../data/{username}_portfolio.json"
        if not os.path.exists(json_file):
            json_file = f"data/{username}_portfolio.json"
        
        # Get all current portfolio items (including existing ones)
        all_items = db.query(Portfolio).filter(Portfolio.user_id == user.id).all()
        
        # Prepare data for JSON file
        json_data = []
        for item in all_items:
            json_data.append({
                "ticker": item.ticker_symbol,
                "shares": item.shares
            })
        
        # Write to JSON file
        with open(json_file, 'w') as f:
            json.dump(json_data, f, indent=2)
        
        return {
            "success": True,
            "message": f"Portfolio updated for {username}",
            "updated_items": updated_count,
            "new_items": new_count,
            "total_items": len(json_data)
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/realized-metrics")
def get_realized_metrics(username: str = "admin", db: Session = Depends(get_db)):
    """Get realized risk metrics for portfolio and individual tickers"""
    try:
        data = data_service.get_realized_metrics(db, username)
        if "error" in data:
            raise HTTPException(status_code=400, detail=data["error"])
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rolling-metric")
def get_rolling_metrics(
    metric: str = "vol",
    window: int = 21,
    tickers: str = "PORTFOLIO",
    username: str = "admin",
    db: Session = Depends(get_db)
):
    """Get rolling metric data for charting"""
    try:
        # Parse tickers from comma-separated string
        ticker_list = [t.strip() for t in tickers.split(',') if t.strip()]
        data = data_service.get_rolling_metric(db, metric=metric, window=window, tickers=ticker_list, username=username)
        if "error" in data:
            raise HTTPException(status_code=400, detail=data["error"])
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Liquidity endpoints
@app.get("/liquidity-overview")
def liquidity_overview(username: str = "admin", db: Session = Depends(get_db)):
    """Get liquidity overview for portfolio"""
    return data_service.get_liquidity_metrics(db, username)

@app.get("/liquidity-volume-analysis")
def liquidity_volume_analysis(username: str = "admin", db: Session = Depends(get_db)):
    """Get liquidity volume analysis for portfolio"""
    return data_service.get_volume_distribution(db, username)

@app.get("/liquidity-alerts")
def liquidity_alerts(username: str = "admin", db: Session = Depends(get_db)):
    """Get liquidity alerts for portfolio"""
    return data_service.get_liquidity_alerts(db, username)

@app.get("/ticker-search")
def search_tickers(query: str = Query(..., min_length=1, max_length=10)):
    """Search for tickers using yfinance"""
    try:
        suggestions = data_service.search_tickers(query)
        return {"suggestions": suggestions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/add-ticker/{username}")
def add_ticker_to_portfolio(
    username: str, 
    ticker: str = Query(..., min_length=1, max_length=10),
    shares: int = Query(100, ge=1),
    db: Session = Depends(get_db)
):
    """Add ticker to user's portfolio with data fetching"""
    try:
        result = data_service.add_ticker_to_portfolio(db, username, ticker, shares)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/remove-ticker/{username}")
def remove_ticker_from_portfolio(
    username: str,
    ticker: str = Query(..., min_length=1, max_length=10),
    db: Session = Depends(get_db)
):
    """Remove ticker from user's portfolio"""
    try:
        result = data_service.remove_ticker_from_portfolio(db, username, ticker)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 