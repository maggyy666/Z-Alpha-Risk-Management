"""Correlation/covariance estimators.

Args/Inputs:
- R: returns matrix (T x N), lam for EWMA.

Provides:
- ewma_corr: EWMA correlation with PD enforcement and renormalized diagonal.

Returns:
- np.ndarray [N x N].
"""

import numpy as np

def ewma_corr(R: np.ndarray, lam: float = 0.94) -> np.ndarray:
    """
    EWMA correlation with weighted mean subtraction and PD enforcement.
    
    Args:
        R: returns matrix (T x N)
        lam: decay parameter (0 < lam < 1)
    
    Returns:
        correlation matrix (N x N) with diagonal = 1
    """
    if not (0.0 < lam < 1.0):
        raise ValueError("lam must be in (0,1)")

    R = np.asarray(R, dtype=float)
    T, N = R.shape if R.ndim == 2 else (0, 0)
    if T < 30 or N < 2:
        return np.eye(N)

    w = lam ** np.arange(T-1, -1, -1)
    w = w / w.sum()

    mu = (w[:, None] * R).sum(axis=0)
    Rc = R - mu

    S = (Rc * w[:, None]).T @ Rc

    std = np.sqrt(np.clip(np.diag(S), 1e-12, None))
    C = S / np.outer(std, std)

    C = 0.5 * (C + C.T)
    eigvals, eigvecs = np.linalg.eigh(C)
    eigvals = np.maximum(eigvals, 1e-6)
    C = eigvecs @ np.diag(eigvals) @ eigvecs.T

    d = np.sqrt(np.clip(np.diag(C), 1e-12, None))
    C = C / np.outer(d, d)
    np.fill_diagonal(C, 1.0)
    return C
