"""Returns utilities.

Args/Inputs:
- R: np.ndarray of returns (T x N), threshold for high-correlation flags.

Provides:
- avg_and_high_corr: average pairwise correlation and count of pairs above threshold.

Returns:
- Tuple[avg_corr: float, total_pairs: int, high_pairs: int].
"""

import numpy as np
from typing import Dict, List, Tuple, Any

def stack_common_returns(ret_map: Dict[str, Tuple[List, np.ndarray]], symbols: List[str], min_obs: int = 30) -> Tuple[List, np.ndarray, List[str]]:
    """
    Stack common returns from return map into matrix
    Returns: (common_dates, returns_matrix, active_symbols)
    """
    if not symbols:
        return [], np.empty((0, 0)), []
    
    # 1. Odfiltruj puste / zbyt krótkie serie
    ok = [s for s in symbols if s in ret_map and len(ret_map[s][1]) >= min_obs]
    if len(ok) < 2:
        print(f"Warning: Only {len(ok)} tickers have sufficient data (min_obs={min_obs})")
        return [], np.empty((0, 0)), []
    
    # Find active symbols (with data)
    active = ok
    if not active:
        return [], np.empty((0, 0)), []
    
    # Collect date sets
    sets = [set(ret_map[s][0]) for s in active]
    if not sets:
        return [], np.empty((0, 0)), []
    
    # Find common dates
    common = sorted(list(set.intersection(*sets)))
    if not common:
        print(f"Warning: No common dates found for {active}")
        return [], np.empty((0, 0)), []
    
    # Map date->idx for each symbol
    idx_maps = {}
    for s in active:
        dates, returns = ret_map[s]
        idx_maps[s] = {d: i for i, d in enumerate(dates)}
    
    # Build returns matrix R [T x N]
    T, N = len(common), len(active)
    R = np.empty((T, N))
    
    for j, symbol in enumerate(active):
        dates, returns = ret_map[symbol]
        idx_map = idx_maps[symbol]
        
        for i, date in enumerate(common):
            if date in idx_map:
                R[i, j] = returns[idx_map[date]]
            else:
                R[i, j] = 0.0  # or np.nan if you prefer
    
    return common, R, active
