import numpy as np
from scipy.stats import norm

def basic_stats(returns: np.ndarray, risk_free_annual: float = 0.0) -> dict:
    """
    Calculate basic statistics from returns
    Returns: dict with mean_daily, std_daily, std_annual, sharpe_ratio
    """
    if len(returns) < 2:
        return {
            "mean_daily": 0.0,
            "std_daily": 0.0,
            "std_annual": 0.0,
            "sharpe_ratio": 0.0
        }
    
    mean_daily = float(np.mean(returns))
    std_daily = float(np.std(returns, ddof=1))  # ddof=1 for estimation
    std_annual = std_daily * np.sqrt(252)
    
    # Sharpe ratio
    if std_daily > 0:
        sharpe_ratio = ((mean_daily * 252) - risk_free_annual) / std_annual
    else:
        sharpe_ratio = 0.0
    
    return {
        "mean_daily": mean_daily,
        "std_daily": std_daily,
        "std_annual": std_annual,
        "sharpe_ratio": sharpe_ratio
    }


def var_cvar(returns: np.ndarray, sigma: float, conf_level: float = 0.95, 
             method: str = "parametric") -> dict:
    """
    Calculate VaR and CVaR (Conditional Value at Risk)
    
    Args:
        returns: historical returns
        sigma: forecast volatility (annualized)
        conf_level: confidence level (default 0.95)
        method: "parametric" or "historical"
    
    Returns:
        dict with var_pct, cvar_pct (both as percentages)
    """
    if len(returns) < 2:
        return {"var_pct": 0.0, "cvar_pct": 0.0}
    
    if method == "parametric":
        # Parametric VaR assuming normal distribution
        z_score = norm.ppf(1 - conf_level)
        var_pct = z_score * sigma / np.sqrt(252)  # Convert to daily
        cvar_pct = var_pct * norm.pdf(z_score) / (1 - conf_level)
        
    elif method == "historical":
        # Historical simulation
        sorted_returns = np.sort(returns)
        cutoff_idx = int((1 - conf_level) * len(returns))
        var_pct = sorted_returns[cutoff_idx]
        cvar_pct = np.mean(sorted_returns[:cutoff_idx])
    
    else:
        raise ValueError(f"Unknown method: {method}")
    
    return {
        "var_pct": float(var_pct * 100),  # Convert to percentage
        "cvar_pct": float(cvar_pct * 100)
    }
