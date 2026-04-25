"""Response shape for the Volatility-Based Sizing module."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class PortfolioVolatilityRow(BaseModel):
    symbol: str
    forecast_volatility_pct: float
    last_price: float
    sharpe_ratio: float
    shares: float
    is_static: bool = False
    current_mv: Optional[float] = None
    current_weight_pct: Optional[float] = None
    adj_volatility_weight_pct: Optional[float] = None
    target_mv: Optional[float] = None
    delta_mv: Optional[float] = None
    delta_shares: Optional[int] = None


class VolatilitySizingResponse(BaseModel):
    portfolio_data: List[PortfolioVolatilityRow]
    source: str = "database"
