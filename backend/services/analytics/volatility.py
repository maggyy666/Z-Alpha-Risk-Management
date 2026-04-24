"""Volatility-forecast analytics.

Per-ticker and portfolio-level volatility forecasts (EWMA / GARCH / EGARCH),
VaR/CVaR per ticker, covariance matrix construction with PD enforcement,
inverse-volatility sizing, and rolling-forecast series for charts.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from database.models.portfolio import Portfolio
from database.models.ticker_data import TickerData
from database.models.user import User
from quant.risk import build_cov, risk_contribution
from quant.stats import basic_stats
from quant.var import var_cvar
from quant.volatility import forecast_sigma
from quant.weights import inverse_vol_allocation

# Module-level memo cache for forecast_sigma calls keyed by (symbol, model, returns hash).
import logging

logger = logging.getLogger(__name__)

_vol_cache: Dict[str, float] = {}

class VolatilityAnalytics:
    def __init__(self, ds_ref):
        self._ds = ds_ref

    def _get_cached_volatility(self, symbol: str, model: str, returns: np.ndarray) -> float:
        cache_key = f"{symbol}_{model}_{hash(returns.tobytes())}"
        if cache_key in _vol_cache:
            return _vol_cache[cache_key]
        vol = forecast_sigma(returns, model)
        _vol_cache[cache_key] = vol
        return vol

    def calculate_volatility_metrics(
        self,
        db: Session,
        symbol: str,
        forecast_model: str = "EWMA (5D)",
        risk_free_annual: float = 0.0,
    ) -> Dict[str, float]:
        """Forecast-vol, annual mean return, Sharpe and last price for a single symbol."""
        try:
            historical_data = (
                db.query(TickerData)
                .filter(TickerData.ticker_symbol == symbol)
                .order_by(TickerData.date.desc())
                .all()
            )
            if len(historical_data) < 30:
                logger.info(f"Not enough data for {symbol} ({len(historical_data)} records)")
                return {}

            logger.info(f"{symbol}: Found {len(historical_data)} historical records")
            historical_data.sort(key=lambda x: x.date)
            prices = [row.close_price for row in historical_data]
            logger.info(f"{symbol}: Prices range: {min(prices):.2f} - {max(prices):.2f}")

            returns = np.diff(np.log(prices))
            logger.info(f"{symbol}: Returns shape: {returns.shape}, mean: {np.mean(returns):.6f}")
            if len(returns) < 30:
                logger.info(f"Not enough returns for {symbol}")
                return {}

            stats = basic_stats(returns, risk_free_annual)
            mean_daily = stats["mean_daily"]
            sharpe_ratio = stats["sharpe_ratio"]

            logger.info(f"Calculating {forecast_model} volatility for returns shape: {returns.shape}")
            forecast_vol = self._get_cached_volatility(symbol, forecast_model, returns) * 100
            logger.info(f"{symbol}: Calculated volatility: {forecast_vol:.2f}%")

            mean_annual = mean_daily * 252
            last_price = float(historical_data[-1].close_price)
            logger.info(f"Using database price for {symbol}: ${last_price}")

            metrics = {
                "volatility_pct": forecast_vol,
                "mean_return_annual": mean_annual,
                "mean_return_pct": mean_annual * 100,
                "sharpe_ratio": sharpe_ratio,
                "last_price": last_price,
            }
            logger.info(f"{symbol} metrics: {metrics}")
            return metrics
        except Exception as e:
            logger.error(f"Error calculating metrics for {symbol}: {e}")
            return {}

    def get_portfolio_volatility_data(
        self,
        db: Session,
        username: str = "admin",
        forecast_model: str = "EWMA (5D)",
        vol_floor_annual_pct: float = 8.0,
        risk_free_annual: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """Per-position volatility + inverse-vol target weights, target MVs and delta shares."""
        ds = self._ds
        try:
            cache_key = ds._get_cache_key(
                "portfolio_volatility_data",
                username,
                forecast_model=forecast_model,
                vol_floor=vol_floor_annual_pct,
                risk_free=risk_free_annual,
            )
            cached_data = ds._get_from_cache(cache_key)
            if cached_data:
                logger.info(f"Using cached portfolio volatility data for user: {username}")
                return cached_data

            logger.info(f"Getting portfolio volatility data for user: {username}")

            portfolio_data: List[Dict[str, Any]] = []

            portfolio_tickers = ds.get_user_portfolio_tickers(db, username)
            if not portfolio_tickers:
                logger.info(f"No portfolio tickers found for user {username}")
                result: List[Dict[str, Any]] = []
                ds._set_cache(cache_key, result)
                return result

            user = db.query(User).filter(User.username == username).first()
            portfolio_items = db.query(Portfolio).filter(Portfolio.user_id == user.id).all()
            shares_map = {item.ticker_symbol: item.shares for item in portfolio_items}

            for symbol in portfolio_tickers:
                logger.info(f"Processing {symbol}...")
                m = self.calculate_volatility_metrics(db, symbol, forecast_model, risk_free_annual)
                logger.info(f"{symbol} metrics: {m}")
                if m:
                    shares = shares_map.get(symbol, 1000)
                    portfolio_data.append(
                        {
                            "symbol": symbol,
                            "forecast_volatility_pct": float(m.get("volatility_pct", 0.0)),
                            "last_price": float(m.get("last_price", 0.0)),
                            "sharpe_ratio": float(m.get("sharpe_ratio", 0.0)),
                            "shares": shares,
                            "is_static": False,
                        }
                    )
                else:
                    logger.info(f"No metrics for {symbol}")

            if not portfolio_data:
                result = []
                ds._set_cache(cache_key, result)
                return result

            for item in portfolio_data:
                item["current_mv"] = float(item["last_price"]) * float(item["shares"])

            total_portfolio_value = (
                float(sum(d["current_mv"] for d in portfolio_data)) if portfolio_data else 0.0
            )
            if total_portfolio_value <= 0:
                result = portfolio_data
                ds._set_cache(cache_key, result)
                return result

            for item in portfolio_data:
                item["current_weight_pct"] = 100.0 * item["current_mv"] / total_portfolio_value

            vols = np.array([d["forecast_volatility_pct"] for d in portfolio_data])
            adj_weights = inverse_vol_allocation(vols, vol_floor_annual_pct)
            for item, adj_weight in zip(portfolio_data, adj_weights):
                item["adj_volatility_weight_pct"] = adj_weight * 100.0

            for item in portfolio_data:
                target_w = item["adj_volatility_weight_pct"] / 100.0
                item["target_mv"] = total_portfolio_value * target_w
                item["delta_mv"] = item["target_mv"] - item["current_mv"]
                lp = item["last_price"]
                item["delta_shares"] = int(np.floor(item["delta_mv"] / lp)) if lp > 0 else 0

            ds._set_cache(cache_key, portfolio_data)
            return portfolio_data
        except Exception as e:
            logger.error(f"Error getting portfolio volatility data: {e}")
            error_result: List[Dict[str, Any]] = []
            try:
                ds._set_cache(cache_key, error_result)
            except Exception:
                pass
            return error_result

    def build_covariance_matrix(
        self, db: Session, tickers: List[str], vol_model: str = "EWMA (5D)"
    ) -> np.ndarray:
        """Build covariance matrix from forecast vols and pandas pairwise correlation
        (PD-clipped via eigenvalue flooring)."""
        ds = self._ds
        if not tickers:
            return np.empty((0, 0))

        logger.debug(f"[COV-MATRIX] Building for tickers: {tickers}")

        vol_vec: List[float] = []
        for ticker in tickers:
            metrics = self.calculate_volatility_metrics(db, ticker, vol_model)
            vol = metrics.get("volatility_pct", 8.0) / 100.0
            vol_vec.append(max(vol, 0.005))

        vol_vec_arr = np.array(vol_vec)
        ret_map = ds._get_return_series_map(
            db, list(set(tickers + ["SPY"])), lookback_days=252
        )
        dates, R, active = ds._align_on_reference(
            ret_map, list(set(tickers + ["SPY"])), ref_symbol="SPY", min_obs=40
        )

        if R.size == 0 or len(dates) < 60:
            logger.warning("Warning: Insufficient data for correlation, using diagonal matrix")
            corr_matrix = np.eye(len(tickers))
        else:
            df = pd.DataFrame(R, index=dates, columns=active)
            C_df = df.corr(min_periods=40)
            C_df = C_df.reindex(index=tickers, columns=tickers).fillna(0.0)
            np.fill_diagonal(C_df.values, 1.0)
            C = C_df.values
            C = np.nan_to_num(C, nan=0.0)
            C = 0.5 * (C + C.T)
            eigvals, eigvecs = np.linalg.eigh(C)
            eigvals = np.clip(eigvals, 1e-6, None)
            C = eigvecs @ np.diag(eigvals) @ eigvecs.T
            d = np.sqrt(np.clip(np.diag(C), 1e-12, None))
            C = C / np.outer(d, d)
            np.fill_diagonal(C, 1.0)
            corr_matrix = C

        cov_matrix = build_cov(vol_vec_arr, corr_matrix)
        logger.debug(f"[COV-MATRIX] Final covariance matrix shape: {cov_matrix.shape}")
        return cov_matrix

    def get_forecast_risk_contribution(
        self,
        db: Session,
        username: str = "admin",
        vol_model: str = "EWMA (5D)",
        tickers: Optional[List[str]] = None,
        include_portfolio_bar: bool = True,
    ) -> Dict[str, Any]:
        ds = self._ds
        try:
            logger.debug(
                f"[FORECAST-RISK] Starting with tickers: {tickers}, "
                f"include_portfolio_bar: {include_portfolio_bar}"
            )
            conc = ds.get_concentration_risk_data(db, username)
            if "error" in conc:
                return {"error": conc["error"]}

            portfolio_data = conc["portfolio_data"]
            if not portfolio_data:
                return {"error": "No portfolio data"}

            all_positions = portfolio_data
            full_tickers = [p["ticker"] for p in all_positions]
            full_w = np.array([float(p["weight_frac"]) for p in all_positions], dtype=float)
            full_w = full_w / full_w.sum()

            logger.debug(f"[FORECAST-RISK] Full portfolio - tickers: {full_tickers}, weights: {full_w}")

            cov_full = self.build_covariance_matrix(db, full_tickers, vol_model)
            if cov_full.size == 0:
                return {"error": "Failed to build full covariance matrix"}

            _, _, sigma_full = risk_contribution(full_w, cov_full)
            logger.debug(f"[FORECAST-RISK] Full portfolio volatility: {sigma_full}")

            tickers_out = [item["ticker"] for item in portfolio_data]
            weights = np.array([float(item["weight_frac"]) for item in portfolio_data], dtype=float)
            weights[~np.isfinite(weights)] = 0.0
            s = float(weights.sum())
            if s <= 0:
                return {"error": "Invalid weights (sum <= 0)"}
            weights = weights / s

            logger.debug(f"[FORECAST-RISK] Using tickers: {tickers_out}, weights: {weights}")

            cov_matrix = self.build_covariance_matrix(db, tickers_out, vol_model)
            if cov_matrix.size == 0:
                return {"error": "Failed to build covariance matrix"}

            logger.debug(f"[FORECAST-RISK] Covariance matrix shape: {cov_matrix.shape}")
            logger.debug(f"[FORECAST-RISK] Weights shape: {weights.shape}")

            try:
                mrc, pct_rc, sigma_p = risk_contribution(weights, cov_matrix)
                risk_data = {"marginal_rc": mrc, "total_rc_pct": pct_rc, "portfolio_vol": sigma_p}
                logger.debug(
                    f"[FORECAST-RISK] Risk contributions calculated - MRC: {mrc}, "
                    f"Total RC: {pct_rc}, Portfolio Vol: {sigma_p}"
                )
            except ValueError as e:
                logger.debug(f"[FORECAST-RISK] Error in risk_contribution: {e}")
                return {"error": str(e)}

            marginal_rc = risk_data["marginal_rc"]
            total_rc_pct = risk_data["total_rc_pct"]

            chart_data: List[Dict[str, Any]] = []
            for i, ticker in enumerate(tickers_out):
                chart_data.append(
                    {
                        "ticker": ticker,
                        "marginal_rc_pct": marginal_rc[i] * 100,
                        "total_rc_pct": total_rc_pct[i],
                        "weight_pct": weights[i] * 100,
                    }
                )
            chart_data.sort(key=lambda x: x["marginal_rc_pct"], reverse=True)

            if include_portfolio_bar:
                portfolio_row = {
                    "ticker": "PORTFOLIO",
                    "marginal_rc_pct": float(sigma_full * 100.0),
                    "total_rc_pct": 100.0,
                    "weight_pct": 100.0,
                }
                logger.debug(f"[FORECAST-RISK] Adding PORTFOLIO row (full portfolio): {portfolio_row}")
                chart_data.insert(0, portfolio_row)

            result = {
                "tickers": [item["ticker"] for item in chart_data],
                "marginal_rc_pct": [float(item["marginal_rc_pct"]) for item in chart_data],
                "total_rc_pct": [float(item["total_rc_pct"]) for item in chart_data],
                "weights_pct": [float(item["weight_pct"]) for item in chart_data],
                "portfolio_vol": float(risk_data["portfolio_vol"]),
                "vol_model": vol_model,
                "portfolio_vol_pct": float(risk_data["portfolio_vol"] * 100.0),
            }
            logger.debug(f"[FORECAST-RISK] Final result - tickers: {result['tickers']}")
            logger.debug(f"[FORECAST-RISK] Final result - marginal_rc_pct: {result['marginal_rc_pct']}")
            return result
        except Exception as e:
            logger.error(f"Error calculating forecast risk contribution: {e}")
            return {"error": str(e)}

    def get_forecast_metrics(
        self, db: Session, username: str = "admin", conf_level: float = 0.95
    ) -> Dict[str, Any]:
        ds = self._ds
        logger.debug(
            f"[FORECAST-METRICS] Starting forecast metrics for user: {username}, "
            f"conf_level: {conf_level}"
        )
        try:
            logger.debug("[FORECAST-METRICS] Getting portfolio tickers...")
            tickers = ds.get_user_portfolio_tickers(db, username)
            if not tickers:
                logger.debug("[FORECAST-METRICS] No portfolio tickers found")
                return {"error": "No portfolio tickers found"}
            logger.debug(f"[FORECAST-METRICS] Portfolio tickers: {tickers}")

            user_id = db.query(User.id).filter(User.username == username).scalar()
            if not user_id:
                return {"error": "User not found"}

            shares_map = {
                p.ticker_symbol: p.shares
                for p in db.query(Portfolio).filter(Portfolio.user_id == user_id).all()
            }

            metrics_data: List[Dict[str, Any]] = []

            for ticker in tickers:
                logger.debug(f"[FORECAST-METRICS] Processing {ticker}...")
                dates, closes = ds._get_close_series(db, ticker)
                if len(closes) < 250:
                    logger.debug(f"[FORECAST-METRICS] {ticker}: Insufficient data ({len(closes)} < 250)")
                    continue

                returns = np.diff(np.log(closes))
                if len(returns) < 250:
                    continue

                logger.debug(f"[FORECAST-METRICS] {ticker}: Calculating volatilities...")
                ewma5 = forecast_sigma(returns, "EWMA (5D)") * 100
                ewma20 = forecast_sigma(returns, "EWMA (20D)") * 100
                garch_vol = forecast_sigma(returns, "GARCH") * 100
                egarch_vol = forecast_sigma(returns, "EGARCH") * 100
                logger.debug(
                    f"[FORECAST-METRICS] {ticker}: EWMA5={ewma5:.2f}%, EWMA20={ewma20:.2f}%, "
                    f"GARCH={garch_vol:.2f}%, EGARCH={egarch_vol:.2f}%"
                )
                stats = basic_stats(returns)
                sigma_d = stats["std_daily"]
                mu_d = stats["mean_daily"]
                var_pct, cvar_pct = var_cvar(sigma_d, mu_d, conf_level)

                last_price = closes[-1]
                shares = shares_map.get(ticker, 0)
                mv = shares * last_price
                var_usd = var_pct / 100 * mv
                cvar_usd = cvar_pct / 100 * mv

                metrics_data.append(
                    {
                        "ticker": ticker,
                        "ewma5_pct": round(ewma5, 2),
                        "ewma20_pct": round(ewma20, 2),
                        "garch_vol_pct": round(garch_vol, 2),
                        "egarch_vol_pct": round(egarch_vol, 2),
                        "var_pct": round(var_pct, 2),
                        "cvar_pct": round(cvar_pct, 2),
                        "var_usd": round(var_usd, 0),
                        "cvar_usd": round(cvar_usd, 0),
                    }
                )

            metrics_data.sort(key=lambda x: x["ticker"])
            return {"metrics": metrics_data, "conf_level": conf_level}
        except Exception as e:
            logger.error(f"Error calculating forecast metrics: {e}")
            return {"error": str(e)}

    def get_rolling_forecast(
        self,
        db: Session,
        tickers: List[str],
        model: str,
        window: int,
        username: str = "admin",
    ) -> Any:
        """Return list of {date, ticker, vol_pct} suitable for line charts."""
        ds = self._ds
        logger.debug(f"[ROLLING-FORECAST] Starting rolling forecast for user: {username}")
        logger.debug(f"[ROLLING-FORECAST] Tickers: {tickers}, model: {model}, window: {window}")
        try:
            if not tickers:
                return []

            lookback = 3 * 365
            ret_map = ds._get_return_series_map(db, tickers, lookback_days=lookback)

            common_dates = None
            for tkr in tickers:
                if tkr == "PORTFOLIO":
                    continue
                dates, rets = ret_map.get(tkr, ([], np.array([])))
                if len(rets) >= window:
                    if common_dates is None:
                        common_dates = set(dates)
                    else:
                        common_dates = common_dates.intersection(set(dates))

            # If only PORTFOLIO requested, seed common_dates from portfolio series
            if common_dates is None and "PORTFOLIO" in tickers:
                conc = ds.get_concentration_risk_data(db, username)
                if "error" not in conc and conc["portfolio_data"]:
                    w_map = {p["ticker"]: p["weight_frac"] for p in conc["portfolio_data"]}
                    active = list(w_map.keys())
                    ret_map.update(
                        ds._get_return_series_map(
                            db, list(set(active + ["SPY"])), lookback_days=lookback
                        )
                    )
                    dates_ref, R, active_aligned = ds._align_on_reference(
                        ret_map, active, ref_symbol="SPY", min_obs=window
                    )
                    dates_p, rp = ds._portfolio_series_with_coverage(
                        dates_ref, R, w_map, active_aligned, min_weight_cov=0.60
                    )
                    common_dates = set(dates_p)
                    logger.debug(
                        f"[ROLLING-FORECAST] Using portfolio dates as common_dates: "
                        f"{len(common_dates)} dates"
                    )
            if common_dates is None:
                return {"data": [], "model": model, "window": window}

            common_dates_sorted = sorted(list(common_dates))

            out: List[Dict[str, Any]] = []
            for tkr in tickers:
                if tkr == "PORTFOLIO":
                    continue
                dates, rets = ret_map.get(tkr, ([], np.array([])))
                if len(rets) < window:
                    continue

                date_idx = {d: i for i, d in enumerate(dates)}
                for date in common_dates_sorted:
                    if date in date_idx:
                        i = date_idx[date]
                        if i >= window:
                            sigma = forecast_sigma(rets[i - window:i], model) * 100
                            out.append(
                                {
                                    "date": date.isoformat() if hasattr(date, "isoformat") else str(date),
                                    "ticker": tkr,
                                    "vol_pct": round(float(sigma), 4),
                                }
                            )

            # PORTFOLIO line via portfolio-coverage aggregation
            if "PORTFOLIO" in tickers:
                conc = ds.get_concentration_risk_data(db, username)
                if "error" not in conc and conc["portfolio_data"]:
                    w_map = {p["ticker"]: p["weight_frac"] for p in conc["portfolio_data"]}
                    active = list(w_map.keys())
                    if any(a not in ret_map for a in active):
                        ret_map.update(
                            ds._get_return_series_map(
                                db, list(set(active + ["SPY"])), lookback_days=lookback
                            )
                        )
                    dates_ref, R, active_aligned = ds._align_on_reference(
                        ret_map, active, ref_symbol="SPY", min_obs=window
                    )
                    if len(dates_ref) >= window:
                        dates_p, rp = ds._portfolio_series_with_coverage(
                            dates_ref, R, w_map, active_aligned, min_weight_cov=0.60
                        )
                        portfolio_date_idx = {d: i for i, d in enumerate(dates_p)}
                        for date in common_dates_sorted:
                            if date in portfolio_date_idx:
                                j = portfolio_date_idx[date]
                                if j >= window:
                                    sigma = forecast_sigma(rp[j - window:j], model) * 100
                                    out.append(
                                        {
                                            "date": date.isoformat() if hasattr(date, "isoformat") else str(date),
                                            "ticker": "PORTFOLIO",
                                            "vol_pct": round(float(sigma), 4),
                                        }
                                    )

            out.sort(key=lambda d: (d["date"], d["ticker"]))
            common_date_range = ds._get_common_date_range(db, tickers)

            return {
                "data": out,
                "model": model,
                "window": window,
                "common_date_range": common_date_range,
            }
        except Exception as e:
            logger.error(f"Error calculating rolling forecast: {e}")
            return []
