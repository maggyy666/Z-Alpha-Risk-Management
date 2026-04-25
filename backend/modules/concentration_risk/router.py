"""HTTP layer for the Concentration Risk module."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.database import get_db
from services.data_service import DataService

from . import service
from .schemas import ConcentrationRiskResponse

router = APIRouter(tags=["concentration-risk"])

_data_service = DataService()


@router.get("/concentration-risk-data", response_model=ConcentrationRiskResponse)
def concentration_risk_data(username: str = "admin", db: Session = Depends(get_db)):
    payload = service.get_concentration_risk_data(_data_service, db, username)
    if "error" in payload:
        raise HTTPException(status_code=400, detail=payload["error"])
    return payload
