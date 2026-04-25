"""Response shapes for the Liquidity Risk module."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class LiquidityOverviewBlock(BaseModel):
    overall_score: float
    risk_level: str
    estimated_liquidation_time: str


class VolumeAnalysisBlock(BaseModel):
    avg_volume_global: Optional[float] = None
    total_portfolio_volume: Optional[float] = None
    volume_weighted_avg: Optional[float] = None


class PositionDetail(BaseModel):
    ticker: str
    shares: float
    market_value: float
    weight_pct: float
    avg_volume: Optional[float] = None
    current_volume: Optional[float] = None
    spread_pct: Optional[float] = None
    volume_category: Optional[str] = None
    volume_score: Optional[float] = None
    liquidity_score: Optional[float] = None
    liq_days: Optional[float] = None


class LiquidityAlert(BaseModel):
    severity: str
    text: str


class LiquidityOverviewResponse(BaseModel):
    overview: LiquidityOverviewBlock
    distribution: Dict[str, Any]
    volume_analysis: VolumeAnalysisBlock
    position_details: List[PositionDetail]
    alerts: List[LiquidityAlert]


class LiquidityAlertsResponse(BaseModel):
    alerts: List[LiquidityAlert]
