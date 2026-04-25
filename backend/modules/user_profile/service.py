"""User Profile -- portfolio CRUD + ticker search + cache invalidation.

Endpoints owned by this module:
  GET    /user-portfolio/{username}
  POST   /user-portfolio/{username}
  POST   /add-ticker/{username}
  DELETE /remove-ticker/{username}
  GET    /ticker-search
  POST   /invalidate-user/{username}

Add/remove/search delegate to DataService primitives. Get + bulk update
are implemented inline because they're database-shape pivots, not analytics.
A successful POST also rewrites the on-disk fixture so seeding stays in
sync between manual edits and reseeds.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Tuple

from sqlalchemy.orm import Session

from database.models.portfolio import Portfolio
from database.models.ticker import TickerInfo
from database.models.ticker_data import TickerData
from database.models.user import User

logger = logging.getLogger(__name__)


def _resolve_user(db: Session, username: str) -> User:
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise ValueError(f"User {username} not found")
    return user


def get_user_portfolio(db: Session, username: str) -> Dict[str, Any]:
    """Snapshot of the user's holdings: ticker, shares, latest close, market value,
    sector/industry from ticker_info. total_market_value summed across positions."""
    user = _resolve_user(db, username)
    items = db.query(Portfolio).filter(Portfolio.user_id == user.id).all()

    portfolio_items: List[Dict[str, Any]] = []
    total_mv = 0.0
    for it in items:
        info = db.query(TickerInfo).filter(TickerInfo.symbol == it.ticker_symbol).first()
        latest = (
            db.query(TickerData)
            .filter(TickerData.ticker_symbol == it.ticker_symbol)
            .order_by(TickerData.date.desc())
            .first()
        )
        if not latest:
            continue
        mv = latest.close_price * it.shares
        total_mv += mv
        portfolio_items.append({
            "ticker": it.ticker_symbol,
            "shares": it.shares,
            "price": latest.close_price,
            "market_value": mv,
            "sector": info.sector if info else "Unknown",
            "industry": info.industry if info else "Unknown",
        })

    return {
        "username": username,
        "portfolio_items": portfolio_items,
        "total_market_value": total_mv,
        "total_positions": len(portfolio_items),
    }


def update_user_portfolio(
    data_service, db: Session, username: str, portfolio_data: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Bulk update: upsert each {ticker, shares} from the payload, rewrite the
    on-disk fixture, then invalidate the user's cache so analytics see the new state."""
    user = _resolve_user(db, username)
    existing = {it.ticker_symbol: it for it in db.query(Portfolio).filter(Portfolio.user_id == user.id).all()}

    updated, added = 0, 0
    for entry in portfolio_data:
        if "ticker" not in entry or "shares" not in entry:
            continue
        ticker = entry["ticker"]
        shares = int(entry["shares"])
        if ticker in existing:
            existing[ticker].shares = shares
            updated += 1
        else:
            db.add(Portfolio(user_id=user.id, ticker_symbol=ticker, shares=shares))
            added += 1
    db.commit()

    data_service._clear_cache(f"*{username}*")

    _rewrite_portfolio_fixture(db, user, username)

    return {
        "success": True,
        "message": f"Portfolio updated for {username}",
        "updated_items": updated,
        "new_items": added,
        "total_items": db.query(Portfolio).filter(Portfolio.user_id == user.id).count(),
    }


def add_ticker(data_service, db: Session, username: str, ticker: str, shares: int) -> Dict[str, Any]:
    """Add a ticker (with shares) to the user's portfolio, fetching market data
    eagerly via the DataService primitive."""
    return data_service.add_ticker_to_portfolio(db, username, ticker, shares)


def remove_ticker(data_service, db: Session, username: str, ticker: str) -> Dict[str, Any]:
    return data_service.remove_ticker_from_portfolio(db, username, ticker)


def search_tickers(data_service, query: str) -> Dict[str, Any]:
    suggestions = data_service.search_tickers(query)
    return {"suggestions": suggestions}


def invalidate_user_cache(data_service, username: str) -> Dict[str, Any]:
    data_service._clear_cache(f"*{username}*")
    return {"ok": True, "message": f"Cache invalidated for user: {username}"}


def _rewrite_portfolio_fixture(db: Session, user: User, username: str) -> None:
    """Mirror the DB state into data/{username}_portfolio.json so a future
    seed reproduces the latest manual edits. Resolved relative to either
    repo root or backend/ depending on cwd."""
    candidates = [f"../data/{username}_portfolio.json", f"data/{username}_portfolio.json"]
    target = next((p for p in candidates if os.path.exists(p)), candidates[0])

    items = db.query(Portfolio).filter(Portfolio.user_id == user.id).all()
    payload = [{"ticker": it.ticker_symbol, "shares": it.shares} for it in items]
    try:
        with open(target, "w") as f:
            json.dump(payload, f, indent=2)
    except Exception as e:
        logger.warning("[user_profile] could not rewrite fixture %s: %s", target, e)
