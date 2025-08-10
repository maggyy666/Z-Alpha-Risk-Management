"""Basic statistics helpers.

Args/Inputs:
- returns: np.ndarray daily returns.

Provides:
- basic_stats: daily/annual means/std, Sharpe, Sortino (NaN-safe).
"""

import numpy as np
from scipy.stats import norm

def basic_stats(returns: np.ndarray, risk_free_annual: float = 0.0) -> dict:
    """Return mean/std (daily/annual), Sharpe, Sortino. NaN-safe."""
    r = np.asarray(returns, dtype=float)
    r = r[np.isfinite(r)]
    if r.size < 2:
        return {k: 0.0 for k in ["mean_daily","std_daily","std_annual","mean_annual","sharpe_ratio","sortino_ratio"]}

    mean_d = float(np.mean(r))
    std_d  = float(np.std(r, ddof=1))
    std_a  = std_d * np.sqrt(252.0)
    mean_a = mean_d * 252.0

    sharpe = (mean_a - risk_free_annual) / std_a if std_a > 0 else 0.0

    neg = r[r < 0.0]
    if neg.size > 0:
        dd = float(np.std(neg, ddof=1)) * np.sqrt(252.0)
        sortino = (mean_a - risk_free_annual) / dd if dd > 0 else 0.0
    else:
        sortino = 0.0

    return {
        "mean_daily":   mean_d,
        "std_daily":    std_d,
        "std_annual":   std_a,
        "mean_annual":  mean_a,
        "sharpe_ratio": float(sharpe),
        "sortino_ratio": float(sortino),
    }



