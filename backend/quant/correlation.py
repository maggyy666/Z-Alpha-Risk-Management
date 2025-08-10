"""Pairwise correlation helpers.

Args/Inputs:
- R: returns matrix (T x N), threshold for high-corr pairs.

Provides:
- avg_and_high_corr: average correlation and count of pairs above threshold.

Returns:
- Tuple[avg: float, total_pairs: int, high_pairs: int].
"""

import numpy as np

def avg_and_high_corr(R: np.ndarray, threshold: float = 0.7) -> tuple[float, int, int]:
    """
    Calculate average correlation and count high correlation pairs
    Returns: (avg_correlation, total_pairs, high_correlation_pairs)
    """
    if R.size == 0 or R.shape[1] < 2 or R.shape[0] < 2:
        return 0.0, 0, 0

    var_mask = np.var(R, axis=0) > 1e-12
    R_sub = R[:, var_mask]
    if R_sub.shape[1] < 2 or R_sub.shape[0] < 2:
        return 0.0, 0, 0

    C = np.corrcoef(R_sub, rowvar=False)
    iu = np.triu_indices(C.shape[0], 1)
    vals = C[iu]
    vals = vals[np.isfinite(vals)]  # filter out NaN/Inf

    if vals.size == 0:
        return 0.0, 0, 0

    avg_correlation = float(np.mean(vals))
    total_pairs = int(vals.size)
    high_correlation_pairs = int((vals >= threshold).sum())
    return avg_correlation, total_pairs, high_correlation_pairs
