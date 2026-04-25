"""HTTP layer for the Volatility-Based Sizing module."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.database import get_db
from services.data_service import DataService

from . import service

router = APIRouter(tags=["volatility-sizing"])

_data_service = DataService()


@router.get("/volatility-data")
def volatility_data(
    forecast_model: str = "EWMA (5D)",
    vol_floor_annual_pct: float = 8.0,
    risk_free_annual: float = 0.0,
    username: str = "admin",
    db: Session = Depends(get_db),
):
    portfolio_data = service.get_portfolio_volatility_data(
        _data_service, db, username,
        forecast_model, vol_floor_annual_pct, risk_free_annual,
    )
    return {"portfolio_data": portfolio_data, "source": "database"}
