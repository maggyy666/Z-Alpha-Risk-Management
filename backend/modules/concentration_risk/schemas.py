"""Response shape for the Concentration Risk module."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class PortfolioPosition(BaseModel):
    ticker: str
    shares: float
    price: float
    market_value: float
    weight: float
    weight_frac: float
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[float] = None


class ConcentrationMetrics(BaseModel):
    largest_position: float
    top_3_concentration: float
    top_5_concentration: float
    top_10_concentration: float
    herfindahl_index: float
    effective_positions: float


class SectorConcentration(BaseModel):
    sectors: List[str]
    weights: List[float]
    hhi: float
    effective_sectors: float


class MarketCapConcentration(BaseModel):
    categories: List[str]
    weights: List[float]
    details: Dict[str, List[Dict[str, Any]]]
    hhi: float
    effective_categories: float


class ConcentrationRiskResponse(BaseModel):
    portfolio_data: List[PortfolioPosition]
    concentration_metrics: ConcentrationMetrics
    sector_concentration: SectorConcentration
    market_cap_concentration: MarketCapConcentration
    total_market_value: float
