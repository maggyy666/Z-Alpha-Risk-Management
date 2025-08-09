"""Rolling metrics for time series.

Args/Inputs:
- ret: DataFrame of returns; metric: str; window; ticker symbol.

Provides:
- rolling_metric: rolling series for vol/sharpe/return/maxdd/beta.

Returns:
- pandas.Series aligned to dates.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List
from .stats import basic_stats

ANNUAL = 252
ROLL_WIN = 21

def rolling_metric(ret: pd.DataFrame,
                   metric: str = "vol",
                   window: int = ROLL_WIN,
                   ticker: str = "PORTFOLIO") -> pd.Series:
    """Return rolling metric series for the ticker (index=dates)."""
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
        raise ValueError("Unsupported metric")

    return r.rolling(window).apply(f, raw=False).dropna()
