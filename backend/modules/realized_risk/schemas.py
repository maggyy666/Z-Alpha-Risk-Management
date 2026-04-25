"""Response shapes for the Realized Risk module endpoints.

Mirrors the frontend's RealizedMetricsResponse / RollingMetricsResponse
interfaces -- TypeScript and Python serializers stay in lock-step.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class RealizedMetricRow(BaseModel):
    ticker: str
    ann_return_pct: float
    volatility_pct: float
    sharpe_ratio: float
    sortino_ratio: float
    skewness: float
    kurtosis: float
    max_drawdown_pct: float
    var_95_pct: float
    cvar_95_pct: float
    hit_ratio_pct: float
    beta_ndx: float
    up_capture_ndx_pct: float
    down_capture_ndx_pct: float
    tracking_error_pct: float
    information_ratio: float


class CommonDateRange(BaseModel):
    start_date: str
    end_date: str
    total_days: int


class RealizedMetricsResponse(BaseModel):
    metrics: List[RealizedMetricRow]
    common_date_range: Optional[CommonDateRange] = None


class RollingDataset(BaseModel):
    ticker: str
    dates: List[str]
    values: List[Optional[float]]


class RollingMetricsResponse(BaseModel):
    datasets: List[RollingDataset]
    metric: str
    window: int
    common_date_range: Optional[CommonDateRange] = None
