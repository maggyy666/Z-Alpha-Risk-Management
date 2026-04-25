"""FastAPI application exposing portfolio risk analytics endpoints.

This API provides authentication, portfolio initialization, and read-only
analytics (volatility, factor exposures, concentration, stress tests,
covariance matrices, rolling metrics, liquidity, and summary). It relies on
database-backed services and is intended for local development/testing.
"""

import logging
from typing import Any, Dict, List

import uvicorn
from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

import jwt as _jwt

from database.database import Base, engine, get_db
from database.models.portfolio import Portfolio
from database.models.ticker import TickerInfo
from database.models.ticker_data import TickerData
from database.models.user import User
from logging_config import setup_logging
from modules.concentration_risk import router as concentration_risk_router
from modules.factor_exposure import router as factor_exposure_router
from modules.forecast_risk import router as forecast_risk_router
from modules.liquidity_risk import router as liquidity_risk_router
from modules.portfolio_summary import router as portfolio_summary_router
from modules.realized_risk import router as realized_risk_router
from modules.stress_testing import router as stress_testing_router
from modules.user_profile import router as user_profile_router
from modules.volatility_sizing import router as volatility_sizing_router
from services.data_service import DataService

setup_logging()
logger = logging.getLogger(__name__)

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

# Modular routers (extracted from this monolith one-by-one).
app.include_router(portfolio_summary_router)
app.include_router(realized_risk_router)
app.include_router(forecast_risk_router)
app.include_router(factor_exposure_router)
app.include_router(stress_testing_router)
app.include_router(concentration_risk_router)
app.include_router(liquidity_risk_router)
app.include_router(volatility_sizing_router)
app.include_router(user_profile_router)


@app.get("/")
def read_root():
    return {"message": "IBKR Portfolio API"}


@app.get("/auth/verify")
def verify_jwt(authorization: str | None = Header(default=None), db: Session = Depends(get_db)):
    """Validate a JWT issued by user-api. Proves the shared-secret contract
    between the two services. Not wired into other endpoints yet -- login
    still works via /login query-param fallback."""
    from auth.jwt_tokens import decode

    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    token = authorization.split(None, 1)[1].strip()
    try:
        claims = decode(token)
    except _jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except _jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.query(User).filter(User.username == claims.get("sub")).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return {"username": user.username, "email": user.email}

@app.post("/login", response_model=LoginResponse)
def login(login_request: LoginRequest, db: Session = Depends(get_db)):
    """Login endpoint. Accepts username OR email in the username field,
    verifies bcrypt hash. Responses are generic to avoid user-enumeration."""
    from auth.passwords import verify_password
    try:
        user = db.query(User).filter(
            (User.username == login_request.username) |
            (User.email == login_request.username)
        ).first()

        if not user or not verify_password(login_request.password, user.password_hash):
            return LoginResponse(
                success=False,
                message="Invalid username or password"
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
                logger.info(f"Injected sample data for {symbol}")
            else:
                logger.info(f"Failed to inject sample data for {symbol}")
        
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


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 
