"""Market regime metrics and classification.

Args/Inputs:
- R: returns matrix (T x N), w: weights (N,), regime thresholds dict.

Provides:
- regime_metrics: annualized vol, average corr, momentum, radar dict, label.

Returns:
- Tuple[vol_ann: float, avg_corr: float, mom: float, radar: dict, label: str].
"""

import numpy as np

def regime_metrics(R: np.ndarray, w: np.ndarray, regime_thresh: dict) -> tuple[float, float, float, dict, str]:
    """
    Calculate market regime metrics and classification
    Returns: (vol_ann, avg_corr, mom, radar, label)
    """
    if R.size == 0 or len(w) == 0:
        return 0.0, 0.0, 0.0, {"volatility": 0, "correlation": 0, "momentum": 0}, "Unknown"
    
    # Clean NaN values from R before calculations
    R_clean = np.nan_to_num(R, nan=0.0)
    
    # Portfolio returns
    rp = R_clean @ w
    
    # 1. Volatility (annualized) - filter out NaN from portfolio returns
    rp_valid = rp[np.isfinite(rp)]
    if len(rp_valid) > 1:
        vol_ann = float(np.std(rp_valid, ddof=1) * np.sqrt(252))
    else:
        vol_ann = 0.0
    
    # 2. Average correlation (filter zero-variance columns and NaN)
    var_mask = np.var(R_clean, axis=0) > 1e-12
    if var_mask.any():
        R_sub = R_clean[:, var_mask]
        # Use pandas for more robust correlation with NaN handling
        import pandas as pd
        df = pd.DataFrame(R_sub)
        corr_matrix = df.corr().values
        upper_tri = corr_matrix[np.triu_indices_from(corr_matrix, k=1)]
        valid_corr = upper_tri[np.isfinite(upper_tri)]
        avg_corr = float(np.mean(valid_corr)) if len(valid_corr) > 0 else 0.0
    else:
        avg_corr = 0.0
    
    # 3. Momentum (20-day cumulative) - use only valid returns
    window = min(20, len(rp_valid))
    if window >= 5:
        mom = float(np.exp(np.sum(rp_valid[-window:])) - 1)  # cumulative return
    else:
        mom = 0.0
    
    # 4. Radar metrics (normalized 0-1)
    radar = {
        "volatility": float(np.clip(vol_ann / 0.4, 0, 1)),  # Normalize to 40% max
        "correlation": float(np.clip((avg_corr + 1) / 2, 0, 1)),  # Map [-1,1] to [0,1]
        "momentum": float(np.clip((mom + 0.1) / 0.2, 0, 1))  # Normalize momentum
    }
    
    # 5. Regime classification
    if vol_ann > regime_thresh["crisis_vol"]:
        label = "Crisis"
    elif vol_ann > regime_thresh["cautious_vol"] or avg_corr > regime_thresh["cautious_corr"]:
        label = "Cautious"
    elif mom > regime_thresh["bull_mom"] and vol_ann < regime_thresh["bull_vol"] and avg_corr < regime_thresh["bull_corr"]:
        label = "Bull"
    else:
        label = "Neutral"
    
    return vol_ann, avg_corr, mom, radar, label
