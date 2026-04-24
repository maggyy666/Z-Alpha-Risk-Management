"""Liquidity analytics -- thin wrappers over quant.liquidity.

The heavy lifting (ADV scoring, liquidation-time bucketing) lives in
quant.liquidity.liquidity_metrics; this module just routes the API calls
and shapes responses per endpoint.
"""

from __future__ import annotations

from typing import Any, Dict, List

from sqlalchemy.orm import Session

from quant.liquidity import liquidity_metrics


class LiquidityAnalytics:
    def __init__(self, ds_ref):
        self._ds = ds_ref

    def get_liquidity_metrics(self, db: Session, username: str = "admin") -> Dict[str, Any]:
        print(f"[LIQUIDITY-METRICS] Starting liquidity metrics for user: {username}")
        try:
            return liquidity_metrics(db, username)
        except Exception as e:
            print(f"Error getting liquidity metrics: {e}")
            return {"error": str(e)}

    def get_volume_distribution(self, db: Session, username: str = "admin") -> Dict[str, Any]:
        try:
            out = self.get_liquidity_metrics(db, username)
            if "error" in out:
                return out
            return out.get("volume_analysis", {})
        except Exception as e:
            print(f"Error getting volume distribution: {e}")
            return {"error": str(e)}

    def get_liquidity_alerts(self, db: Session, username: str = "admin") -> List[Dict[str, Any]]:
        result = liquidity_metrics(db, username)
        return result.get("alerts", [])
