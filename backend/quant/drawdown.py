"""Drawdown utilities.

Args/Inputs:
- returns: np.ndarray daily log or simple returns.

Provides:
- drawdown: series and maximum drawdown.

Returns:
- Tuple[np.ndarray, float].
"""

import numpy as np

def drawdown(returns: np.ndarray, kind: str = "log") -> tuple[np.ndarray, float]:
    """
    Calculate drawdown series and maximum drawdown
    Args:
        returns: np.ndarray daily returns
        kind: "log" or "simple" returns
    Returns: (drawdown_series, max_drawdown)
    """
    if len(returns) == 0:
        return np.array([]), 0.0
    
    r = np.asarray(returns, dtype=float)
    cum = np.cumprod(1.0 + r) if kind == "simple" else np.exp(np.cumsum(r))
    peak = np.maximum.accumulate(cum)
    dd = (cum - peak) / peak
    dd = np.minimum(dd, 0.0)  # numerical clip to ≤0
    max_dd = float(dd.min())
    return dd, max_dd
