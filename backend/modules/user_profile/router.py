"""HTTP layer for the User Profile module.

Owns portfolio CRUD endpoints, ticker search, and per-user cache
invalidation. Authentication endpoints (login/me) live in the separate
user-api service, not here.
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database.database import get_db
from services.data_service import DataService

from . import service
from .schemas import (
    PortfolioMutationResponse,
    TickerSearchResponse,
    UserPortfolioResponse,
)

router = APIRouter(tags=["user-profile"])

_data_service = DataService()


@router.get("/user-portfolio/{username}", response_model=UserPortfolioResponse)
def get_user_portfolio(username: str, db: Session = Depends(get_db)):
    try:
        return service.get_user_portfolio(db, username)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/user-portfolio/{username}", response_model=PortfolioMutationResponse)
def update_user_portfolio(
    username: str, portfolio_data: List[Dict[str, Any]], db: Session = Depends(get_db),
):
    try:
        return service.update_user_portfolio(_data_service, db, username, portfolio_data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/add-ticker/{username}")
def add_ticker_to_portfolio(
    username: str,
    ticker: str = Query(..., min_length=1, max_length=10),
    shares: int = Query(100, ge=1),
    db: Session = Depends(get_db),
):
    result = service.add_ticker(_data_service, db, username, ticker, shares)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.delete("/remove-ticker/{username}")
def remove_ticker_from_portfolio(
    username: str,
    ticker: str = Query(..., min_length=1, max_length=10),
    db: Session = Depends(get_db),
):
    result = service.remove_ticker(_data_service, db, username, ticker)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/ticker-search", response_model=TickerSearchResponse)
def search_tickers(query: str = Query(..., min_length=1, max_length=10)):
    return service.search_tickers(_data_service, query)


@router.post("/invalidate-user/{username}")
def invalidate_user(username: str):
    return service.invalidate_user_cache(_data_service, username)
