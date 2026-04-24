"""Concentration analytics.

Computes position-level weights, sector/market-cap concentration, HHI, and
effective-positions metrics. Reads latest prices and ticker metadata from
DB via the DataService facade (ds_ref).
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict

import numpy as np
from sqlalchemy.orm import Session

from database.models.portfolio import Portfolio
from database.models.ticker_data import TickerData
from database.models.user import User
from quant.concentration import concentration_metrics

import logging

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

class ConcentrationAnalytics:
    def __init__(self, ds_ref):
        self._ds = ds_ref

    def get_concentration_risk_data(self, db: Session, username: str = "admin") -> Dict[str, Any]:
        """Position-level and aggregated (sector, market-cap) concentration metrics."""
        ds = self._ds
        try:
            cache_key = ds._get_cache_key("concentration_risk_data", username)
            cached_data = ds._get_from_cache(cache_key)
            if cached_data:
                logger.info(f"Using cached concentration risk data for user: {username}")
                return cached_data

            logger.info(f"Getting concentration risk data for user: {username}")

            user = db.query(User).filter(User.username == username).first()
            if not user:
                result = {"error": "User not found"}
                ds._set_cache(cache_key, result)
                return result

            portfolio_items = db.query(Portfolio).filter(Portfolio.user_id == user.id).all()
            if not portfolio_items:
                result = {"error": "No portfolio found"}
                ds._set_cache(cache_key, result)
                return result

            portfolio_data = []
            total_mv = 0.0

            for item in portfolio_items:
                ticker = item.ticker_symbol
                shares = item.shares
                latest_data = (
                    db.query(TickerData)
                    .filter(TickerData.ticker_symbol == ticker)
                    .order_by(TickerData.date.desc())
                    .first()
                )
                if latest_data:
                    price = float(latest_data.close_price)
                    market_value = price * shares
                    total_mv += market_value
                    portfolio_data.append(
                        {
                            "ticker": ticker,
                            "shares": shares,
                            "price": price,
                            "market_value": market_value,
                            "weight": 0.0,
                        }
                    )

            if total_mv == 0:
                return {"error": "No market value data"}

            # Weights (fractions and %)
            for item in portfolio_data:
                w = item["market_value"] / total_mv
                item["weight_frac"] = w
                item["weight"] = w * 100.0

            portfolio_data.sort(key=lambda x: x["weight"], reverse=True)

            # Concentration KPIs
            w_frac = np.array([it["weight_frac"] for it in portfolio_data])
            largest_position, top3, top5, top10, hhi, effective_positions = concentration_metrics(w_frac)

            # Enrich with sector / industry / market cap (via TickerInfoService)
            for item in portfolio_data:
                ticker = item["ticker"]
                try:
                    info = ds._ensure_ticker_info(db, ticker)
                    item["sector"] = info.sector if info and info.sector else "Unknown"
                    item["industry"] = info.industry if info and info.industry else "Unknown"
                    item["market_cap"] = info.market_cap if info and info.market_cap else 0.0
                except Exception:
                    item["sector"] = "Unknown"
                    item["industry"] = "Unknown"
                    item["market_cap"] = 0.0

            # Sector aggregation (on fractions)
            sector_w: Dict[str, float] = defaultdict(float)
            for it in portfolio_data:
                sector_w[it.get("sector", "Unknown")] += it["weight_frac"]

            sector_concentration = {
                "sectors": list(sector_w.keys()),
                "weights": [v * 100.0 for v in sector_w.values()],
            }
            hhi_sec = sum(v * v for v in sector_w.values())
            sector_concentration["hhi"] = hhi_sec
            sector_concentration["effective_sectors"] = 1.0 / hhi_sec if hhi_sec > 0 else 0.0

            # Market-cap bucket aggregation
            market_cap_w: Dict[str, float] = defaultdict(float)
            market_cap_details: Dict[str, list] = defaultdict(list)
            for it in portfolio_data:
                market_cap = it.get("market_cap", 0.0)
                category = _market_cap_category(market_cap)
                market_cap_w[category] += it["weight_frac"]
                market_cap_details[category].append(
                    {
                        "ticker": it["ticker"],
                        "market_cap": market_cap,
                        "weight": it["weight"],
                        "market_value": it["market_value"],
                    }
                )

            market_cap_concentration = {
                "categories": list(market_cap_w.keys()),
                "weights": [v * 100.0 for v in market_cap_w.values()],
                "details": dict(market_cap_details),
            }
            hhi_mc = sum(v * v for v in market_cap_w.values())
            market_cap_concentration["hhi"] = hhi_mc
            market_cap_concentration["effective_categories"] = 1.0 / hhi_mc if hhi_mc > 0 else 0.0

            logger.info(f"Calculated concentration metrics for {len(portfolio_data)} positions")

            result = {
                "portfolio_data": portfolio_data,
                "concentration_metrics": {
                    "largest_position": round(largest_position * 100, 1),
                    "top_3_concentration": round(top3 * 100, 1),
                    "top_5_concentration": round(top5 * 100, 1),
                    "top_10_concentration": round(top10 * 100, 1),
                    "herfindahl_index": round(hhi, 4),
                    "effective_positions": round(effective_positions, 1),
                },
                "sector_concentration": sector_concentration,
                "market_cap_concentration": market_cap_concentration,
                "total_market_value": total_mv,
            }

            ds._set_cache(cache_key, result)
            return result
        except Exception as e:
            logger.error(f"Error calculating concentration risk: {e}")
            error_result = {"error": str(e)}
            try:
                ds._set_cache(cache_key, error_result)
            except Exception:
                pass
            return error_result
