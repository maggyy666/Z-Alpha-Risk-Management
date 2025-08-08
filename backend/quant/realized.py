import numpy as np
import pandas as pd
import scipy.stats as st
from typing import Dict, Any, List, Tuple
from .stats import basic_stats
from .drawdown import drawdown
from .var import var_cvar
from .linear import ols_beta

ANNUAL = 252   # dni handlowe
LOG = True     # czy używamy log-zwrotów

def to_simple(x):
    """Convert log returns to simple returns"""
    return np.exp(x) - 1 if LOG else x

def annual_mean(mu_d):
    """Convert daily mean to annual mean"""
    return (np.exp(mu_d*ANNUAL) - 1) if LOG else mu_d*ANNUAL

def compute_realized_metrics(ret: pd.DataFrame,
                           benchmark_ndx: str = "SPY",  # Changed from NDX to SPY
                           benchmark_spy: str = "SPY",
                           R: np.ndarray = None,
                           active: List[str] = None) -> pd.DataFrame:
    """
    ret – DataFrame dziennych log-stop zwrotu; kolumny = tickery (+ SPY, PORTFOLIO)
    R – numpy array [T x N] z zwrotami
    active – lista aktywnych symboli
    Zwraca tabelę z kolumnami jak na screenie.
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

        # ------------- podstawowe staty -----------------
        s = basic_stats(r)                            # mean_daily, std_daily, sharpe, sortino
        
        # Poprawka dla log-zwrotów
        mu_a   = annual_mean(s["mean_daily"])*100    # %
        vol_a  = s["std_daily"]*np.sqrt(ANNUAL)*100  # % (dla log ≈ OK)
        sharpe = s["sharpe_ratio"]
        sortino= s["sortino_ratio"]

        # -------------------------------------------------
        skew    = st.skew(r, bias=False)
        kurtosis= st.kurtosis(r, fisher=False, bias=False)  # 3=normal

        # ---------------- max DD -------------------------
        _, mdd = drawdown(r)
        max_dd = mdd*100                              # %

        # -------------- VaR / CVaR -----------------------
        # Dla log-zwrotów przekazujemy większe mu, sigma
        var_pct, cvar_pct = var_cvar(s["std_daily"], s["mean_daily"], 0.95)

        # -------------- hit ratio ------------------------
        hit_ratio = (r > 0).mean()*100                # %

        # -------------- bety -----------------------------
        # Find benchmark index in active symbols
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

        # -------------- up / down capture ---------------
        if benchmark_idx is not None and R is not None:
            b = R[:, benchmark_idx]
            up   = b > 0
            down = b < 0
            
            # Calculate cumulative returns for up/down periods - POPRAWKA DLA LOG-ZWROTÓW
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
                # Używamy abs() dla down capture żeby znak benchmarku nie odwracał sensu
                down_cap = (r_down_cum / abs(b_down_cum) * 100) if b_down_cum != 0 else np.nan
            else:
                down_cap = np.nan
        else:
            up_cap = np.nan
            down_cap = np.nan

        # -------------- tracking error & IR -------------
        # TE = std dev różnicy
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
