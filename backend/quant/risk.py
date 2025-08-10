"""Portfolio risk algebra (no DB/domain dependencies).

Args/Inputs:
- vol_vec: volatilities vector, corr_mat: correlation matrix, weights, cov.

Provides:
- build_cov: Σ = D ρ D; risk_contribution: MRC, RC% and portfolio σ.

Returns:
- risk_contribution -> (mrc: np.ndarray, rc_pct: np.ndarray, sigma_p: float).
"""

import numpy as np


def clamp(x, lim=0.40):
    return np.clip(x, -abs(lim), abs(lim))


def build_cov(vol_vec, corr_mat):
    """Compute covariance matrix as Σ = D ρ D."""
    D = np.diag(vol_vec)
    return D @ corr_mat @ D


def risk_contribution(weights, cov):
    w = np.asarray(weights, dtype=float)
    cov = np.asarray(cov, dtype=float)
    
    # Sanity checks
    if cov.shape[0] != cov.shape[1] or cov.shape[0] != w.size:
        raise ValueError("Dimension mismatch weights/cov")
    cov = 0.5 * (cov + cov.T)  # ensure symmetry
    
    var_p = float(w @ cov @ w)
    if var_p <= 0 or not np.isfinite(var_p):
        raise ValueError("Portfolio variance must be positive and finite")
    sigma_p = np.sqrt(var_p)

    mrc = (cov @ w) / sigma_p      # marginal contribution
    rc  = w * mrc                  # absolute contribution
    pct = rc / sigma_p * 100       # percentage contribution
    return mrc, pct, sigma_p
