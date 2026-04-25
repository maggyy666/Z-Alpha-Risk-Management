"""HTTP layer for the Liquidity Risk module."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.database import get_db
from services.data_service import DataService

from . import service

router = APIRouter(tags=["liquidity-risk"])

_data_service = DataService()


@router.get("/liquidity-overview")
def liquidity_overview(username: str = "admin", db: Session = Depends(get_db)):
    return service.get_liquidity_overview(_data_service, db, username)


@router.get("/liquidity-volume-analysis")
def liquidity_volume_analysis(username: str = "admin", db: Session = Depends(get_db)):
    return service.get_volume_distribution(_data_service, db, username)


@router.get("/liquidity-alerts")
def liquidity_alerts(username: str = "admin", db: Session = Depends(get_db)):
    return service.get_liquidity_alerts(_data_service, db, username)
