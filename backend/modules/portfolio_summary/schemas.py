"""Response shape for GET /portfolio-summary.

Mirrors the frontend's PortfolioSummaryResponse interface exactly so the
TypeScript client and Python serializer stay in lock-step.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class RiskScoreSummary(BaseModel):
    overall_score: float
    risk_level: str   # "LOW" | "MEDIUM" | "HIGH"
    highest_risk_component: str
    highest_risk_percentage: float
    high_risk_components_count: int


class TopRiskContributor(BaseModel):
    ticker: str
    vol_contribution_pct: float


class PortfolioOverview(BaseModel):
    total_market_value: float
    total_positions: int
    largest_position: float
    top_3_concentration: float
    volatility_egarch: float
    cvar_percentage: float
    cvar_usd: float
    top_risk_contributor: TopRiskContributor


class PortfolioPosition(BaseModel):
    ticker: str
    weight: float
    shares: float
    market_value: float
    sector: Optional[str] = None


class PortfolioSummaryFlags(BaseModel):
    high_vol: Optional[bool] = None
    high_risk_score: Optional[bool] = None
    high_cvar: Optional[bool] = None


class PortfolioSummaryResponse(BaseModel):
    risk_score: RiskScoreSummary
    portfolio_overview: PortfolioOverview
    portfolio_positions: List[PortfolioPosition]
    flags: PortfolioSummaryFlags
