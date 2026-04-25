"""Response shape for the Stress Testing module.

Bundles two concerns into one payload (matches the frontend contract):
  - market_regime: vol/correlation/momentum + radar + label
  - scenarios: per-scenario PnL + max drawdown, plus excluded scenarios
"""

from __future__ import annotations

from typing import List

from pydantic import BaseModel


class RegimeRadar(BaseModel):
    volatility: float
    correlation: float
    momentum: float


class MarketRegimeBlock(BaseModel):
    label: str
    volatility_pct: float
    correlation: float
    momentum_pct: float
    radar: RegimeRadar


class ScenarioResult(BaseModel):
    name: str
    start: str
    end: str
    days: int
    weight_coverage_pct: float
    return_pct: float
    max_drawdown_pct: float


class ScenarioExcluded(BaseModel):
    name: str
    reason: str


class ScenariosBlock(BaseModel):
    scenarios_analyzed: int
    scenarios_excluded: int
    results: List[ScenarioResult]
    excluded: List[ScenarioExcluded]


class StressTestingResponse(BaseModel):
    market_regime: MarketRegimeBlock
    scenarios: ScenariosBlock
