"""HTTP layer for the Factor Exposure module."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.database import get_db
from services.data_service import DataService

from . import service
from .schemas import FactorExposureResponse, LatestFactorExposuresResponse

router = APIRouter(tags=["factor-exposure"])

_data_service = DataService()


@router.get("/factor-exposure-data", response_model=FactorExposureResponse)
def factor_exposure_data(username: str = "admin", db: Session = Depends(get_db)):
    return service.get_factor_exposure_data(_data_service, db, username)


@router.get("/latest-factor-exposures", response_model=LatestFactorExposuresResponse)
def latest_factor_exposures(username: str = "admin", db: Session = Depends(get_db)):
    payload = service.get_latest_factor_exposures(_data_service, db, username)
    if "error" in payload:
        raise HTTPException(status_code=400, detail=payload["error"])
    return payload
