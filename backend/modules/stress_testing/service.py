"""Stress Testing -- market regime + historical-scenario PnL.

Two concerns in one module because the frontend consumes them as a single
payload (regime radar above the scenarios table on the same page).

  - get_market_regime: rolling 60-day vol / avg correlation / momentum,
    bucketed against the configured thresholds into a regime label.
  - get_historical_scenarios: replays each historical crisis window
    against the current portfolio, reporting return + max drawdown,
    skipping scenarios with insufficient coverage.
  - get_stress_testing: aggregator returning both blocks (JSON-safe).

Scenario list and threshold constants live in `setup_database` so the
seed and runtime agree on what to evaluate.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import numpy as np
from sqlalchemy.orm import Session

from quant.drawdown import drawdown
from quant.regime import regime_metrics
from quant.risk import clamp
from services.data_service import REGIME_THRESH, STRESS_LIMITS, STRESS_SCENARIOS
from utils.json_safe import clean_json_values

logger = logging.getLogger(__name__)


def get_market_regime(data_service, db: Session, username: str = "admin") -> Dict[str, Any]:
    """Vol / avg-corr / momentum on the last lookback window -> regime label + radar."""
    ds = data_service
    positions, ok = ds._portfolio_snapshot(db, username)
    if not ok or not positions:
        return {"error": "No positions"}

    tickers = [p["ticker"] for p in positions]
    w_map = {p["ticker"]: p["weight_frac"] for p in positions}

    lookback = STRESS_LIMITS["lookback_regime_days"] + 2
    needed = tickers + ["SPY"]
    ret_map = ds._get_return_series_map(db, needed, lookback_days=lookback)

    dates_ref, R, active = ds._align_on_reference(ret_map, needed, ref_symbol="SPY", min_obs=30)
    if R.size == 0 or len(dates_ref) < 40:
        return {"error": "Insufficient data for regime"}

    w = np.array([w_map.get(s, 0.0) for s in active], dtype=float)
    w = w / (w.sum() if w.sum() > 0 else 1.0)

    R = clamp(R, STRESS_LIMITS["clamp_return_abs"])
    R_win = R[-STRESS_LIMITS["lookback_regime_days"]:, :]

    vol_ann, avg_corr, mom, radar, label = regime_metrics(R_win, w, REGIME_THRESH)
    return {
        "label": label,
        "volatility_pct": vol_ann * 100.0,
        "correlation": avg_corr,
        "momentum_pct": mom * 100.0,
        "radar": radar,
    }


def get_historical_scenarios(
    data_service,
    db: Session,
    username: str = "admin",
    scenarios: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Compute PnL / max-drawdown for each historical scenario.
    Skip scenarios with insufficient coverage or too-short alignment window."""
    ds = data_service
    positions, ok = ds._portfolio_snapshot(db, username)
    if not ok or not positions:
        return {"error": "No positions"}

    tickers = [p["ticker"] for p in positions]
    w_map = {p["ticker"]: p["weight_frac"] for p in positions}
    scenarios = scenarios or STRESS_SCENARIOS
    limits = STRESS_LIMITS

    analyzed: List[Dict[str, Any]] = []
    excluded: List[Dict[str, Any]] = []

    for sc in scenarios:
        name, start_d, end_d = sc["name"], sc["start"], sc["end"]

        ret_map: Dict[str, Any] = {}
        included: List[str] = []
        w_cov = 0.0
        for t in tickers:
            dts, r = ds._get_returns_between_dates(db, t, start_d, end_d)
            if len(r) >= 2:
                ret_map[t] = (dts, r)
                included.append(t)
                w_cov += w_map.get(t, 0.0)

        d_spy, r_spy = ds._get_returns_between_dates(db, "SPY", start_d, end_d)
        if len(r_spy) >= limits["scenario_min_days"]:
            ret_map["SPY"] = (d_spy, r_spy)

        if w_cov < limits["scenario_min_weight_coverage"]:
            excluded.append({"name": name, "reason": f"Low weight coverage ({w_cov * 100:.0f}%)"})
            continue
        if not included:
            excluded.append({"name": name, "reason": "No overlapping data"})
            continue

        dates_ref, R, active = ds._align_on_reference(
            ret_map, included + ["SPY"],
            ref_symbol="SPY", min_obs=limits["scenario_min_days"],
        )
        if R.size == 0 or len(dates_ref) < limits["scenario_min_days"]:
            excluded.append({"name": name, "reason": "Too few aligned dates"})
            continue

        dates_used, rp = ds._portfolio_series_with_coverage(
            dates_ref, R, w_map, active, min_weight_cov=limits["scenario_min_weight_coverage"]
        )
        if len(rp) < limits["scenario_min_days"]:
            excluded.append({"name": name, "reason": "Coverage below threshold after alignment"})
            continue

        ret_pct = (np.exp(rp.sum()) - 1.0) * 100.0
        _, max_dd = drawdown(rp)
        analyzed.append({
            "name": name,
            "start": start_d.isoformat(),
            "end": end_d.isoformat(),
            "days": len(dates_used),
            "weight_coverage_pct": w_cov * 100.0,
            "return_pct": ret_pct,
            "max_drawdown_pct": max_dd * 100.0,
        })

    return {
        "scenarios_analyzed": len(analyzed),
        "scenarios_excluded": len(excluded),
        "results": analyzed,
        "excluded": excluded,
    }


def get_stress_testing(data_service, db: Session, username: str = "admin") -> Dict[str, Any]:
    """Aggregated stress response: regime + scenarios, NaN/Inf-cleaned for JSON."""
    return clean_json_values({
        "market_regime": get_market_regime(data_service, db, username),
        "scenarios": get_historical_scenarios(data_service, db, username),
    })
