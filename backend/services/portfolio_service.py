"""User portfolio CRUD and ticker search.

Responsibilities:
- Read portfolio holdings for a user
- Add/remove tickers, triggering IBKR data fetch on add and cache invalidation
- Mirror portfolio state to the filesystem JSON fixture (kept for seed flows)
- Ticker search via yfinance (IBKR does not expose a symbol search)

Collaborates with: IBKRService, MarketDataService (for historical fetch),
TTLCache (for per-user invalidation).
"""

from __future__ import annotations

import json
import os
import subprocess
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from database.models.portfolio import Portfolio
from database.models.user import User
from services.cache import TTLCache
from services.ibkr_service import IBKRService
from services.market_data_service import MarketDataService

import logging

logger = logging.getLogger(__name__)

class PortfolioService:
    def __init__(
        self,
        ibkr_service: IBKRService,
        market_data: MarketDataService,
        cache: TTLCache,
    ):
        self.ibkr_service = ibkr_service
        self.market_data = market_data
        self.cache = cache

    def get_user_portfolio_tickers(self, db: Session, username: str = "admin") -> List[str]:
        """Return ticker symbols currently held by the user."""
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return []
        items = db.query(Portfolio).filter(Portfolio.user_id == user.id).all()
        return [item.ticker_symbol for item in items]

    def add_ticker(
        self, db: Session, username: str, ticker: str, shares: int
    ) -> Dict[str, Any]:
        """Add a ticker to the user's portfolio. Pulls historical data from IBKR
        and invalidates the user's cache on success."""
        try:
            ticker = ticker.upper().strip()

            user = db.query(User).filter(User.username == username).first()
            if not user:
                return {"error": f"User {username} not found"}

            existing = (
                db.query(Portfolio)
                .filter(Portfolio.user_id == user.id, Portfolio.ticker_symbol == ticker)
                .first()
            )
            if existing:
                return {"error": f"Ticker {ticker} already exists in portfolio"}

            if not self._check_ibkr_connection():
                return {"error": "IBKR connection unavailable"}

            logger.info(f"IBKR available, fetching data for {ticker}")
            if not self.market_data.fetch_and_store_historical_data(db, ticker):
                return {"error": f"Failed to fetch data for {ticker} from IBKR"}

            db.add(Portfolio(user_id=user.id, ticker_symbol=ticker, shares=shares))
            db.commit()

            self._update_portfolio_json(username, db)
            removed = self.cache.clear(f"*{username}*")
            logger.debug(f"[cache] cleared {removed} entries for user {username}")

            return {
                "success": True,
                "message": f"Ticker {ticker} added successfully with {shares} shares (data from IBKR)",
                "data_source": "IBKR",
                "ticker": ticker,
                "shares": shares,
            }
        except Exception as e:
            db.rollback()
            logger.error(f"Error adding ticker to portfolio: {e}")
            return {"error": str(e)}

    def remove_ticker(self, db: Session, username: str, ticker: str) -> Dict[str, Any]:
        """Remove a ticker from the user's portfolio and invalidate their cache."""
        try:
            ticker = ticker.upper().strip()

            user = db.query(User).filter(User.username == username).first()
            if not user:
                return {"error": f"User {username} not found"}

            item = (
                db.query(Portfolio)
                .filter(Portfolio.user_id == user.id, Portfolio.ticker_symbol == ticker)
                .first()
            )
            if not item:
                return {"error": f"Ticker {ticker} not found in portfolio"}

            db.delete(item)
            db.commit()

            self._update_portfolio_json(username, db)
            removed = self.cache.clear(f"*{username}*")
            logger.debug(f"[cache] cleared {removed} entries for user {username}")

            return {
                "success": True,
                "message": f"Ticker {ticker} removed successfully from portfolio",
                "ticker": ticker,
            }
        except Exception as e:
            db.rollback()
            logger.error(f"Error removing ticker from portfolio: {e}")
            return {"error": str(e)}

    def _update_portfolio_json(self, username: str, db: Session) -> None:
        """Mirror the user's portfolio to data/{username}_portfolio.json so that
        re-seeding from fixture stays in sync with the latest DB state."""
        try:
            user = db.query(User).filter(User.username == username).first()
            if not user:
                return
            items = db.query(Portfolio).filter(Portfolio.user_id == user.id).all()
            json_data = [{"ticker": i.ticker_symbol, "shares": i.shares} for i in items]

            json_file = f"../data/{username}_portfolio.json"
            if not os.path.exists(json_file):
                json_file = f"data/{username}_portfolio.json"

            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error updating portfolio JSON: {e}")

    def search_tickers(self, query: str) -> List[Dict[str, str]]:
        """Look up tickers by symbol prefix across a few major exchanges.
        Uses yfinance because IBKR does not expose a symbol-search API."""
        try:
            import yfinance as yf  # lazy -- yfinance import is slow (~2s)

            patterns = [
                query.upper(),
                f"{query.upper()}.TO",  # Toronto
                f"{query.upper()}.L",   # London
                f"{query.upper()}.PA",  # Paris
                f"{query.upper()}.DE",  # Frankfurt
                f"{query.upper()}.SW",  # Swiss
                f"{query.upper()}.AS",  # Amsterdam
            ]

            suggestions: List[Dict[str, str]] = []
            seen: set[str] = set()

            for pattern in patterns:
                try:
                    ticker = yf.Ticker(pattern)
                    info = ticker.info
                    if info and "symbol" in info and info["symbol"] not in seen:
                        seen.add(info["symbol"])
                        suggestions.append(
                            {
                                "symbol": info["symbol"],
                                "name": info.get("longName", info.get("shortName", "Unknown")),
                                "exchange": info.get("exchange", "Unknown"),
                                "type": info.get("quoteType", "Unknown"),
                            }
                        )
                        if len(suggestions) >= 10:
                            break
                except Exception:
                    continue

            return suggestions
        except Exception as e:
            logger.error(f"Error searching tickers: {e}")
            return []

    def _check_ibkr_connection(self) -> bool:
        """Spawn a short-lived Poetry subprocess to probe IBKR TWS without
        touching the main thread's IBKR connection state."""
        try:
            test_script = """
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from services.ibkr_service import IBKRService
    ibkr = IBKRService()
    connected = ibkr.connect(timeout=10)
    logger.info(f"Connected: {connected}")
    if connected:
        ibkr.disconnect()
    sys.exit(0 if connected else 1)
except Exception as e:
    logger.error(f"Error: {e}")
    sys.exit(1)
"""
            test_file = "test_ibkr_connection.py"
            with open(test_file, "w") as f:
                f.write(test_script)

            try:
                result = subprocess.run(
                    ["poetry", "run", "python", test_file],
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
                if os.path.exists(test_file):
                    os.remove(test_file)
                return result.returncode == 0 and "Connected: True" in result.stdout
            except subprocess.TimeoutExpired:
                return False
            finally:
                if os.path.exists(test_file):
                    os.remove(test_file)
        except Exception as e:
            logger.error(f"Error checking IBKR connection: {e}")
            return False
