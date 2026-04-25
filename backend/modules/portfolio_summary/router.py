"""HTTP layer for the Portfolio Summary module."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.database import get_db
from services.data_service import DataService

from .schemas import PortfolioSummaryResponse
from .service import build_portfolio_summary

router = APIRouter(tags=["portfolio-summary"])

_data_service = DataService()


@router.get("/portfolio-summary", response_model=PortfolioSummaryResponse)
def get_portfolio_summary(username: str = "admin", db: Session = Depends(get_db)):
    payload = build_portfolio_summary(_data_service, db, username)
    if "error" in payload:
        raise HTTPException(status_code=400, detail=payload["error"])
    return payload
