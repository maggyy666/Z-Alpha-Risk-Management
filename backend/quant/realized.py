import numpy as np
import pandas as pd
import scipy.stats as st
from typing import Dict, Any, List, Tuple
from .stats import basic_stats
from .drawdown import drawdown
from .var import var_cvar
from .linear import ols_beta

ANNUAL = 252   # dni handlowe

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
        mu_a   = s["mean_annual"]*100                 # %
        vol_a  = s["std_annual"]*100                  # %
        sharpe = s["sharpe_ratio"]
        sortino= s["sortino_ratio"]

        # -------------------------------------------------
        skew    = st.skew(r, bias=False)
        kurtosis= st.kurtosis(r, fisher=False, bias=False)  # 3=normal

        # ---------------- max DD -------------------------
        _, mdd = drawdown(r)
        max_dd = mdd*100                              # %

        # -------------- VaR / CVaR -----------------------
        var_pct, cvar_pct = var_cvar(s["std_daily"], s["mean_daily"], 0.95)

        # -------------- hit ratio ------------------------
        hit_ratio = (r > 0).mean()*100                # %

        # -------------- bety -----------------------------
        # Find benchmark index in active symbols
        benchmark_idx = None
        if active is not None:
            for j, symbol in enumerate(active):
                if symbol == benchmark_ndx:
                    benchmark_idx = j
                    break
        
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
            up_cap   = (r[up ].mean()/b[up ].mean() if up .any() else np.nan)*100
            down_cap = (r[down].mean()/b[down].mean() if down.any() else np.nan)*100
        else:
            up_cap = np.nan
            down_cap = np.nan

        # -------------- tracking error & IR -------------
        # TE = std dev różnicy
        if benchmark_idx is not None and R is not None:
            b = R[:, benchmark_idx]
            te = np.std(r - b, ddof=1) * np.sqrt(ANNUAL) * 100
            ir = (mu_a - np.mean(b)*ANNUAL*100) / te if te!=0 else np.nan
        else:
            te = np.nan
            ir = np.nan

        tbl.append([tkr, mu_a, vol_a, sharpe, sortino,
                    skew, kurtosis, max_dd,
                    var_pct, cvar_pct, hit_ratio,
                    beta_ndx, beta_spy,
                    up_cap, down_cap, te, ir])

    cols = ["Ticker", "Ann.Return%", "Ann.Volatility%", "Sharpe", "Sortino",
            "Skew", "Kurtosis", "Max Drawdown%",
            "VaR(5%)%", "CVaR(95%)%", "Hit Ratio%",
            "Beta (SPY)", "Beta (SPY)",  # Changed from NDX to SPY
            "Up Capture (SPY)%", "Down Capture (SPY)%",  # Changed from NDX to SPY
            "Tracking Error%", "Information Ratio"]
    return pd.DataFrame(tbl, columns=cols).set_index("Ticker")
