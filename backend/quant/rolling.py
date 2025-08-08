import pandas as pd
import numpy as np
from typing import Dict, Any, List
from .stats import basic_stats

ANNUAL = 252
ROLL_WIN = 21          # 1 miesiąc; front wysyła inny? – przekaż parametrem

def rolling_metric(ret: pd.DataFrame,
                   metric: str = "vol",      # vol | sharpe | return | drawdown …
                   window: int = ROLL_WIN,
                   ticker: str = "PORTFOLIO") -> pd.Series:
    """
    Zwraca serię rolling-metric dla wskazanego tickera.
    index = data, values = % lub bezw.
    """
    r = ret[ticker].dropna()

    if metric == "vol":
        f = lambda x: x.std(ddof=1)*np.sqrt(ANNUAL)*100
    elif metric == "sharpe":
        f = lambda x: basic_stats(x)["sharpe_ratio"]
    elif metric == "return":
        f = lambda x: x.mean()*ANNUAL*100
    elif metric == "maxdd":
        from .drawdown import drawdown
        f = lambda x: drawdown(x)[1]*100
    elif metric == "beta":
        from .linear import ols_beta
        def beta_func(x):
            if len(x) < window:
                return np.nan
            # Get benchmark data for same period
            benchmark = ret["SPY"].loc[x.index]  # Changed from NDX to SPY
            if len(benchmark) != len(x):
                return np.nan
            return ols_beta(x.values, benchmark.values)[0]
        f = beta_func
    else:
        raise ValueError("Nieobsługiwany metric")

    return r.rolling(window).apply(f, raw=False).dropna()
