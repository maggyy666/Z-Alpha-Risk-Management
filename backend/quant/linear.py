"""Linear models helpers.

Args/Inputs:
- y, x: np.ndarray aligned series.

Provides:
- ols_beta: OLS beta and R^2 for y on x.

Returns:
- Tuple[beta: float, r_squared: float].
"""

import numpy as np
from numpy.linalg import LinAlgError
from typing import Tuple

def ols_beta(y: np.ndarray, x: np.ndarray) -> Tuple[float, float]:
    """
    OLS regression: y = α + βx + ε
    Returns: (beta, r_squared)
    """
    if len(y) != len(x) or len(y) < 2:
        return 0.0, 0.0
    
    # Guard for zero-variance x
    if np.allclose(np.var(x), 0.0):
        return 0.0, 0.0
    
    # Add constant for regression
    X = np.column_stack([np.ones(len(x)), x])
    
    try:
        coef = np.linalg.lstsq(X, y, rcond=None)[0]
        beta = float(coef[1])
        y_pred = X @ coef
        ss_res = float(np.sum((y - y_pred) ** 2))
        ss_tot = float(np.sum((y - np.mean(y)) ** 2))
        r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
        r2 = float(np.clip(r2, 0.0, 1.0))
        return beta, r2
    except LinAlgError:
        return 0.0, 0.0
