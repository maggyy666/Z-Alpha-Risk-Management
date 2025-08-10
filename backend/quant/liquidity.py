"""Portfolio liquidity metrics.

Args/Inputs:
- db: Session, username (str). Uses `TickerData`, `Portfolio`, `User`.

Provides:
- liquidity_metrics(db, username): JSON-like dict expected by frontend.

Returns:
- Dict with overview, distribution, volume_analysis, position_details, alerts.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any
from datetime import date, timedelta
from sqlalchemy.orm import Session
from database.models.ticker_data import TickerData
from database.models.portfolio import Portfolio
from database.models.user import User


_N_VOL = 21
_N_SPR = 10

def _get_series(db: Session, symbol: str, field: str, lookback: int):
    """Get time series for a specific field from database"""
    rows = (db.query(TickerData)
               .filter(TickerData.ticker_symbol == symbol)
               .order_by(TickerData.date.desc())
               .limit(lookback)
               .all())
    rows.reverse()           # oldest to newest
    if not rows:
        return np.array([])
    return np.array([getattr(r, field) for r in rows], dtype=float)

def _avg_volume(db, symbol):       
    """Calculate average daily volume over last N_VOL days"""
    vol_series = _get_series(db, symbol, "volume", 180)
    if len(vol_series) < _N_VOL:
        return 0.0
    return vol_series[-_N_VOL:].mean()

def _curr_volume(db, symbol):      
    """Get current volume (last trading day)"""
    vol_series = _get_series(db, symbol, "volume", 1)
    return vol_series[-1] if len(vol_series) > 0 else 0.0

def _spread_pct(db, symbol):
    """Calculate spread percentage using real bid/ask or high-low proxy"""
    # Try real bid/ask first; fallback to high/low proxy
    latest_data = (db.query(TickerData)
                      .filter(TickerData.ticker_symbol == symbol)
                      .order_by(TickerData.date.desc())
                      .first())
    
    bid = getattr(latest_data, "bid_price", None) if latest_data else None
    ask = getattr(latest_data, "ask_price", None) if latest_data else None
    if bid is not None and ask is not None:
        bid = float(bid)
        ask = float(ask)
        mid = (bid + ask) / 2
        if mid > 0:
            spread = (ask - bid) / mid
            return max(spread, 0.0001)  # minimum 0.01%
    
    # Proxy path
    high = _get_series(db, symbol, "high_price", _N_SPR)
    low = _get_series(db, symbol, "low_price", _N_SPR)
    
    if len(high) < _N_SPR or len(low) < _N_SPR:
        return np.nan
    
    mid = (high + low) / 2
    with np.errstate(divide="ignore", invalid="ignore"):
        spr = np.where(mid > 0, (high - low) / mid, np.nan)
    
    spr = np.clip(spr, 0.0001, 0.20)  # 0.01% to 20%
    return np.nanmean(spr)

def _vol_score(avg_vol):
    """Calculate volume score (1-10) based on average volume"""
    if avg_vol <= 0:
        return 1.0
    return float(np.clip(2 * np.log10(avg_vol / 1e5) + 1, 1, 10))

def _spr_score(spread):
    """Calculate spread score (1-10) based on spread percentage"""
    if not np.isfinite(spread) or spread <= 0:
        return 1.0  # no data/zero data = worst score
    return float(np.clip(10 - 400 * spread, 1, 10))



def liquidity_metrics(
    db: Session,
    username: str = "admin",
    adv_frac: float = 0.20,
    vol_thr_high: float = 5e6,
    vol_thr_med: float = 1e6
) -> Dict[str, Any]:
    """Core calculator - returns exactly the JSON the React tab expects."""
    # Get user portfolio (weight, shares, market value)
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return {"error": "user not found"}
    
    items = (db.query(Portfolio)
               .filter(Portfolio.user_id == user.id)
               .all())
    if not items:
        return {"error": "empty portfolio"}

    pos = []
    total_mv = 0.0
    
    for it in items:
        last_px = (db.query(TickerData.close_price)
                     .filter(TickerData.ticker_symbol == it.ticker_symbol)
                     .order_by(TickerData.date.desc())
                     .first())
        if not last_px:
            continue
        mv = float(last_px[0]) * it.shares
        total_mv += mv
        pos.append({
            "ticker": it.ticker_symbol,
            "shares": it.shares,
            "market_value": mv,
            "weight_frac": 0.0  # will calculate after total
        })

    if total_mv == 0:
        return {"error": "no prices?"}

    # Per-ticker liquidity metrics
    high_liq_w, med_liq_w, low_liq_w = 0.0, 0.0, 0.0
    max_liq_days = 0
    overall_score = 0.0
    alerts = []
    details = []

    # Calculate weights
    for p in pos:
        p["weight_frac"] = p["market_value"] / total_mv
    
    for p in pos:
        w = p["weight_frac"]
        avol = _avg_volume(db, p["ticker"])
        cvol = _curr_volume(db, p["ticker"])
        spr = _spread_pct(db, p["ticker"])   # may return np.nan

        v_cat = "High" if avol > vol_thr_high else ("Medium" if avol > vol_thr_med else "Low")
        v_scr = _vol_score(avol)
        s_scr = _spr_score(spr)              # converts nan/0 to score=1
        liq = 0.7 * v_scr + 0.3 * s_scr

        # liquidation time (adv_frac * ADV per day)
        if avol <= 1:
            days = int(1e9)
            alerts.append({
                "severity": "HIGH",
                "text": f"Zero/low volume: {p['ticker']} (ADV: {avol:.0f})"
            })
        else:
            days = int(np.ceil(p["shares"] / (adv_frac * avol)))
        days = max(days, 1)

        # Bucket assignment
        if liq >= 8:
            high_liq_w += w
        elif liq >= 5:
            med_liq_w += w
        else:
            low_liq_w += w

        max_liq_days = max(max_liq_days, days)
        overall_score += w * liq

        # Alerts
        if not np.isfinite(spr):
            alerts.append({
                "severity": "MEDIUM",
                "text": f"No spread data for {p['ticker']} (using proxy/NA)"
            })
        elif spr > 0.015:
            alerts.append({
                "severity": "MEDIUM",
                "text": f"Wide avg spread on {p['ticker']} ({spr:.2%})"
            })

        if liq < 3:
            alerts.append({
                "severity": "HIGH",
                "text": f"Very illiquid: {p['ticker']} (score {liq:.1f})"
            })

        details.append({
            **p,
            "weight_pct": round(w * 100, 2),
            "avg_volume": int(avol),
            "current_volume": int(cvol),
            "spread_pct": round(spr * 100, 2) if np.isfinite(spr) else 0.0,
            "volume_category": v_cat,
            "volume_score": round(v_scr, 1),
            "liquidity_score": round(liq, 1),
            "liq_days": days
        })

    # Portfolio-level outputs
    risk_level = ("LOW" if overall_score >= 8
                  else "MEDIUM" if overall_score >= 5
                  else "HIGH")

    if overall_score < 5:
        alerts.append({
            "severity": "HIGH",
            "text": "Portfolio liquidity classified as HIGH RISK"
        })

    # portfolio-level liquidation time formatting
    if max_liq_days >= 365*10:
        liq_time = "illiquid"
    elif max_liq_days <= 1:
        liq_time = "1 day"
    elif max_liq_days <= 5:
        liq_time = "2-5 days"
    else:
        liq_time = f"{max_liq_days} days"

    # volume_weighted_avg — use exact weights
    avg_volume_global = int(np.mean([p['avg_volume'] for p in details]))
    volume_weighted_avg = int(sum(p['avg_volume'] * p['weight_frac'] for p in details))

    return {
        "overview": {
            "overall_score": round(overall_score, 1),
            "risk_level": risk_level,
            "estimated_liquidation_time": liq_time
        },
        "distribution": {
            "High Liquidity (8-10)": round(high_liq_w * 100, 1),
            "Medium Liquidity (5-8)": round(med_liq_w * 100, 1),
            "Low Liquidity (<5)": round(low_liq_w * 100, 1)
        },
        "volume_analysis": {
            "avg_volume_global": avg_volume_global,
            "total_portfolio_volume": int(sum(p['current_volume'] for p in details)),
            "volume_weighted_avg": volume_weighted_avg
        },
        "position_details": details,
        "alerts": alerts
    }
