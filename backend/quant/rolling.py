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
    r = ret[ticker].astype(float)

    if metric == "vol":
        f = lambda x: x.std(ddof=1)*np.sqrt(ANNUAL)*100 if len(x.dropna()) >= window//2 else np.nan
    elif metric == "sharpe":
        f = lambda x: basic_stats(x.dropna())["sharpe_ratio"] if len(x.dropna()) >= window//2 else np.nan
    elif metric == "return":
        f = lambda x: x.mean()*ANNUAL*100 if len(x.dropna()) >= window//2 else np.nan
    elif metric == "maxdd":
        from .drawdown import drawdown
        f = lambda x: drawdown(x.dropna())[1]*100 if len(x.dropna()) >= window//2 else np.nan
    elif metric == "beta":
        # Fast beta calculation using rolling covariance/variance
        if "SPY" not in ret.columns:
            # Fallback: return NaN series if SPY not available
            return pd.Series(index=r.index, dtype=float)
        
        b = ret["SPY"].astype(float)
        aligned = r.dropna().index.intersection(b.dropna().index)
        if len(aligned) < window:
            # Not enough overlapping data
            return pd.Series(index=r.index, dtype=float)
            
        r = r.loc[aligned]
        b = b.loc[aligned]
        cov_rb = r.rolling(window).cov(b)
        var_b = b.rolling(window).var()
        ser = cov_rb / var_b
        
        # Reindex back to original index, filling missing values with NaN
        result = pd.Series(index=r.index, dtype=float)
        result.loc[ser.index] = ser
        return result
    else:
        raise ValueError("Unsupported metric")

    # Don't drop NaN at the beginning - let rolling handle it
    return r.rolling(window, min_periods=window//2).apply(f, raw=False)
