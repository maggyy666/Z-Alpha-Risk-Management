"""Response shapes for the Factor Exposure module."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class FactorExposurePoint(BaseModel):
    date: str
    ticker: str
    factor: str
    beta: float


class R2Point(BaseModel):
    date: str
    ticker: str
    r2: float


class CommonDateRange(BaseModel):
    start_date: str
    end_date: str
    total_days: int


class FactorExposureResponse(BaseModel):
    factor_exposures: List[FactorExposurePoint]
    r2_data: List[R2Point]
    available_factors: List[str]
    available_tickers: List[str]
    common_date_range: Optional[CommonDateRange] = None


class LatestFactorExposuresResponse(BaseModel):
    as_of: str
    factors: List[str]
    # Each row: {"ticker": str, <factor_name>: float, ...}
    data: List[Dict[str, Any]]
