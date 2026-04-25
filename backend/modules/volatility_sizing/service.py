"""Volatility-Based Sizing -- forecast vol per position + inverse-vol target weights.

Pipeline (per request):
  1. For each portfolio ticker: fit the chosen vol model (EWMA/GARCH/EGARCH)
     and derive last price + Sharpe.
  2. Compute current MVs and current weights.
  3. Apply inverse-volatility allocation with a vol floor (annualized %) so
     near-zero-vol assets don't blow up the weights.
  4. Translate target weights into target MVs and delta-shares to reach them.

Helper functions `_get_cached_volatility` and `calculate_volatility_metrics`
are exported because the forecast_risk module also needs them
(covariance-matrix construction and rolling-forecast pipeline).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

import numpy as np
from sqlalchemy.orm import Session

from database.models.portfolio import Portfolio
from database.models.ticker_data import TickerData
from database.models.user import User
from quant.stats import basic_stats
from quant.volatility import forecast_sigma
from quant.weights import inverse_vol_allocation

logger = logging.getLogger(__name__)

# Module-level memo cache for forecast_sigma keyed by (symbol, model, hash(returns)).
# Lifetime = process lifetime; sufficient for a single request burst.
_vol_cache: Dict[str, float] = {}

MIN_OBS_VOL = 30


def _get_cached_volatility(symbol: str, model: str, returns: np.ndarray) -> float:
    cache_key = f"{symbol}_{model}_{hash(returns.tobytes())}"
    if cache_key in _vol_cache:
        return _vol_cache[cache_key]
    vol = forecast_sigma(returns, model)
    _vol_cache[cache_key] = vol
    return vol


def calculate_volatility_metrics(
    db: Session,
    symbol: str,
    forecast_model: str = "EWMA (5D)",
    risk_free_annual: float = 0.0,
) -> Dict[str, float]:
    """Forecast vol, annual mean return, Sharpe, last price for one symbol.
    Returns {} when there are fewer than MIN_OBS_VOL bars."""
    try:
        rows = (
            db.query(TickerData)
            .filter(TickerData.ticker_symbol == symbol)
            .order_by(TickerData.date.desc())
            .all()
        )
        if len(rows) < MIN_OBS_VOL:
            return {}

        rows.sort(key=lambda r: r.date)
        prices = [r.close_price for r in rows]
        returns = np.diff(np.log(prices))
        if len(returns) < MIN_OBS_VOL:
            return {}

        stats = basic_stats(returns, risk_free_annual)
        forecast_vol_pct = _get_cached_volatility(symbol, forecast_model, returns) * 100

        return {
            "volatility_pct": forecast_vol_pct,
            "mean_return_annual": stats["mean_daily"] * 252,
            "mean_return_pct": stats["mean_daily"] * 252 * 100,
            "sharpe_ratio": stats["sharpe_ratio"],
            "last_price": float(rows[-1].close_price),
        }
    except Exception as e:
        logger.error("Error calculating metrics for %s: %s", symbol, e)
        return {}


def get_portfolio_volatility_data(
    data_service,
    db: Session,
    username: str = "admin",
    forecast_model: str = "EWMA (5D)",
    vol_floor_annual_pct: float = 8.0,
    risk_free_annual: float = 0.0,
) -> List[Dict[str, Any]]:
    """Per-position forecast vol + inverse-vol target weights, target MVs, delta shares."""
    ds = data_service
    cache_key = ds._get_cache_key(
        "portfolio_volatility_data", username,
        forecast_model=forecast_model,
        vol_floor=vol_floor_annual_pct,
        risk_free=risk_free_annual,
    )
    cached = ds._get_from_cache(cache_key)
    if cached:
        return cached

    try:
        portfolio_tickers = ds.get_user_portfolio_tickers(db, username)
        if not portfolio_tickers:
            ds._set_cache(cache_key, [])
            return []

        user = db.query(User).filter(User.username == username).first()
        items = db.query(Portfolio).filter(Portfolio.user_id == user.id).all()
        shares_map = {it.ticker_symbol: it.shares for it in items}

        portfolio_data: List[Dict[str, Any]] = []
        for symbol in portfolio_tickers:
            m = calculate_volatility_metrics(db, symbol, forecast_model, risk_free_annual)
            if not m:
                continue
            portfolio_data.append({
                "symbol": symbol,
                "forecast_volatility_pct": float(m.get("volatility_pct", 0.0)),
                "last_price": float(m.get("last_price", 0.0)),
                "sharpe_ratio": float(m.get("sharpe_ratio", 0.0)),
                "shares": shares_map.get(symbol, 1000),
                "is_static": False,
            })

        if not portfolio_data:
            ds._set_cache(cache_key, [])
            return []

        for it in portfolio_data:
            it["current_mv"] = float(it["last_price"]) * float(it["shares"])

        total_mv = float(sum(d["current_mv"] for d in portfolio_data))
        if total_mv <= 0:
            ds._set_cache(cache_key, portfolio_data)
            return portfolio_data

        for it in portfolio_data:
            it["current_weight_pct"] = 100.0 * it["current_mv"] / total_mv

        vols = np.array([d["forecast_volatility_pct"] for d in portfolio_data])
        adj_weights = inverse_vol_allocation(vols, vol_floor_annual_pct)
        for it, w in zip(portfolio_data, adj_weights):
            it["adj_volatility_weight_pct"] = w * 100.0

        for it in portfolio_data:
            target_w = it["adj_volatility_weight_pct"] / 100.0
            it["target_mv"] = total_mv * target_w
            it["delta_mv"] = it["target_mv"] - it["current_mv"]
            lp = it["last_price"]
            it["delta_shares"] = int(np.floor(it["delta_mv"] / lp)) if lp > 0 else 0

        ds._set_cache(cache_key, portfolio_data)
        return portfolio_data
    except Exception as e:
        logger.exception("[volatility_sizing] error: %s", e)
        try: ds._set_cache(cache_key, [])
        except Exception: pass
        return []
