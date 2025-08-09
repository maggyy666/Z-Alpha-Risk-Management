"""One-dimensional parametric VaR/CVaR for log-returns.

Args/Inputs:
- sigma_daily, mu_daily, conf, method ('param').

Provides:
- var_cvar: negative VaR/CVaR percentages (loss conventions).
"""

import numpy as np
from scipy.stats import norm

_Z = norm.ppf

def var_cvar(sigma_daily: float,
             mu_daily: float = 0.0,
             conf: float = 0.95,
             method: str = "param") -> tuple[float, float]:
    """Return (VaR%, CVaR%) as negative numbers (loss convention)."""
    if method != "param":
        raise NotImplementedError

    z = _Z(conf)    # 1.64485 for 95%
    var = -(mu_daily + z * sigma_daily)
    cvar = -(mu_daily + sigma_daily * norm.pdf(z)/(1-conf))
    return var*100, cvar*100
