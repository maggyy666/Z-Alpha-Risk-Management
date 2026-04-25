"""Forecast Risk -- portfolio risk decomposition and per-ticker forecasts.

Two endpoints:
  - get_forecast_risk_contribution: builds the chosen vol-model covariance,
    then runs marginal/total risk-contribution decomposition over the
    portfolio. Optionally prepends a synthetic PORTFOLIO row using the
    full (un-renormalized) weights for context.
  - get_forecast_metrics: per-ticker forward-looking volatility (EWMA-5/20,
    GARCH, EGARCH) plus parametric VaR/CVaR at the requested confidence.

Both lean on quant.risk / quant.var / quant.volatility for math; the
DataService facade supplies portfolio data and the covariance builder.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from database.models.portfolio import Portfolio
from database.models.user import User
from modules.volatility_sizing.service import calculate_volatility_metrics
from quant.risk import build_cov, risk_contribution
from quant.stats import basic_stats
from quant.var import var_cvar
from quant.volatility import forecast_sigma

logger = logging.getLogger(__name__)

MIN_OBS_FORECAST_METRICS = 250
MIN_OBS_COV_DATES = 60
MIN_OBS_COV_ALIGN = 40


def build_covariance_matrix(
    data_service, db: Session, tickers: List[str], vol_model: str = "EWMA (5D)",
) -> np.ndarray:
    """Build covariance matrix from forecast vols + pandas pairwise correlation.
    Eigenvalue-floor + symmetrization keeps the result PSD."""
    ds = data_service
    if not tickers:
        return np.empty((0, 0))

    vol_vec: List[float] = []
    for t in tickers:
        m = calculate_volatility_metrics(db, t, vol_model)
        vol_vec.append(max(m.get("volatility_pct", 8.0) / 100.0, 0.005))
    vol_vec_arr = np.array(vol_vec)

    universe = list(set(tickers + ["SPY"]))
    ret_map = ds._get_return_series_map(db, universe, lookback_days=252)
    dates, R, active = ds._align_on_reference(
        ret_map, universe, ref_symbol="SPY", min_obs=MIN_OBS_COV_ALIGN,
    )

    if R.size == 0 or len(dates) < MIN_OBS_COV_DATES:
        logger.warning("[cov] insufficient overlap; falling back to identity correlation")
        corr = np.eye(len(tickers))
    else:
        df = pd.DataFrame(R, index=dates, columns=active)
        C = df.corr(min_periods=MIN_OBS_COV_ALIGN).reindex(
            index=tickers, columns=tickers,
        ).fillna(0.0).values
        np.fill_diagonal(C, 1.0)
        C = np.nan_to_num(C, nan=0.0)
        C = 0.5 * (C + C.T)
        eigvals, eigvecs = np.linalg.eigh(C)
        eigvals = np.clip(eigvals, 1e-6, None)
        C = eigvecs @ np.diag(eigvals) @ eigvecs.T
        d = np.sqrt(np.clip(np.diag(C), 1e-12, None))
        C = C / np.outer(d, d)
        np.fill_diagonal(C, 1.0)
        corr = C

    return build_cov(vol_vec_arr, corr)


def get_forecast_risk_contribution(
    data_service,
    db: Session,
    username: str = "admin",
    vol_model: str = "EWMA (5D)",
    tickers: Optional[List[str]] = None,
    include_portfolio_bar: bool = True,
) -> Dict[str, Any]:
    """Marginal + total risk contribution per position under a forward
    volatility model. The PORTFOLIO bar (if requested) reports the
    portfolio sigma at the head of the chart.
    """
    ds = data_service
    try:
        conc = ds.get_concentration_risk_data(db, username)
        if "error" in conc:
            return {"error": conc["error"]}

        portfolio_data = conc["portfolio_data"]
        if not portfolio_data:
            return {"error": "No portfolio data"}

        full_tickers = [p["ticker"] for p in portfolio_data]
        full_w = np.array([float(p["weight_frac"]) for p in portfolio_data], dtype=float)
        full_w = full_w / full_w.sum()

        cov_full = build_covariance_matrix(ds, db, full_tickers, vol_model)
        if cov_full.size == 0:
            return {"error": "Failed to build full covariance matrix"}

        _, _, sigma_full = risk_contribution(full_w, cov_full)

        # Renormalize over the (possibly filtered) tickers_out used for the chart.
        tickers_out = [item["ticker"] for item in portfolio_data]
        weights = np.array([float(item["weight_frac"]) for item in portfolio_data], dtype=float)
        weights[~np.isfinite(weights)] = 0.0
        s = float(weights.sum())
        if s <= 0:
            return {"error": "Invalid weights (sum <= 0)"}
        weights = weights / s

        cov_matrix = build_covariance_matrix(ds, db, tickers_out, vol_model)
        if cov_matrix.size == 0:
            return {"error": "Failed to build covariance matrix"}

        try:
            mrc, pct_rc, sigma_p = risk_contribution(weights, cov_matrix)
        except ValueError as e:
            return {"error": str(e)}

        chart_rows: List[Dict[str, Any]] = [
            {
                "ticker": t,
                "marginal_rc_pct": mrc[i] * 100,
                "total_rc_pct": pct_rc[i],
                "weight_pct": weights[i] * 100,
            }
            for i, t in enumerate(tickers_out)
        ]
        chart_rows.sort(key=lambda r: r["marginal_rc_pct"], reverse=True)

        if include_portfolio_bar:
            chart_rows.insert(0, {
                "ticker": "PORTFOLIO",
                "marginal_rc_pct": float(sigma_full * 100.0),
                "total_rc_pct": 100.0,
                "weight_pct": 100.0,
            })

        return {
            "tickers": [r["ticker"] for r in chart_rows],
            "marginal_rc_pct": [float(r["marginal_rc_pct"]) for r in chart_rows],
            "total_rc_pct": [float(r["total_rc_pct"]) for r in chart_rows],
            "weights_pct": [float(r["weight_pct"]) for r in chart_rows],
            "portfolio_vol": float(sigma_p),
            "portfolio_vol_pct": float(sigma_p * 100.0),
            "vol_model": vol_model,
        }
    except Exception as e:
        logger.exception("[forecast_risk] contribution error: %s", e)
        return {"error": str(e)}


def get_forecast_metrics(
    data_service, db: Session, username: str = "admin", conf_level: float = 0.95,
) -> Dict[str, Any]:
    """Per-ticker forward volatility forecasts (EWMA-5/20, GARCH, EGARCH)
    plus parametric VaR/CVaR. Tickers with < MIN_OBS_FORECAST_METRICS bars
    are skipped to keep GARCH stable.
    """
    ds = data_service
    try:
        tickers = ds.get_user_portfolio_tickers(db, username)
        if not tickers:
            return {"error": "No portfolio tickers found"}

        user_id = db.query(User.id).filter(User.username == username).scalar()
        if not user_id:
            return {"error": "User not found"}

        shares_map = {
            p.ticker_symbol: p.shares
            for p in db.query(Portfolio).filter(Portfolio.user_id == user_id).all()
        }

        metrics: List[Dict[str, Any]] = []
        for ticker in tickers:
            _, closes = ds._get_close_series(db, ticker)
            if len(closes) < MIN_OBS_FORECAST_METRICS:
                continue
            returns = np.diff(np.log(closes))
            if len(returns) < MIN_OBS_FORECAST_METRICS:
                continue

            ewma5 = forecast_sigma(returns, "EWMA (5D)") * 100
            ewma20 = forecast_sigma(returns, "EWMA (20D)") * 100
            garch = forecast_sigma(returns, "GARCH") * 100
            egarch = forecast_sigma(returns, "EGARCH") * 100

            stats = basic_stats(returns)
            var_pct, cvar_pct = var_cvar(stats["std_daily"], stats["mean_daily"], conf_level)

            mv = shares_map.get(ticker, 0) * closes[-1]
            metrics.append({
                "ticker": ticker,
                "ewma5_pct": round(ewma5, 2),
                "ewma20_pct": round(ewma20, 2),
                "garch_vol_pct": round(garch, 2),
                "egarch_vol_pct": round(egarch, 2),
                "var_pct": round(var_pct, 2),
                "cvar_pct": round(cvar_pct, 2),
                "var_usd": round(var_pct / 100 * mv, 0),
                "cvar_usd": round(cvar_pct / 100 * mv, 0),
            })

        metrics.sort(key=lambda r: r["ticker"])
        return {"metrics": metrics, "conf_level": conf_level}
    except Exception as e:
        logger.exception("[forecast_risk] metrics error: %s", e)
        return {"error": str(e)}


def get_rolling_forecast(
    data_service,
    db: Session,
    tickers: List[str],
    model: str,
    window: int,
    username: str = "admin",
) -> Dict[str, Any]:
    """Rolling vol-forecast series per ticker; supports synthetic PORTFOLIO line.

    The PORTFOLIO line is built by taking the user's portfolio weights, aligning
    constituent return series on SPY, and aggregating with day-by-day weight
    coverage renormalization (consistent with realized_risk's PORTFOLIO logic).
    """
    ds = data_service
    if not tickers:
        return {"data": [], "model": model, "window": window}

    lookback = 3 * 365
    ret_map = ds._get_return_series_map(db, tickers, lookback_days=lookback)

    # Common dates = intersection across non-PORTFOLIO tickers with enough history.
    common_dates = None
    for tkr in tickers:
        if tkr == "PORTFOLIO":
            continue
        _, rets = ret_map.get(tkr, ([], np.array([])))
        if len(rets) >= window:
            ts = set(ret_map[tkr][0])
            common_dates = ts if common_dates is None else common_dates.intersection(ts)

    # If only PORTFOLIO requested, seed common_dates from the synthetic series.
    if common_dates is None and "PORTFOLIO" in tickers:
        conc = ds.get_concentration_risk_data(db, username)
        if "error" not in conc and conc["portfolio_data"]:
            w_map = {p["ticker"]: p["weight_frac"] for p in conc["portfolio_data"]}
            active = list(w_map.keys())
            ret_map.update(
                ds._get_return_series_map(db, list(set(active + ["SPY"])), lookback_days=lookback)
            )
            dates_ref, R, active_aligned = ds._align_on_reference(
                ret_map, active, ref_symbol="SPY", min_obs=window,
            )
            dates_p, _ = ds._portfolio_series_with_coverage(
                dates_ref, R, w_map, active_aligned, min_weight_cov=0.60,
            )
            common_dates = set(dates_p)

    if common_dates is None:
        return {"data": [], "model": model, "window": window}

    common_sorted = sorted(common_dates)
    out: List[Dict[str, Any]] = []

    for tkr in tickers:
        if tkr == "PORTFOLIO":
            continue
        dates, rets = ret_map.get(tkr, ([], np.array([])))
        if len(rets) < window:
            continue
        date_idx = {d: i for i, d in enumerate(dates)}
        for date in common_sorted:
            if date not in date_idx:
                continue
            i = date_idx[date]
            if i < window:
                continue
            sigma = forecast_sigma(rets[i - window:i], model) * 100
            out.append({
                "date": date.isoformat() if hasattr(date, "isoformat") else str(date),
                "ticker": tkr,
                "vol_pct": round(float(sigma), 4),
            })

    if "PORTFOLIO" in tickers:
        conc = ds.get_concentration_risk_data(db, username)
        if "error" not in conc and conc["portfolio_data"]:
            w_map = {p["ticker"]: p["weight_frac"] for p in conc["portfolio_data"]}
            active = list(w_map.keys())
            if any(a not in ret_map for a in active):
                ret_map.update(
                    ds._get_return_series_map(db, list(set(active + ["SPY"])), lookback_days=lookback)
                )
            dates_ref, R, active_aligned = ds._align_on_reference(
                ret_map, active, ref_symbol="SPY", min_obs=window,
            )
            if len(dates_ref) >= window:
                dates_p, rp = ds._portfolio_series_with_coverage(
                    dates_ref, R, w_map, active_aligned, min_weight_cov=0.60,
                )
                p_idx = {d: i for i, d in enumerate(dates_p)}
                for date in common_sorted:
                    if date not in p_idx:
                        continue
                    j = p_idx[date]
                    if j < window:
                        continue
                    sigma = forecast_sigma(rp[j - window:j], model) * 100
                    out.append({
                        "date": date.isoformat() if hasattr(date, "isoformat") else str(date),
                        "ticker": "PORTFOLIO",
                        "vol_pct": round(float(sigma), 4),
                    })

    out.sort(key=lambda d: (d["date"], d["ticker"]))
    return {
        "data": out,
        "model": model,
        "window": window,
        "common_date_range": ds._get_common_date_range(db, tickers),
    }
