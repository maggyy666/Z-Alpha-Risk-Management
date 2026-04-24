"""Factor exposure analytics.

Rolling 60-day OLS beta of each ticker against five factor proxies:
  MARKET  = SPY
  MOMENTUM = MTUM - SPY (market-neutral)
  SIZE    = IWM - SPY
  VALUE   = VLUE - SPY
  QUALITY = QUAL - SPY

Two endpoints:
  get_factor_exposure_data -- full time series (trimmed to 400 obs per pair)
  get_latest_factor_exposures -- pivot: latest beta per (ticker, factor)
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Tuple

import numpy as np
from sqlalchemy.orm import Session

from database.models.ticker_data import TickerData
from quant.linear import ols_beta

import logging

logger = logging.getLogger(__name__)

_FACTORS = ("MARKET", "MOMENTUM", "SIZE", "VALUE", "QUALITY")
_FACTOR_PROXY = {
    "MARKET": "SPY",
    "MOMENTUM": "MTUM",
    "SIZE": "IWM",
    "VALUE": "VLUE",
    "QUALITY": "QUAL",
}
_WINDOW = 60            # rolling regression window (days)
_MIN_COMMON = 5         # min overlapping dates before we attempt a regression
_MAX_PER_PAIR = 400     # bound the response size per (ticker, factor) to keep JSON sane

def _rolling_beta_r2(a: np.ndarray, f: np.ndarray, dates, ticker: str, factor: str):
    """Yield dicts (beta_row, r2_row) for each rolling window over aligned arrays."""
    for idx in range(_WINDOW, len(dates)):
        y = a[idx - _WINDOW:idx]
        x = f[idx - _WINDOW:idx]
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
                {
                    "date": date.isoformat(),
                    "ticker": ticker,
                    "factor": factor,
                    "beta": round(beta, 3),
                },
                {
                    "date": date.isoformat(),
                    "ticker": ticker,
                    "r2": round(max(0.0, min(1.0, r2)), 3),
                },
            )
        except Exception as e:
            logger.error(f"Error calculating {factor} beta for {ticker}: {e}")
            continue

class FactorAnalytics:
    def __init__(self, ds_ref):
        self._ds = ds_ref

    def get_factor_exposure_data(
        self, db: Session, username: str = "admin"
    ) -> Dict[str, Any]:
        """Full time-series of factor betas per (ticker, factor). Cached."""
        ds = self._ds
        try:
            cache_key = ds._get_cache_key("factor_exposure_data", username)
            cached_data = ds._get_from_cache(cache_key)
            if cached_data:
                logger.info(f"Using cached factor exposure data for user: {username}")
                return cached_data

            logger.info(f"Getting factor exposure data for user: {username}")

            all_tickers = ds.get_all_tickers(db, username)
            logger.info(f"All tickers: {all_tickers}")

            if not all_tickers:
                logger.info("No tickers found")
                result = {
                    "factor_exposures": [],
                    "r2_data": [],
                    "available_factors": [],
                    "available_tickers": [],
                }
                ds._set_cache(cache_key, result)
                return result

            factor_exposures: List[Dict[str, Any]] = []
            r2_data: List[Dict[str, Any]] = []

            date_range = db.query(TickerData.date).distinct().order_by(TickerData.date).all()
            dates_global = [d[0] for d in date_range]
            if not dates_global:
                logger.info("No historical data found in database")
                return {
                    "factor_exposures": [],
                    "r2_data": [],
                    "available_factors": list(_FACTORS),
                    "available_tickers": all_tickers,
                }
            logger.info(f"Found {len(dates_global)} dates from {min(dates_global)} to {max(dates_global)}")

            # Load ETF proxies once (dict: date -> return) so the inner loop is O(1) lookup.
            logger.info("Loading ETF data for factor proxies...")
            proxy_maps: Dict[str, Dict[Any, float]] = {}
            proxy_sizes: Dict[str, int] = {}
            for factor, symbol in _FACTOR_PROXY.items():
                p_dates, p_closes = ds._get_close_series(db, symbol)
                p_ret_dates, p_rets = ds._log_returns_from_series(p_dates, p_closes)
                proxy_maps[factor] = dict(zip(p_ret_dates, p_rets))
                proxy_sizes[factor] = len(p_ret_dates)
            logger.info(
                "ETF data loaded: "
                + ", ".join(
                    f"{_FACTOR_PROXY[f]}({proxy_sizes[f]})" for f in _FACTORS
                )
            )

            spy_map = proxy_maps["MARKET"]

            for ticker in all_tickers:
                logger.info(f"Processing {ticker}...")
                ticker_data = (
                    db.query(TickerData)
                    .filter(TickerData.ticker_symbol == ticker)
                    .order_by(TickerData.date)
                    .all()
                )
                if len(ticker_data) < 1:
                    logger.info(f"Not enough data for {ticker} ({len(ticker_data)} records)")
                    continue

                asset_dates = [row.date for row in ticker_data]
                prices = [row.close_price for row in ticker_data]
                asset_ret_dates, asset_rets = ds._log_returns_from_series(asset_dates, prices)

                for factor in _FACTORS:
                    f_map = proxy_maps[factor]
                    # MARKET: regress against SPY directly; other factors are market-neutral (proxy - SPY)
                    if factor == "MARKET":
                        common = [d for d in asset_ret_dates if d in f_map]
                    else:
                        common = [
                            d for d in asset_ret_dates if d in f_map and d in spy_map
                        ]

                    if len(common) < _MIN_COMMON:
                        logger.info(
                            f"Not enough common dates for {ticker} vs {_FACTOR_PROXY[factor]} "
                            f"({len(common)} records)"
                        )
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

            logger.info(f"Generated {len(factor_exposures)} factor exposures and {len(r2_data)} R^2 records")

            # Cap payload size per (ticker, factor) so the frontend does not choke
            trimmed_exposures: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)
            trimmed_r2: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
            for row in factor_exposures:
                k = (row["ticker"], row["factor"])
                if len(trimmed_exposures[k]) < _MAX_PER_PAIR:
                    trimmed_exposures[k].append(row)
            for row in r2_data:
                if len(trimmed_r2[row["ticker"]]) < _MAX_PER_PAIR:
                    trimmed_r2[row["ticker"]].append(row)
            factor_exposures = [r for sub in trimmed_exposures.values() for r in sub]
            r2_data = [r for sub in trimmed_r2.values() for r in sub]
            logger.info(
                f"After trimming: {len(factor_exposures)} factor exposures and "
                f"{len(r2_data)} R^2 records"
            )
            common_date_range = ds._get_common_date_range(db, all_tickers)
            result = {
                "factor_exposures": factor_exposures,
                "r2_data": r2_data,
                "available_factors": list(_FACTORS),
                "available_tickers": all_tickers,
                "common_date_range": common_date_range,
            }
            ds._set_cache(cache_key, result)
            return result
        except Exception as e:
            logger.error(f"Error getting factor exposure data: {e}")
            error_result = {
                "factor_exposures": [],
                "r2_data": [],
                "available_factors": [],
                "available_tickers": [],
            }
            try:
                ds._set_cache(cache_key, error_result)
            except Exception:
                pass
            return error_result

    def get_latest_factor_exposures(
        self, db: Session, username: str = "admin"
    ) -> Dict[str, Any]:
        """Pivot: latest beta per (ticker, factor), plus a weighted PORTFOLIO row."""
        ds = self._ds
        try:
            data = self.get_factor_exposure_data(db, username)
            exposures = data["factor_exposures"]

            latest_map: Dict[Tuple[str, str], Tuple[str, float]] = {}
            for row in exposures:
                key = (row["ticker"], row["factor"])
                if key not in latest_map or row["date"] > latest_map[key][0]:
                    latest_map[key] = (row["date"], row["beta"])

            factors = data["available_factors"]
            tickers = data["available_tickers"] + ["PORTFOLIO"]

            # Portfolio betas = weight-weighted sum over user holdings
            port_betas = {f: 0.0 for f in factors}
            try:
                conc = ds.get_concentration_risk_data(db, username)
                if "error" not in conc and conc["portfolio_data"]:
                    w_map = {p["ticker"]: p["weight_frac"] for p in conc["portfolio_data"]}
                    for factor in factors:
                        for ticker, weight in w_map.items():
                            if (ticker, factor) in latest_map:
                                beta = latest_map[(ticker, factor)][1]
                                port_betas[factor] += weight * beta
            except Exception as e:
                logger.error(f"Error calculating portfolio betas: {e}")

            table: List[Dict[str, Any]] = []
            for t in tickers:
                row: Dict[str, Any] = {"ticker": t}
                for f in factors:
                    if t == "PORTFOLIO":
                        row[f] = round(port_betas[f], 2)
                    else:
                        beta = latest_map.get((t, f), (None, 0.0))[1]
                        row[f] = round(beta, 2)
                table.append(row)

            return {
                "as_of": max(d for d, _ in latest_map.values()) if latest_map else "",
                "factors": factors,
                "data": table,
            }
        except Exception as e:
            logger.error(f"Error getting latest factor exposures: {e}")
            return {"error": str(e)}
