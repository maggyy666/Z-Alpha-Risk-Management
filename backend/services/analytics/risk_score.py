"""Risk scoring and portfolio summary aggregators.

These are the "dashboard" endpoints -- they don't compute new primitives,
they compose outputs from concentration / volatility / forecast / regime
analytics into a unified score and a summary card.

Because of the heavy cross-analytics composition, everything goes through
the DataService facade (ds_ref) rather than wiring each peer analytics
service individually (construction order stays simple).
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import numpy as np
from sqlalchemy.orm import Session

from quant.drawdown import drawdown
from quant.linear import ols_beta
from quant.scoring import risk_mix
from quant.volatility import annualized_vol

import logging

logger = logging.getLogger(__name__)

_RISK_SCORE_WEIGHTS = {
    "concentration": 0.25,
    "volatility": 0.20,
    "factor": 0.20,
    "correlation": 0.15,
    "market": 0.10,
    "stress": 0.10,
}

class RiskScoreAnalytics:
    def __init__(self, ds_ref, normalization: Dict[str, float]):
        self._ds = ds_ref
        self._normalization = normalization

    def get_risk_scoring(self, db: Session, username: str = "admin") -> Dict[str, Any]:
        """Aggregated risk score: 7 component scores + contribution percentages."""
        ds = self._ds
        logger.debug(f"[RISK-SCORING] Starting risk scoring for user: {username}")

        logger.debug("[RISK-SCORING] Getting concentration risk data...")
        conc = ds.get_concentration_risk_data(db, username)
        if "error" in conc:
            logger.debug(f"[RISK-SCORING] Error in concentration risk: {conc['error']}")
            return {"error": conc["error"]}
        positions = conc["portfolio_data"]
        if not positions:
            logger.debug("[RISK-SCORING] No positions found")
            return {"error": "No positions"}
        tickers = [p["ticker"] for p in positions]
        w = np.array([p["weight_frac"] for p in positions], dtype=float)
        logger.debug(f"[RISK-SCORING] Portfolio tickers: {tickers}, weights sum: {w.sum():.4f}")

        factor_proxies = {"MOMENTUM": "MTUM", "SIZE": "IWM", "VALUE": "VLUE", "QUALITY": "QUAL"}
        needed = list(set(tickers + ["SPY"] + list(factor_proxies.values())))
        logger.debug(f"[RISK-SCORING] Getting return series for: {needed}")
        ret_map = ds._get_return_series_map(db, needed, lookback_days=180)

        logger.debug("[RISK-SCORING] Aligning returns on SPY calendar...")
        dates_ref, R_all, active = ds._align_on_reference(
            ret_map, tickers + ["SPY"], ref_symbol="SPY", min_obs=40
        )
        if R_all.size == 0 or len(dates_ref) < 40:
            logger.debug("[RISK-SCORING] Insufficient overlapping history (vs SPY)")
            return {"error": "Insufficient overlapping history (vs SPY)"}
        logger.debug(f"[RISK-SCORING] Aligned data shape: {R_all.shape}, active symbols: {active}")

        w_map = {p["ticker"]: p["weight_frac"] for p in positions}
        dates_win, rp = ds._portfolio_series_with_coverage(
            dates_ref, R_all, w_map, active, min_weight_cov=0.60
        )
        if len(rp) < 40:
            return {"error": "Too few portfolio days after coverage filter"}

        d_spy, r_spy_full = ret_map.get("SPY", ([], np.array([])))
        idx_spy = {d: i for i, d in enumerate(d_spy)}
        r_spy = np.array(
            [r_spy_full[idx_spy[d]] for d in dates_win if d in idx_spy], dtype=float
        )
        dates_common = [d for d in dates_win if d in idx_spy]
        rp_win = np.array([rp[dates_win.index(d)] for d in dates_common], dtype=float)
        if len(rp_win) < 30 or len(r_spy) < 30:
            return {"error": "Insufficient market overlap"}

        # Raw metrics
        sigma_ann = annualized_vol(rp_win)
        beta_mkt = ols_beta(rp_win, r_spy)[0]

        betas: Dict[str, float] = {}
        for fac, etf in factor_proxies.items():
            d_f, r_f_full = ret_map.get(etf, ([], np.array([])))
            f_idx = {d: i for i, d in enumerate(d_f)}
            dates_fac = [d for d in dates_common if d in f_idx]
            if len(dates_fac) < 30:
                betas[fac] = 0.0
                continue
            rf = np.array([r_f_full[f_idx[d]] for d in dates_fac], dtype=float)
            rs = np.array([r_spy[dates_common.index(d)] for d in dates_fac], dtype=float)
            rp_fac = np.array(
                [rp_win[dates_common.index(d)] for d in dates_fac], dtype=float
            )
            betas[fac] = ols_beta(rp_fac, rf - rs)[0]

        win = min(60, len(dates_ref))
        R_win = R_all[-win:, :]
        avg_corr, pairs, high_pairs = ds._pairwise_corr_nan_safe(R_win, min_periods=30)

        _, max_dd = drawdown(rp_win)

        hhi = float(conc["concentration_metrics"]["herfindahl_index"])
        neff = float(conc["concentration_metrics"]["effective_positions"])

        # Worst historical scenario -> stress_loss_pct
        stress = ds.get_historical_scenarios(db, username)
        worst_loss = 0.0
        if "results" in stress:
            losses = [-r["return_pct"] for r in stress["results"] if r["return_pct"] < 0]
            if losses:
                worst_loss = max(losses) / 100.0

        raw_metrics = {
            "hhi": hhi,
            "vol_ann_pct": sigma_ann * 100,
            "beta_market": beta_mkt,
            "avg_pair_corr": avg_corr,
            "max_drawdown_pct": max_dd * 100,
            "factor_l1": sum(abs(betas[k]) for k in betas),
            "stress_loss_pct": worst_loss,
        }

        scores, contrib_pct = risk_mix(raw_metrics, self._normalization, _RISK_SCORE_WEIGHTS)

        alerts: List[Dict[str, str]] = []
        if max_dd < -0.2:
            alerts.append(
                {
                    "severity": "HIGH",
                    "text": f"Drawdown Risk: Maximum drawdown ({max_dd * 100:.1f}%) is significant",
                }
            )
        elif max_dd < -0.1:
            alerts.append(
                {
                    "severity": "MEDIUM",
                    "text": f"Drawdown Risk: Maximum drawdown ({max_dd * 100:.1f}%) is significant",
                }
            )
        if abs(beta_mkt) > 0.8:
            alerts.append(
                {
                    "severity": "MEDIUM",
                    "text": f"Factor Exposure: High exposure to MARKET factor (beta: {beta_mkt:.2f})",
                }
            )
        for fac in ("SIZE", "VALUE", "MOMENTUM", "QUALITY"):
            b = betas.get(fac, 0.0)
            if abs(b) > 0.5:
                alerts.append(
                    {
                        "severity": "MEDIUM",
                        "text": f"Factor Exposure: High exposure to {fac} factor (beta: {b:.2f})",
                    }
                )
        if high_pairs >= 2:
            alerts.append(
                {
                    "severity": "MEDIUM",
                    "text": f"Correlation Risk: {high_pairs} pairs with correlation > 0.7",
                }
            )

        recs: List[str] = []
        top_comp = max(contrib_pct, key=contrib_pct.get)
        if top_comp == "concentration" and neff < 8:
            recs.append("Reduce concentration: increase number of effective positions (>8).")
        if abs(beta_mkt) > 0.8:
            recs.append("Trim market beta towards 0.6-0.8 (hedge or rotate).")
        if avg_corr > 0.5:
            recs.append("Add diversifiers to lower average pairwise correlation (<0.4).")

        return {
            "score_weights": _RISK_SCORE_WEIGHTS,
            "component_scores": scores,
            "risk_contribution_pct": contrib_pct,
            "alerts": alerts,
            "recommendations": recs,
            "raw_metrics": {
                "hhi": hhi,
                "n_eff": neff,
                "vol_ann_pct": sigma_ann * 100.0,
                "beta_market": beta_mkt,
                "avg_pair_corr": avg_corr,
                "pairs_total": pairs,
                "pairs_high_corr": high_pairs,
                "max_drawdown_pct": max_dd * 100.0,
            },
        }

    def get_portfolio_summary(self, db: Session, username: str = "admin") -> Dict[str, Any]:
        """Dashboard aggregator: risk score + concentration + forecast + CVaR total."""
        ds = self._ds
        logger.debug(f"[PORTFOLIO-SUMMARY] Starting portfolio summary for user: {username}")
        try:
            logger.debug("[PORTFOLIO-SUMMARY] Getting risk scoring data...")
            risk_data = self.get_risk_scoring(db, username)
            if "error" in risk_data:
                logger.debug(f"[PORTFOLIO-SUMMARY] Warning: Risk scoring failed: {risk_data['error']}")
                risk_data = {
                    "component_scores": {"overall": 0.5},
                    "risk_contribution_pct": {
                        "market": 25.0,
                        "concentration": 25.0,
                        "volatility": 25.0,
                        "liquidity": 25.0,
                    },
                }

            logger.debug("[PORTFOLIO-SUMMARY] Getting concentration risk data...")
            conc_data = ds.get_concentration_risk_data(db, username)
            if "error" in conc_data:
                logger.debug(f"[PORTFOLIO-SUMMARY] Warning: Concentration risk failed: {conc_data['error']}")
                conc_data = {
                    "total_market_value": 0,
                    "portfolio_data": [],
                    "concentration_metrics": {"largest_position": 0, "top_3_concentration": 0},
                }

            logger.debug("[PORTFOLIO-SUMMARY] Getting forecast risk contribution (EGARCH)...")
            forecast_contribution = ds.get_forecast_risk_contribution(
                db, username, vol_model="EGARCH"
            )
            if "error" in forecast_contribution:
                logger.debug(
                    f"[PORTFOLIO-SUMMARY] Warning: Forecast risk contribution failed: "
                    f"{forecast_contribution['error']}"
                )
                forecast_contribution = {
                    "portfolio_vol": 0.15,
                    "tickers": ["N/A"],
                    "marginal_rc_pct": [0.0],
                }

            logger.debug("[PORTFOLIO-SUMMARY] Getting forecast metrics...")
            forecast_metrics = ds.get_forecast_metrics(db, username)
            if "error" in forecast_metrics:
                logger.debug(
                    f"[PORTFOLIO-SUMMARY] Warning: Forecast metrics failed: "
                    f"{forecast_metrics['error']}"
                )
                forecast_metrics = {"metrics": []}

            total_cvar_usd = sum(item.get("cvar_usd", 0) for item in forecast_metrics.get("metrics", []))
            total_market_value = conc_data.get("total_market_value", 1)
            total_cvar_pct = (
                (total_cvar_usd / total_market_value * 100) if total_market_value > 0 else 0
            )

            overall_score = risk_data.get("component_scores", {}).get("overall", 0) * 100
            if not (0.0 <= overall_score <= 100.0):
                logger.warning(
                    f"Warning: Overall score out of range: {overall_score}, clipping to [0,100]"
                )
                overall_score = max(0, min(overall_score, 100))

            if overall_score <= 33:
                risk_level = "LOW"
            elif overall_score <= 66:
                risk_level = "MEDIUM"
            else:
                risk_level = "HIGH"

            risk_contribution = risk_data.get("risk_contribution_pct", {})
            highest_risk = (
                max(risk_contribution.items(), key=lambda x: x[1])
                if risk_contribution
                else ("", 0)
            )
            high_risk_components = sum(1 for v in risk_contribution.values() if v > 25)

            portfolio_positions = conc_data.get("portfolio_data", [])

            flags: Dict[str, bool] = {}
            volatility_egarch = forecast_contribution.get("portfolio_vol", 0)
            if volatility_egarch > 3.0:
                flags["high_vol"] = True
                logger.warning(f"Warning: EGARCH volatility {volatility_egarch * 100:.1f}% > 300%")
            if overall_score > 1.0:
                flags["high_risk_score"] = True
                logger.warning(f"Warning: Risk score {overall_score:.1f}% > 100%")
            if total_cvar_pct < -10.0:
                flags["high_cvar"] = True
                logger.warning(f"Warning: CVaR {total_cvar_pct:.1f}% < -10%")

            top_ticker, top_pct = self.get_top_risk_contributor(forecast_contribution)

            return {
                "risk_score": {
                    "overall_score": round(overall_score, 1),
                    "risk_level": risk_level,
                    "highest_risk_component": highest_risk[0],
                    "highest_risk_percentage": round(highest_risk[1], 1),
                    "high_risk_components_count": high_risk_components,
                },
                "portfolio_overview": {
                    "total_market_value": conc_data.get("total_market_value", 0),
                    "total_positions": len(portfolio_positions),
                    "largest_position": round(
                        conc_data.get("concentration_metrics", {}).get("largest_position", 0), 1
                    ),
                    "top_3_concentration": round(
                        conc_data.get("concentration_metrics", {}).get("top_3_concentration", 0), 1
                    ),
                    "volatility_egarch": round(
                        forecast_contribution.get("portfolio_vol_pct", volatility_egarch * 100), 1
                    ),
                    "cvar_percentage": round(total_cvar_pct, 1),
                    "cvar_usd": round(total_cvar_usd, 0),
                    "top_risk_contributor": {
                        "ticker": top_ticker,
                        "vol_contribution_pct": top_pct,
                    },
                },
                "portfolio_positions": portfolio_positions,
                "flags": flags,
            }
        except Exception as e:
            logger.error(f"Error getting portfolio summary: {e}")
            return {"error": str(e)}

    @staticmethod
    def get_top_risk_contributor(forecast_contribution: Dict[str, Any]) -> Tuple[str, float]:
        """Return (ticker, pct) of the position with the largest total_rc_pct,
        skipping the synthetic PORTFOLIO row if present."""
        tickers = forecast_contribution.get("tickers", [])
        trc = forecast_contribution.get("total_rc_pct", [])

        start = 1 if tickers and tickers[0] == "PORTFOLIO" else 0
        if trc and len(trc) > start:
            idx_rel = int(np.argmax(trc[start:]))
            idx = start + idx_rel
            top_ticker = tickers[idx]
            top_pct = float(trc[idx])
        else:
            top_ticker, top_pct = "N/A", 0.0
        return top_ticker, round(top_pct, 1)
