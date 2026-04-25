"""Factor Exposure -- rolling 60-day OLS betas vs five factor proxies.

Factor proxies:
  MARKET   = SPY
  MOMENTUM = MTUM - SPY  (market-neutral spread)
  SIZE     = IWM  - SPY
  VALUE    = VLUE - SPY
  QUALITY  = QUAL - SPY

Two endpoints:
  - get_factor_exposure_data: full time series (capped at MAX_PER_PAIR
    observations per (ticker, factor) so the JSON payload stays bounded).
  - get_latest_factor_exposures: pivot of the most recent beta per
    (ticker, factor), plus a weighted PORTFOLIO row.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any, Dict, List, Tuple

import numpy as np
from sqlalchemy.orm import Session

from database.models.ticker_data import TickerData

logger = logging.getLogger(__name__)

FACTORS: Tuple[str, ...] = ("MARKET", "MOMENTUM", "SIZE", "VALUE", "QUALITY")
FACTOR_PROXY: Dict[str, str] = {
    "MARKET": "SPY",
    "MOMENTUM": "MTUM",
    "SIZE": "IWM",
    "VALUE": "VLUE",
    "QUALITY": "QUAL",
}
WINDOW = 60          # rolling regression window (days)
MIN_COMMON = 5       # min overlapping dates before we attempt a regression
MAX_PER_PAIR = 400   # cap response size per (ticker, factor) pair


def _rolling_beta_r2(a: np.ndarray, f: np.ndarray, dates, ticker: str, factor: str):
    """Yield (beta_row, r2_row) tuples for each rolling window over aligned arrays."""
    for idx in range(WINDOW, len(dates)):
        y = a[idx - WINDOW:idx]
        x = f[idx - WINDOW:idx]
        X = np.column_stack([np.ones(len(x)), x])
        try:
            coef = np.linalg.lstsq(X, y, rcond=None)[0]
            beta = float(coef[1])
            y_hat = X @ coef
            ssr = float(((y - y_hat) ** 2).sum())
            sst = float(((y - y.mean()) ** 2).sum())
            r2 = 1.0 - ssr / sst if sst > 0 else 0.0
            date = dates[idx]
            yield (
                {"date": date.isoformat(), "ticker": ticker, "factor": factor, "beta": round(beta, 3)},
                {"date": date.isoformat(), "ticker": ticker, "r2": round(max(0.0, min(1.0, r2)), 3)},
            )
        except Exception as e:
            logger.error("Error calculating %s beta for %s: %s", factor, ticker, e)
            continue


def get_factor_exposure_data(data_service, db: Session, username: str = "admin") -> Dict[str, Any]:
    """Full time-series of factor betas per (ticker, factor). Cached."""
    ds = data_service
    cache_key = ds._get_cache_key("factor_exposure_data", username)
    cached = ds._get_from_cache(cache_key)
    if cached:
        return cached

    try:
        all_tickers = ds.get_all_tickers(db, username)
        if not all_tickers:
            result = {
                "factor_exposures": [], "r2_data": [],
                "available_factors": [], "available_tickers": [],
            }
            ds._set_cache(cache_key, result)
            return result

        date_range = db.query(TickerData.date).distinct().order_by(TickerData.date).all()
        dates_global = [d[0] for d in date_range]
        if not dates_global:
            return {
                "factor_exposures": [], "r2_data": [],
                "available_factors": list(FACTORS), "available_tickers": all_tickers,
            }

        # Load ETF proxies once (date -> return) for O(1) lookup in the inner loop.
        proxy_maps: Dict[str, Dict[Any, float]] = {}
        for factor, symbol in FACTOR_PROXY.items():
            p_dates, p_closes = ds._get_close_series(db, symbol)
            p_ret_dates, p_rets = ds._log_returns_from_series(p_dates, p_closes)
            proxy_maps[factor] = dict(zip(p_ret_dates, p_rets))

        spy_map = proxy_maps["MARKET"]

        factor_exposures: List[Dict[str, Any]] = []
        r2_data: List[Dict[str, Any]] = []

        for ticker in all_tickers:
            ticker_data = (
                db.query(TickerData)
                .filter(TickerData.ticker_symbol == ticker)
                .order_by(TickerData.date)
                .all()
            )
            if not ticker_data:
                continue

            asset_dates = [row.date for row in ticker_data]
            prices = [row.close_price for row in ticker_data]
            asset_ret_dates, asset_rets = ds._log_returns_from_series(asset_dates, prices)

            for factor in FACTORS:
                f_map = proxy_maps[factor]
                # MARKET: regress against SPY directly.
                # Other factors: market-neutral spread (proxy - SPY).
                if factor == "MARKET":
                    common = [d for d in asset_ret_dates if d in f_map]
                else:
                    common = [d for d in asset_ret_dates if d in f_map and d in spy_map]
                if len(common) < MIN_COMMON:
                    continue
                common.sort()

                a = np.array([asset_rets[asset_ret_dates.index(d)] for d in common])
                if factor == "MARKET":
                    f_arr = np.array([f_map[d] for d in common])
                else:
                    f_arr = np.array([f_map[d] - spy_map[d] for d in common])

                for beta_row, r2_row in _rolling_beta_r2(a, f_arr, common, ticker, factor):
                    factor_exposures.append(beta_row)
                    r2_data.append(r2_row)

        # Cap per-pair observations so the frontend payload stays bounded.
        trimmed_exposures: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)
        trimmed_r2: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for row in factor_exposures:
            key = (row["ticker"], row["factor"])
            if len(trimmed_exposures[key]) < MAX_PER_PAIR:
                trimmed_exposures[key].append(row)
        for row in r2_data:
            if len(trimmed_r2[row["ticker"]]) < MAX_PER_PAIR:
                trimmed_r2[row["ticker"]].append(row)

        result = {
            "factor_exposures": [r for sub in trimmed_exposures.values() for r in sub],
            "r2_data": [r for sub in trimmed_r2.values() for r in sub],
            "available_factors": list(FACTORS),
            "available_tickers": all_tickers,
            "common_date_range": ds._get_common_date_range(db, all_tickers),
        }
        ds._set_cache(cache_key, result)
        return result
    except Exception as e:
        logger.exception("[factor_exposure] error: %s", e)
        empty = {
            "factor_exposures": [], "r2_data": [],
            "available_factors": [], "available_tickers": [],
        }
        try: ds._set_cache(cache_key, empty)
        except Exception: pass
        return empty


def get_latest_factor_exposures(
    data_service, db: Session, username: str = "admin",
) -> Dict[str, Any]:
    """Pivot: latest beta per (ticker, factor), plus a weighted PORTFOLIO row."""
    ds = data_service
    try:
        data = get_factor_exposure_data(ds, db, username)
        exposures = data["factor_exposures"]

        latest: Dict[Tuple[str, str], Tuple[str, float]] = {}
        for row in exposures:
            key = (row["ticker"], row["factor"])
            if key not in latest or row["date"] > latest[key][0]:
                latest[key] = (row["date"], row["beta"])

        factors = data["available_factors"]
        tickers = data["available_tickers"] + ["PORTFOLIO"]

        # Portfolio betas = weight-weighted sum over the user's holdings.
        port_betas = {f: 0.0 for f in factors}
        try:
            conc = ds.get_concentration_risk_data(db, username)
            if "error" not in conc and conc["portfolio_data"]:
                w_map = {p["ticker"]: p["weight_frac"] for p in conc["portfolio_data"]}
                for factor in factors:
                    for t, w in w_map.items():
                        if (t, factor) in latest:
                            port_betas[factor] += w * latest[(t, factor)][1]
        except Exception as e:
            logger.error("[factor_exposure] portfolio beta calc failed: %s", e)

        table: List[Dict[str, Any]] = []
        for t in tickers:
            row: Dict[str, Any] = {"ticker": t}
            for f in factors:
                if t == "PORTFOLIO":
                    row[f] = round(port_betas[f], 2)
                else:
                    row[f] = round(latest.get((t, f), (None, 0.0))[1], 2)
            table.append(row)

        return {
            "as_of": max(d for d, _ in latest.values()) if latest else "",
            "factors": factors,
            "data": table,
        }
    except Exception as e:
        logger.exception("[factor_exposure] latest error: %s", e)
        return {"error": str(e)}
