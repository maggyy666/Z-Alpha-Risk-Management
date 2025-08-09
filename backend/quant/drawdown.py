"""Drawdown utilities.

Args/Inputs:
- returns: np.ndarray daily log or simple returns.

Provides:
- drawdown: series and maximum drawdown.

Returns:
- Tuple[np.ndarray, float].
"""

import numpy as np

def drawdown(returns: np.ndarray) -> tuple[np.ndarray, float]:
    """
    Calculate drawdown series and maximum drawdown
    Returns: (drawdown_series, max_drawdown)
    """
    if len(returns) == 0:
        return np.array([]), 0.0
    
    # Calculate cumulative returns
    cum = np.exp(np.cumsum(returns))
    
    # Calculate running maximum (peak)
    peak = np.maximum.accumulate(cum)
    
    # Calculate drawdown series
    dd = (cum - peak) / peak
    
    # Get maximum drawdown
    max_dd = float(np.min(dd))
    
    return dd, max_dd
