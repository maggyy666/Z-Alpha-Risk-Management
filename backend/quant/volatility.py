"""
Czyste modele zmienności – brak zależności od SQLAlchemy
ani wewnętrznych klas projektu.
"""

from math import exp, log, sqrt
import numpy as np

# -------- helpers -------- #

def lambda_from_half_life(days: int) -> float:
    """λ = 2^(-1/HL)"""
    return exp(-log(2) / max(1, days))


def log_returns(prices):
    prices = np.asarray(prices, dtype=float)
    return np.diff(np.log(prices))


# -------- główne modele -------- #

def ewma_vol(returns, lam=0.94, annualize=True):
    if len(returns) < 2:
        return 0.0
    var = returns[0] ** 2
    for r in returns[1:]:
        var = lam * var + (1 - lam) * r**2
    sigma = sqrt(var)
    return sigma * sqrt(252) if annualize else sigma


def garch11_vol(returns, omega=1e-6, alpha=0.1, beta=0.8, annualize=True):
    if len(returns) < 100:
        return np.std(returns, ddof=1) * (sqrt(252) if annualize else 1)
    var = np.var(returns[:100])
    for i in range(100, len(returns)):
        var = omega + alpha * returns[i - 1] ** 2 + beta * var
    sigma = sqrt(var)
    return sigma * sqrt(252) if annualize else sigma


def egarch_vol(returns, omega=-0.1, alpha=0.1, gamma=0.1, beta=0.9, annualize=True):
    if len(returns) < 100:
        return np.std(returns, ddof=1) * (sqrt(252) if annualize else 1)
    log_var = np.log(np.var(returns[:100]))
    for i in range(100, len(returns)):
        z = returns[i - 1] / sqrt(exp(log_var))
        log_var = omega + alpha * abs(z) + gamma * z + beta * log_var
    sigma = sqrt(exp(log_var))
    return sigma * sqrt(252) if annualize else sigma


# -------- wygodny dispatcher -------- #

def forecast_sigma(returns, model="EWMA (5D)"):
    m = model.upper()
    if m.startswith("EWMA"):
        if "5" in m:
            lam = lambda_from_half_life(5)
        elif "30" in m:
            lam = lambda_from_half_life(30)
        elif "200" in m:
            lam = lambda_from_half_life(200)
        else:
            lam = 0.94
        return ewma_vol(returns, lam)
    if "E-GARCH" in m or "EGARCH" in m:
        return egarch_vol(returns)
    if "GARCH" in m:
        return garch11_vol(returns)
    return np.std(returns, ddof=1) * np.sqrt(252)
