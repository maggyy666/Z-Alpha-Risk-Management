from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database.database import get_db, engine, Base
from services.data_service import DataService
from database.models.user import User
from database.models.portfolio import Portfolio
from database.models.ticker_data import TickerData
# from services.ibkr_client_portal import PortfolioDataService  # Not needed for now
from typing import List, Dict, Any
import uvicorn

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="IBKR Portfolio API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React app
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
data_service = DataService()
# portfolio_service = PortfolioDataService()  # Not needed for now

# Portfolio symbols (fallback)
# Portfolio symbols are now managed through user portfolios

@app.get("/")
def read_root():
    return {"message": "IBKR Portfolio API"}

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
                print(f"✅ Injected sample data for {symbol}")
            else:
                print(f"❌ Failed to inject sample data for {symbol}")
        
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
    username: str = "admin",
    db: Session = Depends(get_db)
):
    """Get Forecast Risk Contribution data for portfolio"""
    try:
        data = data_service.get_forecast_risk_contribution(db, username, vol_model)
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
    tickers: str = Query("PORTFOLIO"),   # CSV w URL-u
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
        return {"model": model, "window": window, "data": data}
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
    """Get comprehensive portfolio summary data for dashboard"""
    try:
        data = data_service.get_portfolio_summary(db, username)
        if "error" in data:
            raise HTTPException(status_code=400, detail=data["error"])
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 