"""HTTP layer for the Realized Risk module."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.database import get_db
from services.data_service import DataService

from . import service
from .schemas import RealizedMetricsResponse, RollingMetricsResponse

router = APIRouter(tags=["realized-risk"])

_data_service = DataService()


@router.get("/realized-metrics", response_model=RealizedMetricsResponse)
def get_realized_metrics(username: str = "admin", db: Session = Depends(get_db)):
    payload = service.get_realized_metrics(_data_service, db, username)
    if "error" in payload:
        raise HTTPException(status_code=400, detail=payload["error"])
    return payload


@router.get("/rolling-metric", response_model=RollingMetricsResponse)
def get_rolling_metric(
    metric: str = "vol",
    window: int = 21,
    tickers: str = "PORTFOLIO",
    username: str = "admin",
    db: Session = Depends(get_db),
):
    ticker_list = [t.strip() for t in tickers.split(",") if t.strip()]
    payload = service.get_rolling_metric(
        _data_service, db,
        metric=metric, window=window, tickers=ticker_list, username=username,
    )
    if "error" in payload:
        raise HTTPException(status_code=400, detail=payload["error"])
    return payload
