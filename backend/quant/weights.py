import numpy as np

def inverse_vol_allocation(vols: np.ndarray, floor: float = 0.08) -> np.ndarray:
    """
    Calculate inverse volatility weights with floor
    Returns: normalized weights
    """
    if len(vols) == 0:
        return np.array([])
    
    # Apply floor to volatilities
    vols_frac = np.maximum(vols / 100.0, floor / 100.0)
    
    # Calculate inverse weights
    inv_weights = 1.0 / vols_frac
    
    # Normalize to sum to 1
    total_inv = np.sum(inv_weights)
    if total_inv > 0:
        normalized_weights = inv_weights / total_inv
    else:
        # Fallback to equal weights
        normalized_weights = np.ones(len(vols)) / len(vols)
    
    return normalized_weights
