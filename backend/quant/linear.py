import numpy as np

def ols_beta(y: np.ndarray, x: np.ndarray) -> tuple[float, float]:
    """
    OLS regression: y = α + βx + ε
    Returns: (beta, r_squared)
    """
    if len(y) != len(x) or len(y) < 2:
        return 0.0, 0.0
    
    # Add constant for regression
    x_with_const = np.column_stack([np.ones(len(x)), x])
    
    try:
        # OLS regression
        coef = np.linalg.lstsq(x_with_const, y, rcond=None)[0]
        beta = coef[1]
        
        # Calculate R-squared
        y_pred = x_with_const @ coef
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        
        return float(beta), float(r_squared)
    except:
        return 0.0, 0.0
