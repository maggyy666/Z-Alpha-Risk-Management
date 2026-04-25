"""HTTP layer for the Forecast Risk module."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database.database import get_db
from services.data_service import DataService

from . import service
from .schemas import ForecastMetricsResponse, ForecastRiskContributionResponse

router = APIRouter(tags=["forecast-risk"])

_data_service = DataService()


@router.get("/forecast-risk-contribution", response_model=ForecastRiskContributionResponse)
def forecast_risk_contribution(
    vol_model: str = "EWMA (5D)",
    tickers: str = "",
    include_portfolio_bar: bool = True,
    username: str = "admin",
    db: Session = Depends(get_db),
):
    ticker_list = [t.strip() for t in tickers.split(",") if t.strip()] or None
    payload = service.get_forecast_risk_contribution(
        _data_service, db, username=username,
        vol_model=vol_model, tickers=ticker_list,
        include_portfolio_bar=include_portfolio_bar,
    )
    if "error" in payload:
        raise HTTPException(status_code=400, detail=payload["error"])
    return payload


@router.get("/forecast-metrics", response_model=ForecastMetricsResponse)
def forecast_metrics(
    username: str = "admin",
    conf_level: float = Query(default=0.95, ge=0.5, le=0.999),
    db: Session = Depends(get_db),
):
    payload = service.get_forecast_metrics(_data_service, db, username, conf_level)
    if "error" in payload:
        raise HTTPException(status_code=400, detail=payload["error"])
    return payload


@router.get("/rolling-forecast")
def rolling_forecast(
    model: str = Query("EWMA (5D)"),
    window: int = Query(21, ge=5, le=252),
    tickers: str = Query("PORTFOLIO"),
    username: str = "admin",
    db: Session = Depends(get_db),
):
    ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]
    if not ticker_list:
        raise HTTPException(status_code=400, detail="No tickers specified")
    return service.get_rolling_forecast(_data_service, db, ticker_list, model, window, username)
