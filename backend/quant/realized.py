"""Realized performance/risk metrics.

Args/Inputs:
- ret: DataFrame of daily returns; R: np.ndarray (T x N); active tickers list.

Provides:
- compute_realized_metrics: per-ticker table (annual return/vol, Sharpe, Sortino,
  skew, kurtosis, max DD, VaR/CVaR, hit ratio, beta, captures, TE, IR).

Returns:
- pandas.DataFrame indexed by ticker.
"""

import numpy as np
import pandas as pd
import scipy.stats as st
from typing import Dict, Any, List, Tuple
from .stats import basic_stats
from .drawdown import drawdown
from .var import var_cvar
from .linear import ols_beta

ANNUAL = 252
LOG = True

def to_simple(x):
    """Convert log returns to simple returns"""
    return np.exp(x) - 1 if LOG else x

def annual_mean(mu_d):
    """Convert daily mean to annual mean"""
    return (np.exp(mu_d*ANNUAL) - 1) if LOG else mu_d*ANNUAL

def compute_realized_metrics(ret: pd.DataFrame,
       benchmark_ndx: str = "SPY",
                           benchmark_spy: str = "SPY",
                           R: np.ndarray = None,
                           active: List[str] = None) -> pd.DataFrame:
    """Compute realized metrics table for active symbols.

    Args:
      ret: DataFrame of daily (log) returns; columns are tickers (incl. SPY/PORTFOLIO).
      benchmark_ndx: benchmark symbol.
      benchmark_spy: kept for compatibility.
      R: returns matrix (T x N) aligned to active.
      active: list of tickers.

    Returns:
      DataFrame with performance and risk measures per ticker.
    """
    
    tbl = []
    if active is None:
        return pd.DataFrame()
        
    for i, tkr in enumerate(active):
        if i >= R.shape[1]:
            continue
            
        r = R[:, i]  # Use the i-th column from R matrix
        
        if len(r) < 30:  # Minimum observations
            continue

        s = basic_stats(r)
        
        mu_a   = annual_mean(s["mean_daily"]) * 100
        vol_a  = s["std_daily"] * np.sqrt(ANNUAL) * 100
        sharpe = s["sharpe_ratio"]
        sortino= s["sortino_ratio"]

        skew    = st.skew(r, bias=False)
        kurtosis= st.kurtosis(r, fisher=False, bias=False)

        _, mdd = drawdown(r)
        max_dd = mdd * 100

        var_pct, cvar_pct = var_cvar(s["std_daily"], s["mean_daily"], 0.95)

        hit_ratio = (r > 0).mean() * 100

        # Beta vs benchmark
        benchmark_idx = None
        if active is not None:
            try:
                benchmark_idx = active.index(benchmark_ndx)
            except ValueError:
                benchmark_idx = None
        
        if benchmark_idx is not None and R is not None:
            beta_ndx = ols_beta(r, R[:, benchmark_idx])[0]
            beta_spy = ols_beta(r, R[:, benchmark_idx])[0]  # Same for SPY
        else:
            beta_ndx = np.nan
            beta_spy = np.nan

        # Up/Down capture
        if benchmark_idx is not None and R is not None:
            b = R[:, benchmark_idx]
            up   = b > 0
            down = b < 0
            
            # Cumulative returns during up/down periods (log to simple)
            if up.any():
                # Up capture: ratio of cumulative returns during up periods
                r_up_cum = np.exp(r[up].sum()) - 1
                b_up_cum = np.exp(b[up].sum()) - 1
                up_cap = (r_up_cum / b_up_cum * 100) if b_up_cum != 0 else np.nan
            else:
                up_cap = np.nan
                
            if down.any():
                # Down capture: ratio of cumulative returns during down periods
                r_down_cum = np.exp(r[down].sum()) - 1
                b_down_cum = np.exp(b[down].sum()) - 1
                down_cap = (r_down_cum / abs(b_down_cum) * 100) if b_down_cum != 0 else np.nan
            else:
                down_cap = np.nan
        else:
            up_cap = np.nan
            down_cap = np.nan

        # Tracking error & Information Ratio
        if benchmark_idx is not None and R is not None:
            b = R[:, benchmark_idx]
            te = np.std(r - b, ddof=1) * np.sqrt(ANNUAL) * 100
            
            # Poprawka dla log-zwrotów w Information Ratio
            mu_b = annual_mean(np.mean(b))
            ir = (mu_a/100 - mu_b) / (te/100) if te != 0 else np.nan
        else:
            te = np.nan
            ir = np.nan

        tbl.append([tkr, mu_a, vol_a, sharpe, sortino,
                    skew, kurtosis, max_dd,
                    var_pct, cvar_pct, hit_ratio,
                    beta_ndx,
                    up_cap, down_cap, te, ir])

    cols = ["Ticker", "Ann.Return%", "Ann.Volatility%", "Sharpe", "Sortino",
            "Skew", "Kurtosis", "Max Drawdown%",
            "VaR(5%)%", "CVaR(95%)%", "Hit Ratio%",
            "Beta (SPY)",  # Usunięto duplikat
            "Up Capture (SPY)%", "Down Capture (SPY)%",  # Changed from NDX to SPY
            "Tracking Error%", "Information Ratio"]
    return pd.DataFrame(tbl, columns=cols).set_index("Ticker")
