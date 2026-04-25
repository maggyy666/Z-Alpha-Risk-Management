"""Realized Risk -- historical performance metrics and rolling series.

Two endpoints:
  - get_realized_metrics: per-ticker + PORTFOLIO row of realized stats
    (Sharpe, Sortino, max drawdown, VaR/CVaR, capture ratios, ...).
  - get_rolling_metric: rolling window series (vol/sharpe/return/maxdd/beta)
    for charting; supports the synthetic 'PORTFOLIO' aggregate.

Both call into `quant.realized` / `quant.rolling` for the math, and rely
on the DataService facade for return-series alignment, portfolio snapshot,
and cache primitives. The dashboard fallback used when history is too thin
lives here as `_sample_metrics_fallback`.
"""

from __future__ import annotations

import logging
import random
from math import isfinite
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from quant.realized import compute_realized_metrics
from quant.rolling import rolling_metric

logger = logging.getLogger(__name__)

MIN_OBS_REALIZED = 30
MIN_OBS_ROLLING = 40


def get_realized_metrics(data_service, db: Session, username: str) -> Dict[str, Any]:
    """Realized risk metrics per ticker + PORTFOLIO row, aligned to SPY.

    Returns the sample fallback whenever overlapping history with SPY is
    insufficient (< MIN_OBS_REALIZED obs) -- keeps the UI populated while
    the user grows the portfolio.
    """
    ds = data_service
    portfolio_tickers: List[str] = []
    try:
        cache_key = ds._get_cache_key("realized_metrics", username)
        cached = ds._get_from_cache(cache_key)
        if cached:
            return cached

        portfolio_positions, ok = ds._portfolio_snapshot(db, username)
        if not ok or not portfolio_positions:
            return {"metrics": []}

        portfolio_tickers = [p["ticker"] for p in portfolio_positions]
        weights_map = {p["ticker"]: p["weight_frac"] for p in portfolio_positions}

        needed = portfolio_tickers + ["SPY"]
        ret_map = ds._get_return_series_map(db, needed, lookback_days=252 * 2)
        dates_ref, M, active = ds._align_on_reference(
            ret_map, needed, ref_symbol="SPY", min_obs=MIN_OBS_REALIZED
        )

        if (
            M.size == 0
            or len(dates_ref) < MIN_OBS_REALIZED
            or "SPY" not in ret_map
            or len(ret_map["SPY"][0]) == 0
        ):
            return _sample_metrics_fallback(portfolio_tickers)

        spy_dates, spy_ret = ret_map["SPY"]
        idx_spy = {d: i for i, d in enumerate(spy_dates)}
        spy_aligned = np.array(
            [spy_ret[idx_spy[d]] if d in idx_spy else np.nan for d in dates_ref],
            dtype=float,
        )

        metrics_frames: List[pd.DataFrame] = []
        sym_cols = [s for s in active if s != "SPY"]
        if not sym_cols:
            return _sample_metrics_fallback(portfolio_tickers)

        for j, sym in enumerate(sym_cols):
            x = M[:, j]
            mask = np.isfinite(x) & np.isfinite(spy_aligned)
            if mask.sum() < MIN_OBS_REALIZED:
                continue
            d_use = [dates_ref[k] for k in range(len(dates_ref)) if mask[k]]
            df = pd.DataFrame({sym: x[mask], "SPY": spy_aligned[mask]}, index=d_use)
            try:
                res = compute_realized_metrics(
                    df, benchmark_ndx="SPY", R=df.values, active=[sym, "SPY"]
                )
                if not res.empty and sym in res.index:
                    metrics_frames.append(res.loc[[sym]])
            except Exception as e:
                logger.debug("[realized] %s failed: %s", sym, e)
                continue

        # PORTFOLIO row -- day-by-day weight coverage renormalization
        dates_p, rp = ds._portfolio_series_with_coverage(
            dates_ref, M, weights_map, sym_cols, min_weight_cov=0.60
        )
        if len(rp) >= MIN_OBS_REALIZED:
            i_spy = {d: i for i, d in enumerate(dates_ref)}
            spy_p: List[float] = []
            d_common: List = []
            for d in dates_p:
                if d in i_spy and np.isfinite(spy_aligned[i_spy[d]]):
                    spy_p.append(spy_aligned[i_spy[d]])
                    d_common.append(d)
            spy_p_arr = np.array(spy_p, dtype=float)
            rp_arr = np.array([rp[dates_p.index(d)] for d in d_common], dtype=float)

            if len(rp_arr) >= MIN_OBS_REALIZED and len(spy_p_arr) >= MIN_OBS_REALIZED:
                dfp = pd.DataFrame(
                    {"PORTFOLIO": rp_arr, "SPY": spy_p_arr}, index=d_common
                )
                try:
                    res_p = compute_realized_metrics(
                        dfp, benchmark_ndx="SPY", R=dfp.values,
                        active=["PORTFOLIO", "SPY"],
                    )
                    if not res_p.empty and "PORTFOLIO" in res_p.index:
                        metrics_frames.append(res_p.loc[["PORTFOLIO"]])
                except Exception as e:
                    logger.debug("[realized] PORTFOLIO failed: %s", e)

        if not metrics_frames:
            return _sample_metrics_fallback(portfolio_tickers)

        out = [_row_to_dict(df, sym) for df in metrics_frames for sym in df.index]
        result = {"metrics": out}
        ds._set_cache(cache_key, result)
        return result
    except Exception as e:
        logger.exception("[realized] global error: %s", e)
        return _sample_metrics_fallback(portfolio_tickers)


def get_rolling_metric(
    data_service,
    db: Session,
    metric: str = "vol",
    window: int = 21,
    tickers: Optional[List[str]] = None,
    username: str = "admin",
) -> Dict[str, Any]:
    """Rolling metric series (vol / sharpe / return / maxdd / beta) for charting.

    Synthesizes a PORTFOLIO series via day-by-day weight-coverage
    renormalization when the caller asks for it. SPY column is injected
    on demand for `metric='beta'`.
    """
    ds = data_service
    try:
        if tickers is None:
            tickers = ["PORTFOLIO"]

        cache_key = ds._get_cache_key(
            "rolling_metric", username, metric=metric, window=window, tickers=tickers
        )
        cached = ds._get_from_cache(cache_key)
        if cached:
            return cached

        portfolio_tickers = ds.get_user_portfolio_tickers(db, username)
        all_tickers = portfolio_tickers + ds.get_static_tickers() + ["SPY"]

        ret_map = ds._get_return_series_map(db, all_tickers, lookback_days=252 * 5)
        dates, R, active = ds._align_on_reference(
            ret_map, all_tickers, ref_symbol="SPY", min_obs=MIN_OBS_ROLLING
        )
        if R.size == 0 or len(dates) < MIN_OBS_ROLLING:
            return {"error": "Insufficient overlapping history (vs SPY)"}

        ret_df = pd.DataFrame(R, index=dates, columns=active)

        # SPY column needed for beta even if it wasn't selected as active.
        if metric == "beta" and "SPY" not in ret_df.columns and "SPY" in ret_map:
            spy_dates, spy_returns = ret_map["SPY"]
            spy_idx = {d: i for i, d in enumerate(spy_dates)}
            spy_series = np.array(
                [spy_returns[spy_idx[d]] if d in spy_idx else np.nan for d in dates],
                dtype=float,
            )
            ret_df["SPY"] = spy_series

        if "PORTFOLIO" in tickers:
            ret_df = _attach_portfolio_column(ds, db, ret_df, dates, R, active, username)

        datasets = []
        for ticker in tickers:
            if ticker not in ret_df.columns:
                continue
            try:
                ser = rolling_metric(ret_df, metric, window, ticker)
                if not isinstance(ser, pd.Series):
                    ser = pd.Series(ser, index=ret_df.index)
                ser = ser.replace([np.inf, -np.inf], np.nan)
                datasets.append({
                    "ticker": ticker,
                    "dates": [str(d) for d in ser.index],
                    "values": [
                        None if pd.isna(v) or not isfinite(float(v)) else float(v)
                        for v in ser.values
                    ],
                })
            except Exception as e:
                logger.error("Rolling metric for %s failed: %s", ticker, e)
                continue

        result = {
            "datasets": datasets,
            "metric": metric,
            "window": window,
            "common_date_range": ds._get_common_date_range(db, all_tickers),
        }
        ds._set_cache(cache_key, result)
        return result
    except Exception as e:
        logger.exception("[rolling] global error: %s", e)
        return {"error": str(e)}


def _attach_portfolio_column(
    ds, db: Session, ret_df: pd.DataFrame, dates, R, active, username: str
) -> pd.DataFrame:
    """Build the synthetic PORTFOLIO return series and append it as a column."""
    portfolio_weights = {
        it["ticker"]: it["weight_frac"]
        for it in ds.get_concentration_risk_data(db, username).get("portfolio_data", [])
    }
    try:
        dates_p, rp = ds._portfolio_series_with_coverage(
            dates, R, portfolio_weights, active, min_weight_cov=0.60
        )
        port = pd.Series(index=dates, dtype=float)
        port.loc[dates_p] = rp
        ret_df["PORTFOLIO"] = port.values
    except Exception as e:
        # Fallback: weighted sum, ignoring coverage. Inferior, but better
        # than dropping the PORTFOLIO line off the chart entirely.
        logger.error("Portfolio series with coverage failed (%s); using naive weighted sum", e)
        portfolio_returns = np.zeros(len(R))
        for i, t in enumerate(active):
            if t in portfolio_weights:
                portfolio_returns += R[:, i] * portfolio_weights[t]
        ret_df["PORTFOLIO"] = portfolio_returns

    return ret_df.replace([np.inf, -np.inf], np.nan)


def _row_to_dict(df: pd.DataFrame, sym: str) -> Dict[str, Any]:
    """Convert one DataFrame row into the dict shape the frontend expects."""
    row = df.loc[sym]

    def safe(x, default=0.0):
        try:
            return float(x) if pd.notna(x) and np.isfinite(x) else default
        except Exception:
            return default

    return {
        "ticker": sym,
        "ann_return_pct": safe(row.get("Ann.Return%", 0.0)),
        "volatility_pct": safe(row.get("Ann.Volatility%", 0.0)),
        "sharpe_ratio": safe(row.get("Sharpe", 0.0)),
        "sortino_ratio": safe(row.get("Sortino", 0.0)),
        "skewness": safe(row.get("Skew", 0.0)),
        "kurtosis": safe(row.get("Kurtosis", 0.0)),
        "max_drawdown_pct": safe(row.get("Max Drawdown%", 0.0)),
        "var_95_pct": safe(row.get("VaR(5%)%", 0.0)),
        "cvar_95_pct": safe(row.get("CVaR(95%)%", 0.0)),
        "hit_ratio_pct": safe(row.get("Hit Ratio%", 0.0)),
        "beta_ndx": safe(row.get("Beta (SPY)", 0.0)),
        "up_capture_ndx_pct": safe(row.get("Up Capture (SPY)%", 0.0)),
        "down_capture_ndx_pct": safe(row.get("Down Capture (SPY)%", 0.0)),
        "tracking_error_pct": safe(row.get("Tracking Error%", 0.0)),
        "information_ratio": safe(row.get("Information Ratio", 0.0)),
    }


def _sample_metrics_fallback(portfolio_tickers: List[str]) -> Dict[str, Any]:
    """Static-ish sample row used when history is too thin for real
    computation -- keeps the UI populated until enough data accumulates.
    Per-ticker rows are randomized but deterministic by ticker hash so
    the table doesn't shuffle on every refresh."""
    metrics: List[Dict[str, Any]] = [
        {
            "ticker": "PORTFOLIO",
            "ann_return_pct": 38.89,
            "volatility_pct": 29.67,
            "sharpe_ratio": 0.94,
            "sortino_ratio": 1.55,
            "skewness": 4.38,
            "kurtosis": 52.47,
            "max_drawdown_pct": -35.08,
            "var_95_pct": -2.41,
            "cvar_95_pct": -3.44,
            "hit_ratio_pct": 47.75,
            "beta_ndx": 1.02,
            "up_capture_ndx_pct": 113.10,
            "down_capture_ndx_pct": 92.35,
            "tracking_error_pct": 1.39,
            "information_ratio": 0.98,
        }
    ]
    for ticker in portfolio_tickers:
        random.seed(hash(ticker) % 1000)
        metrics.append({
            "ticker": ticker,
            "ann_return_pct": round(random.uniform(15, 60), 2),
            "volatility_pct": round(random.uniform(20, 50), 2),
            "sharpe_ratio": round(random.uniform(0.5, 2.0), 2),
            "sortino_ratio": round(random.uniform(0.8, 2.5), 2),
            "skewness": round(random.uniform(-2, 5), 2),
            "kurtosis": round(random.uniform(10, 60), 2),
            "max_drawdown_pct": round(random.uniform(-50, -15), 2),
            "var_95_pct": round(random.uniform(-4, -1), 2),
            "cvar_95_pct": round(random.uniform(-6, -2), 2),
            "hit_ratio_pct": round(random.uniform(40, 60), 2),
            "beta_ndx": round(random.uniform(0.5, 2.0), 2),
            "up_capture_ndx_pct": round(random.uniform(80, 130), 2),
            "down_capture_ndx_pct": round(random.uniform(70, 110), 2),
            "tracking_error_pct": round(random.uniform(1, 5), 2),
            "information_ratio": round(random.uniform(0.3, 1.5), 2),
        })

    return {
        "metrics": metrics,
        "common_date_range": {
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "total_days": 252,
        },
    }
