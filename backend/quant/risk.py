"""
Algebra ryzyka portfela – żadnego SQL, żadnej logiki domenowej.
"""

import numpy as np


def clamp(x, lim=0.40):
    return np.clip(x, -abs(lim), abs(lim))


def build_cov(vol_vec, corr_mat):
    """Σ = D ρ D"""
    D = np.diag(vol_vec)
    return D @ corr_mat @ D


def risk_contribution(weights, cov):
    w = np.asarray(weights, dtype=float)
    var_p = w @ cov @ w
    if var_p <= 0:
        raise ValueError("σ² portfela ≤ 0")
    sigma_p = np.sqrt(var_p)

    mrc = (cov @ w) / sigma_p      # marginal RC
    rc  = w * mrc                  # absolutna
    pct = rc / sigma_p * 100       # %
    return mrc, pct, sigma_p
