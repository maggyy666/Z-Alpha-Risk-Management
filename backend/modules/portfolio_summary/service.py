"""Portfolio Summary -- dashboard aggregator.

This module owns the `/portfolio-summary` endpoint. It does not compute
analytics itself; it composes results from four upstream modules and
applies the dashboard-specific rules (risk-level bucketing, alert flags,
top contributor selection).

Upstream dependencies (all reached through the DataService facade):
  - risk_score        -> overall score, component contributions
  - concentration     -> total market value, position weights, sector data
  - forecast_risk     -> EGARCH portfolio volatility, per-ticker rc%
  - forecast_metrics  -> per-ticker CVaR USD (summed for portfolio total)
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Tuple

import numpy as np
from sqlalchemy.orm import Session

from modules.forecast_risk import service as forecast_risk_service

logger = logging.getLogger(__name__)

# Risk-level bucketing on the 0-100 overall score.
LEVEL_LOW_MAX = 33.0
LEVEL_MEDIUM_MAX = 66.0

# Flag thresholds. Defensive: the upstream metrics can occasionally blow up
# (e.g. EGARCH on a freshly listed ticker) -- we surface the spike to the UI
# rather than silently clip.
FLAG_HIGH_VOL_PCT = 3.0          # portfolio_vol > 3.0 (~300%)
FLAG_HIGH_RISK_SCORE_RAW = 1.0   # overall component score > 1.0 (>100%)
FLAG_HIGH_CVAR_PCT = -10.0       # total CVaR % below -10%

# Risk-contribution component is "high" if it crosses this share of total.
HIGH_COMPONENT_PCT_THRESHOLD = 25.0


def _risk_level(overall_score: float) -> str:
    if overall_score <= LEVEL_LOW_MAX:
        return "LOW"
    if overall_score <= LEVEL_MEDIUM_MAX:
        return "MEDIUM"
    return "HIGH"


def _top_risk_contributor(forecast_contribution: Dict[str, Any]) -> Tuple[str, float]:
    """Pick the position with the largest total_rc_pct, skipping the
    synthetic 'PORTFOLIO' aggregate row if it sits at index 0."""
    tickers = forecast_contribution.get("tickers", [])
    trc = forecast_contribution.get("total_rc_pct", [])

    start = 1 if tickers and tickers[0] == "PORTFOLIO" else 0
    if trc and len(trc) > start:
        idx_rel = int(np.argmax(trc[start:]))
        idx = start + idx_rel
        return tickers[idx], round(float(trc[idx]), 1)
    return "N/A", 0.0


def _safe_risk_data(data_service, db: Session, username: str) -> Dict[str, Any]:
    risk = data_service.get_risk_scoring(db, username)
    if "error" in risk:
        logger.warning("[portfolio_summary] risk_scoring failed: %s", risk["error"])
        return {
            "component_scores": {"overall": 0.5},
            "risk_contribution_pct": {
                "market": 25.0, "concentration": 25.0,
                "volatility": 25.0, "liquidity": 25.0,
            },
        }
    return risk


def _safe_concentration(data_service, db: Session, username: str) -> Dict[str, Any]:
    conc = data_service.get_concentration_risk_data(db, username)
    if "error" in conc:
        logger.warning("[portfolio_summary] concentration failed: %s", conc["error"])
        return {
            "total_market_value": 0,
            "portfolio_data": [],
            "concentration_metrics": {"largest_position": 0, "top_3_concentration": 0},
        }
    return conc


def _safe_forecast_contribution(data_service, db: Session, username: str) -> Dict[str, Any]:
    fc = forecast_risk_service.get_forecast_risk_contribution(
        data_service, db, username=username, vol_model="EGARCH",
    )
    if "error" in fc:
        logger.warning("[portfolio_summary] forecast_risk_contribution failed: %s", fc["error"])
        return {"portfolio_vol": 0.15, "tickers": ["N/A"], "marginal_rc_pct": [0.0]}
    return fc


def _safe_forecast_metrics(data_service, db: Session, username: str) -> Dict[str, Any]:
    fm = forecast_risk_service.get_forecast_metrics(data_service, db, username)
    if "error" in fm:
        logger.warning("[portfolio_summary] forecast_metrics failed: %s", fm["error"])
        return {"metrics": []}
    return fm


def build_portfolio_summary(data_service, db: Session, username: str) -> Dict[str, Any]:
    """Compose the dashboard payload from the four upstream analytics modules.

    Returns either the populated payload dict or `{"error": str}` -- the
    router translates the error case into an HTTP 400.
    """
    try:
        risk_data = _safe_risk_data(data_service, db, username)
        conc_data = _safe_concentration(data_service, db, username)
        forecast_contribution = _safe_forecast_contribution(data_service, db, username)
        forecast_metrics = _safe_forecast_metrics(data_service, db, username)

        total_market_value = conc_data.get("total_market_value", 1)
        total_cvar_usd = sum(item.get("cvar_usd", 0) for item in forecast_metrics.get("metrics", []))
        total_cvar_pct = (total_cvar_usd / total_market_value * 100) if total_market_value > 0 else 0

        overall_score_raw = risk_data.get("component_scores", {}).get("overall", 0) * 100
        overall_score = max(0.0, min(overall_score_raw, 100.0))
        if overall_score != overall_score_raw:
            logger.warning("[portfolio_summary] overall_score %.2f clipped to [0,100]", overall_score_raw)

        risk_contribution = risk_data.get("risk_contribution_pct", {})
        highest_component, highest_pct = (
            max(risk_contribution.items(), key=lambda kv: kv[1]) if risk_contribution else ("", 0)
        )
        high_components_count = sum(1 for v in risk_contribution.values() if v > HIGH_COMPONENT_PCT_THRESHOLD)

        portfolio_positions = conc_data.get("portfolio_data", [])

        # Threshold compare uses raw (pre-clip) values so we don't hide spikes.
        vol_egarch_raw = forecast_contribution.get("portfolio_vol", 0)
        flags: Dict[str, bool] = {}
        if vol_egarch_raw > FLAG_HIGH_VOL_PCT:
            flags["high_vol"] = True
        if overall_score_raw > FLAG_HIGH_RISK_SCORE_RAW * 100:
            flags["high_risk_score"] = True
        if total_cvar_pct < FLAG_HIGH_CVAR_PCT:
            flags["high_cvar"] = True

        top_ticker, top_pct = _top_risk_contributor(forecast_contribution)

        return {
            "risk_score": {
                "overall_score": round(overall_score, 1),
                "risk_level": _risk_level(overall_score),
                "highest_risk_component": highest_component,
                "highest_risk_percentage": round(highest_pct, 1),
                "high_risk_components_count": high_components_count,
            },
            "portfolio_overview": {
                "total_market_value": conc_data.get("total_market_value", 0),
                "total_positions": len(portfolio_positions),
                "largest_position": round(
                    conc_data.get("concentration_metrics", {}).get("largest_position", 0), 1
                ),
                "top_3_concentration": round(
                    conc_data.get("concentration_metrics", {}).get("top_3_concentration", 0), 1
                ),
                "volatility_egarch": round(
                    forecast_contribution.get("portfolio_vol_pct", vol_egarch_raw * 100), 1
                ),
                "cvar_percentage": round(total_cvar_pct, 1),
                "cvar_usd": round(total_cvar_usd, 0),
                "top_risk_contributor": {
                    "ticker": top_ticker,
                    "vol_contribution_pct": top_pct,
                },
            },
            "portfolio_positions": portfolio_positions,
            "flags": flags,
        }
    except Exception as e:
        logger.exception("[portfolio_summary] aggregation failed: %s", e)
        return {"error": str(e)}
