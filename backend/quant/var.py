import numpy as np
from scipy.stats import norm

_Z = norm.ppf  # skrót

def var_cvar(sigma_daily: float,
             mu_daily: float = 0.0,
             conf: float = 0.95,
             method: str = "param") -> tuple[float, float]:
    """
    Zwraca (VaR_pct, CVaR_pct) ujemne liczby (!) – strata.
    Założenie: jednowymiarowe rozkłady log-zwrotów.
    """
    if method != "param":
        raise NotImplementedError

    z = _Z(conf)           # 1.64485 dla 95 %
    var = -(mu_daily + z * sigma_daily)
    cvar = -(mu_daily + sigma_daily * norm.pdf(z)/(1-conf))
    return var*100, cvar*100
