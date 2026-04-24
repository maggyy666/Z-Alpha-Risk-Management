"""Return-series alignment helpers.

Given a set of symbols, these helpers pull recent log returns, align them on
a reference calendar (usually SPY), build NaN-tolerant matrices for analytics,
and compute pairwise stats. No IBKR access here -- everything reads via
MarketDataService which hits the DB.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import numpy as np
from sqlalchemy.orm import Session

from quant.returns import stack_common_returns
from services.market_data_service import MarketDataService


class ReturnsService:
    def __init__(self, market_data: MarketDataService):
        self.market_data = market_data

    def get_return_series_map(
        self, db: Session, symbols: List[str], lookback_days: int = 120
    ) -> Dict[str, Tuple[List, np.ndarray]]:
        """symbol -> (dates, returns) trimmed to last ~lookback_days."""
        ret_map: Dict[str, Tuple[List, np.ndarray]] = {}
        for s in symbols:
            if s in ("PORTFOLIO", None, ""):
                ret_map[s] = ([], np.array([]))
                continue

            print(f"Debug: Getting data for {s}")
            dates, closes = self.market_data.get_close_series(db, s)
            print(f"Debug: {s} - dates: {len(dates)}, closes: {len(closes)}")
            if len(closes) < 2:
                print(f"Debug: {s} - insufficient data")
                ret_map[s] = ([], np.array([]))
                continue
            dates = dates[-(lookback_days + 2):]
            closes = closes[-(lookback_days + 2):]
            rd, r = self.market_data.log_returns_from_series(dates, closes)
            print(f"Debug: {s} - returns: {len(r)}")
            ret_map[s] = (rd, r)
        return ret_map

    @staticmethod
    def align_on_reference(
        ret_map: Dict[str, Tuple[List, np.ndarray]],
        symbols: List[str],
        ref_symbol: str = "SPY",
        min_obs: int = 40,
    ) -> Tuple[List, np.ndarray, List[str]]:
        """Align on reference calendar. Returns (dates_ref, M[T x N] with NaN, active_syms).

        Columns = symbols with >= min_obs overlapping points against ref_symbol.
        """
        if ref_symbol not in ret_map:
            return [], np.empty((0, 0)), []
        dates_ref, _r_ref = ret_map[ref_symbol]
        if len(dates_ref) == 0:
            return [], np.empty((0, 0)), []

        idx_ref = {d: i for i, d in enumerate(dates_ref)}
        T = len(dates_ref)
        cols: List[str] = []
        X: List[np.ndarray] = []

        for s in symbols:
            if s == ref_symbol or s not in ret_map:
                continue
            dts, r = ret_map[s]
            if len(r) == 0:
                continue
            x = np.full(T, np.nan, dtype=float)
            idx_s = {d: i for i, d in enumerate(dts)}
            common = [d for d in dates_ref if d in idx_s]
            if len(common) >= min_obs:
                for d in common:
                    x[idx_ref[d]] = r[idx_s[d]]
                cols.append(s)
                X.append(x)

        if not cols:
            return [], np.empty((0, 0)), []
        return dates_ref, np.column_stack(X), cols

    @staticmethod
    def portfolio_series_with_coverage(
        dates: List,
        R: np.ndarray,
        weights_map: Dict[str, float],
        symbols: List[str],
        min_weight_cov: float = 0.6,
    ) -> Tuple[List, np.ndarray]:
        """Daily portfolio return, renormalizing by available names.

        R is [T x N] possibly with NaN. A row is kept only when the sum of
        weights of non-NaN columns >= min_weight_cov.
        """
        if R.size == 0:
            return [], np.array([])
        w_full = np.array([weights_map.get(s, 0.0) for s in symbols], dtype=float)
        total = w_full.sum()
        w_full = w_full / (total if total > 0 else 1.0)

        rp: List[float] = []
        used_dates: List = []
        for t in range(R.shape[0]):
            row = R[t, :]
            mask = np.isfinite(row)
            cov = w_full[mask].sum()
            if cov >= min_weight_cov and mask.any():
                w_t = w_full[mask] / cov
                rp.append(float((row[mask] * w_t).sum()))
                used_dates.append(dates[t])
        return used_dates, np.array(rp, dtype=float)

    @staticmethod
    def pairwise_corr_nan_safe(R: np.ndarray, min_periods: int = 30) -> Tuple[float, int, int]:
        """Return (avg_corr, total_pairs, high_pairs>=0.7) on pairwise-common obs."""
        if R.size == 0:
            return 0.0, 0, 0
        N = R.shape[1]
        vals: List[float] = []
        high = 0
        for i in range(N):
            xi = R[:, i]
            for j in range(i + 1, N):
                xj = R[:, j]
                m = np.isfinite(xi) & np.isfinite(xj)
                if m.sum() >= min_periods:
                    c = np.corrcoef(xi[m], xj[m])[0, 1]
                    if np.isfinite(c):
                        vals.append(c)
                        if c >= 0.7:
                            high += 1
        if not vals:
            return 0.0, 0, 0
        return float(np.mean(vals)), len(vals), int(high)

    @staticmethod
    def intersect_and_stack(
        ret_map: Dict[str, Any], symbols: List[str]
    ) -> Tuple[List, np.ndarray, List[str]]:
        """Wrapper over quant.returns.stack_common_returns with debug prints."""
        print(f"Debug: Intersecting {symbols}")
        print(f"Debug: ret_map keys: {list(ret_map.keys())}")
        for s in symbols:
            if s in ret_map:
                dates, returns = ret_map[s]
                print(f"Debug: {s} - dates: {len(dates)}, returns: {len(returns)}")
            else:
                print(f"Debug: {s} - not in ret_map")
        result = stack_common_returns(ret_map, symbols)
        print(
            f"Debug: Result - dates: {len(result[0])}, R shape: {result[1].shape}, active: {result[2]}"
        )
        return result

    def get_common_date_range(self, db: Session, symbols: List[str]) -> Dict[str, Any]:
        """Find the (min, max) date range observed across the given tickers."""
        try:
            all_dates: List = []
            for symbol in symbols:
                dates, _ = self.market_data.get_close_series(db, symbol)
                if dates:
                    all_dates.extend(dates)

            if not all_dates:
                return {"start_date": None, "end_date": None, "total_days": 0}

            min_date = min(all_dates)
            max_date = max(all_dates)
            total_days = (max_date - min_date).days if (min_date and max_date) else 0

            return {
                "start_date": min_date.isoformat() if min_date else None,
                "end_date": max_date.isoformat() if max_date else None,
                "total_days": total_days,
            }
        except Exception as e:
            print(f"Error getting common date range: {e}")
            return {"start_date": None, "end_date": None, "total_days": 0}
