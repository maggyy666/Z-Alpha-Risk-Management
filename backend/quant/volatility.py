"""
Czyste modele zmienności – brak zależności od SQLAlchemy
ani wewnętrznych klas projektu.
"""

from math import exp, log, sqrt
import numpy as np
from arch import arch_model
import warnings

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

def annualized_vol(returns: np.ndarray) -> float:
    """Calculate annualized volatility from returns"""
    if len(returns) < 2:
        return 0.0
    return float(np.std(returns, ddof=1) * np.sqrt(252))


def forecast_sigma(returns: np.ndarray, model: str = "EWMA (5D)") -> float:
    """
    Forecast volatility using specified model.
    Returns annualized volatility as decimal (e.g., 0.25 for 25%).
    """
    if len(returns) < 30:
        return np.std(returns) * np.sqrt(252)
    
    if model.startswith("EWMA"):
        # Extract lambda from model name
        if "(5D)" in model:
            lam = np.exp(-1/5)
        elif "(20D)" in model:
            lam = np.exp(-1/20)
        else:
            lam = 0.94  # default
            
        # EWMA calculation
        weights = np.array([(1-lam) * lam**i for i in range(len(returns))])
        weights = weights / weights.sum()
        
        # Calculate weighted variance
        mean_return = np.mean(returns)
        variance = np.sum(weights * (returns - mean_return)**2)
        return np.sqrt(variance * 252)
    
    elif model in ["GARCH", "EGARCH"]:
        try:
            # Clamp extreme returns to prevent model explosion
            returns_clamped = np.clip(returns, -0.2, 0.2)
            
            if model == "GARCH":
                am = arch_model(returns_clamped, vol='Garch', p=1, q=1, dist='normal')
            else:  # EGARCH
                am = arch_model(returns_clamped, vol='EGARCH', p=1, q=1, dist='normal')
            
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                res = am.fit(disp='off', show_warning=False)
            
            # Get forecast
            forecast = res.forecast(horizon=1)
            sigma = np.sqrt(forecast.variance.values[-1, 0] * 252)
            
            # Sanity check: clip extreme values
            if sigma > 3.0:  # > 300% annualized
                print(f"Warning: {model} volatility {sigma*100:.1f}% exceeds 300%, clipping to 300%")
                sigma = 3.0
                
            return sigma
            
        except Exception as e:
            print(f"Warning: {model} failed for volatility forecast: {e}")
            # Fallback to simple std
            return np.std(returns) * np.sqrt(252)
    
    else:
        raise ValueError(f"Unknown model: {model}")


def test_vol_reasonable(returns: np.ndarray, symbol: str = "UNKNOWN") -> bool:
    """
    Test if volatility forecast is reasonable.
    Returns True if OK, False if suspicious.
    """
    try:
        sigma = forecast_sigma(returns, "EGARCH")
        
        # Check if volatility is reasonable
        if sigma > 3.0:  # > 300% annualized
            print(f"⚠️  {symbol}: EGARCH volatility {sigma*100:.1f}% > 300% – suspicious!")
            return False
        elif sigma < 0.05:  # < 5% annualized
            print(f"⚠️  {symbol}: EGARCH volatility {sigma*100:.1f}% < 5% – suspicious!")
            return False
        else:
            print(f"✅ {symbol}: EGARCH volatility {sigma*100:.1f}% – reasonable")
            return True
            
    except Exception as e:
        print(f"❌ {symbol}: EGARCH volatility test failed: {e}")
        return False
