"""Response shapes for the Forecast Risk module."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class ForecastRiskContributionResponse(BaseModel):
    tickers: List[str]
    marginal_rc_pct: List[float]
    total_rc_pct: List[float]
    weights_pct: List[float]
    portfolio_vol: float
    portfolio_vol_pct: Optional[float] = None
    vol_model: str


class ForecastMetricRow(BaseModel):
    ticker: str
    ewma5_pct: float
    ewma20_pct: float
    garch_vol_pct: float
    egarch_vol_pct: float
    var_pct: float
    cvar_pct: float
    var_usd: float
    cvar_usd: float


class ForecastMetricsResponse(BaseModel):
    metrics: List[ForecastMetricRow]
    conf_level: float
