"""HTTP layer for the Stress Testing module."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.database import get_db
from services.data_service import DataService

from . import service
from .schemas import StressTestingResponse

router = APIRouter(tags=["stress-testing"])

_data_service = DataService()


@router.get("/stress-testing", response_model=StressTestingResponse)
def stress_testing(username: str = "admin", db: Session = Depends(get_db)):
    return service.get_stress_testing(_data_service, db, username)
