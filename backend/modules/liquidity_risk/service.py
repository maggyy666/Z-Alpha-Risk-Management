"""Liquidity Risk -- ADV scoring, spread proxy, liquidation-time bucketing.

Three endpoints, all derived from a single quant.liquidity.liquidity_metrics
call. The overview pulls the full payload; the per-block endpoints just
slice it for the frontend's smaller charts.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from quant.liquidity import liquidity_metrics

logger = logging.getLogger(__name__)


def get_liquidity_overview(data_service, db: Session, username: str = "admin") -> Dict[str, Any]:
    try:
        return liquidity_metrics(db, username)
    except Exception as e:
        logger.exception("[liquidity] overview error: %s", e)
        return {"error": str(e)}


def get_volume_distribution(data_service, db: Session, username: str = "admin") -> Dict[str, Any]:
    out = get_liquidity_overview(data_service, db, username)
    if "error" in out:
        return out
    return out.get("volume_analysis", {})


def get_liquidity_alerts(data_service, db: Session, username: str = "admin") -> List[Dict[str, Any]]:
    out = get_liquidity_overview(data_service, db, username)
    if "error" in out:
        return []
    return out.get("alerts", [])
