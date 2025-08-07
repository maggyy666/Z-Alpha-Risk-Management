import numpy as np

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
