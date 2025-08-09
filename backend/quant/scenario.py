"""Scenario analytics.

Args/Inputs:
- R: scenario returns (T x N), w: weights (N,).

Provides:
- scenario_pnl: total return (%) and max drawdown (%) for the scenario.
"""

import numpy as np
from .drawdown import drawdown

def scenario_pnl(R: np.ndarray, w: np.ndarray) -> tuple[float, float]:
    """
    Calculate scenario PnL and maximum drawdown
    Returns: (return_pct, max_drawdown_pct)
    """
    if R.size == 0 or len(w) == 0:
        return 0.0, 0.0
    
    # Portfolio returns for the scenario
    rp = R @ w
    
    # Calculate total return
    total_return = np.exp(np.sum(rp)) - 1
    return_pct = float(total_return * 100)  # Convert to percentage
    
    # Calculate maximum drawdown
    _, max_dd = drawdown(rp)
    max_drawdown_pct = float(max_dd * 100)  # Convert to percentage
    
    return return_pct, max_drawdown_pct
