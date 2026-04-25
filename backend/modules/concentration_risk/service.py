"""Concentration Risk -- position weights, sector / market-cap aggregations,
HHI and effective-positions metrics.

Reads latest closing prices and ticker metadata (sector / industry /
market_cap) via the DataService facade. The math (HHI, effective positions,
top-N) lives in `quant.concentration`.

Output is consumed by:
  - the Concentration Risk page directly
  - portfolio_summary as the source of `total_market_value` and weights
  - factor_exposure / forecast_risk as the source of portfolio weights
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any, Dict

import numpy as np
from sqlalchemy.orm import Session

from database.models.portfolio import Portfolio
from database.models.ticker_data import TickerData
from database.models.user import User
from quant.concentration import concentration_metrics

logger = logging.getLogger(__name__)


def _market_cap_category(market_cap: float) -> str:
    if market_cap >= 200_000_000_000:
        return "Mega Cap"
    if market_cap >= 10_000_000_000:
        return "Large Cap"
    if market_cap >= 2_000_000_000:
        return "Mid Cap"
    if market_cap >= 300_000_000:
        return "Small Cap"
    if market_cap >= 50_000_000:
        return "Micro Cap"
    if market_cap >= 10_000_000:
        return "Nano Cap"
    return "Micro Cap"


def get_concentration_risk_data(data_service, db: Session, username: str = "admin") -> Dict[str, Any]:
    """Position-level + aggregated (sector, market-cap) concentration metrics."""
    ds = data_service
    cache_key = ds._get_cache_key("concentration_risk_data", username)
    cached = ds._get_from_cache(cache_key)
    if cached:
        return cached

    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            result = {"error": "User not found"}
            ds._set_cache(cache_key, result)
            return result

        items = db.query(Portfolio).filter(Portfolio.user_id == user.id).all()
        if not items:
            result = {"error": "No portfolio found"}
            ds._set_cache(cache_key, result)
            return result

        portfolio_data = []
        total_mv = 0.0
        for item in items:
            latest = (
                db.query(TickerData)
                .filter(TickerData.ticker_symbol == item.ticker_symbol)
                .order_by(TickerData.date.desc())
                .first()
            )
            if not latest:
                continue
            price = float(latest.close_price)
            mv = price * item.shares
            total_mv += mv
            portfolio_data.append({
                "ticker": item.ticker_symbol,
                "shares": item.shares,
                "price": price,
                "market_value": mv,
                "weight": 0.0,
            })

        if total_mv == 0:
            return {"error": "No market value data"}

        for it in portfolio_data:
            it["weight_frac"] = it["market_value"] / total_mv
            it["weight"] = it["weight_frac"] * 100.0
        portfolio_data.sort(key=lambda x: x["weight"], reverse=True)

        w_frac = np.array([it["weight_frac"] for it in portfolio_data])
        largest, top3, top5, top10, hhi, n_eff = concentration_metrics(w_frac)

        # Enrich with sector / industry / market cap (TickerInfoService via facade).
        for it in portfolio_data:
            try:
                info = ds._ensure_ticker_info(db, it["ticker"])
                it["sector"] = info.sector if info and info.sector else "Unknown"
                it["industry"] = info.industry if info and info.industry else "Unknown"
                it["market_cap"] = info.market_cap if info and info.market_cap else 0.0
            except Exception:
                it["sector"] = "Unknown"
                it["industry"] = "Unknown"
                it["market_cap"] = 0.0

        sector_w: Dict[str, float] = defaultdict(float)
        for it in portfolio_data:
            sector_w[it.get("sector", "Unknown")] += it["weight_frac"]
        hhi_sec = sum(v * v for v in sector_w.values())
        sector_block = {
            "sectors": list(sector_w.keys()),
            "weights": [v * 100.0 for v in sector_w.values()],
            "hhi": hhi_sec,
            "effective_sectors": 1.0 / hhi_sec if hhi_sec > 0 else 0.0,
        }

        mc_w: Dict[str, float] = defaultdict(float)
        mc_details: Dict[str, list] = defaultdict(list)
        for it in portfolio_data:
            cat = _market_cap_category(it.get("market_cap", 0.0))
            mc_w[cat] += it["weight_frac"]
            mc_details[cat].append({
                "ticker": it["ticker"],
                "market_cap": it.get("market_cap", 0.0),
                "weight": it["weight"],
                "market_value": it["market_value"],
            })
        hhi_mc = sum(v * v for v in mc_w.values())
        mc_block = {
            "categories": list(mc_w.keys()),
            "weights": [v * 100.0 for v in mc_w.values()],
            "details": dict(mc_details),
            "hhi": hhi_mc,
            "effective_categories": 1.0 / hhi_mc if hhi_mc > 0 else 0.0,
        }

        result = {
            "portfolio_data": portfolio_data,
            "concentration_metrics": {
                "largest_position": round(largest * 100, 1),
                "top_3_concentration": round(top3 * 100, 1),
                "top_5_concentration": round(top5 * 100, 1),
                "top_10_concentration": round(top10 * 100, 1),
                "herfindahl_index": round(hhi, 4),
                "effective_positions": round(n_eff, 1),
            },
            "sector_concentration": sector_block,
            "market_cap_concentration": mc_block,
            "total_market_value": total_mv,
        }
        ds._set_cache(cache_key, result)
        return result
    except Exception as e:
        logger.exception("[concentration] error: %s", e)
        result = {"error": str(e)}
        try: ds._set_cache(cache_key, result)
        except Exception: pass
        return result
