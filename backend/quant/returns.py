import numpy as np
from typing import Dict, List, Tuple, Any

def stack_common_returns(ret_map: Dict[str, Tuple[List, np.ndarray]], symbols: List[str]) -> Tuple[List, np.ndarray, List[str]]:
    """
    Stack common returns from return map into matrix
    Returns: (common_dates, returns_matrix, active_symbols)
    """
    if not symbols:
        return [], np.empty((0, 0)), []
    
    # Find active symbols (with data)
    active = [s for s in symbols if s in ret_map and len(ret_map[s][0]) > 0]
    if not active:
        return [], np.empty((0, 0)), []
    
    # Collect date sets
    sets = [set(ret_map[s][0]) for s in active]
    if not sets:
        return [], np.empty((0, 0)), []
    
    # Find common dates
    common = sorted(list(set.intersection(*sets)))
    if not common:
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
