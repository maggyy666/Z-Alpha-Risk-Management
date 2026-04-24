"""Ticker metadata service: sector, industry, market cap.

Uses IBKR fundamentals when available, falls back to yfinance for ETFs and
when Reuters subscription is missing (error 10358). Cache window: 30 days.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from database.models.ticker import TickerInfo
from services.ibkr_service import IBKRService

import logging

logger = logging.getLogger(__name__)

_ETF_HINTS = frozenset({
    "etf", "trust", "fund", "treasury", "ultra", "proshares", "ishares",
    "vanguard", "spy", "qqq", "iwm", "mtum", "vlue", "qual", "sgov",
    "ulty", "bull",
})

class TickerInfoService:
    def __init__(self, ibkr_service: IBKRService):
        self.ibkr_service = ibkr_service

    @staticmethod
    def looks_like_etf(symbol: str) -> bool:
        """Heuristic ETF check by symbol substring."""
        s = symbol.lower()
        return any(hint in s for hint in _ETF_HINTS)

    def ensure_ticker_info(
        self,
        db: Session,
        symbol: str,
        *,
        preloaded: Optional[dict] = None,
    ) -> Optional[TickerInfo]:
        """Ensure ticker_info row exists and is fresher than 30 days.
        Fills missing fields from IBKR fundamentals + yfinance."""
        try:
            info = db.query(TickerInfo).filter(TickerInfo.symbol == symbol).first()
            if info and info.updated_at and (datetime.now(timezone.utc) - info.updated_at).days < 30:
                logger.debug(f"[cache] Using cached ticker info for {symbol}")
                return info

            fundamental_data = preloaded

            # ETF preload -> skip IBKR, go straight to yfinance
            if fundamental_data and fundamental_data.get("type") == "ETF":
                logger.debug(f"[etf] {symbol} is ETF -> skipping IBKR, going straight to yfinance")
                sector, industry = self.ibkr_service._get_sector_industry_external(symbol)
                market_cap = self.ibkr_service._get_market_cap_external(symbol)
                fundamental_data = {
                    "industry": industry,
                    "sector": sector,
                    "market_cap": market_cap,
                    "company_name": fundamental_data.get("company_name", symbol),
                }

            # Nothing preloaded yet -- try IBKR, then yfinance
            if not fundamental_data:
                if self.ibkr_service.connection and self.ibkr_service.connection.connected:
                    fundamental_data = self.ibkr_service.get_fundamentals(symbol)
                if not fundamental_data or fundamental_data.get("industry") == "Unknown":
                    sector, industry = self.ibkr_service._get_sector_industry_external(symbol)
                    market_cap = self.ibkr_service._get_market_cap_external(symbol)
                    if not fundamental_data:
                        fundamental_data = {}
                    fundamental_data.update(
                        {"industry": industry, "sector": sector, "market_cap": market_cap}
                    )

            if not fundamental_data:
                return info  # Nothing new, return whatever we had

            if not info:
                info = TickerInfo(symbol=symbol)
                db.add(info)

            info.industry = fundamental_data.get("industry")
            info.sector = fundamental_data.get("sector")
            info.market_cap = fundamental_data.get("market_cap")
            info.company_name = fundamental_data.get("company_name")
            info.updated_at = datetime.now(timezone.utc)

            db.commit()
            logger.debug(f"[ok] Updated ticker info for {symbol}: {fundamental_data}")
            return info
        except Exception as e:
            logger.error(f"Error ensuring ticker info for {symbol}: {e}")
            db.rollback()
            return None
