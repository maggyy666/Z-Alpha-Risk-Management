import numpy as np

def regime_metrics(R: np.ndarray, w: np.ndarray, regime_thresh: dict) -> tuple[float, float, float, dict, str]:
    """
    Calculate market regime metrics and classification
    Returns: (vol_ann, avg_corr, mom, radar, label)
    """
    if R.size == 0 or len(w) == 0:
        return 0.0, 0.0, 0.0, {"volatility": 0, "correlation": 0, "momentum": 0}, "Unknown"
    
    # Portfolio returns
    rp = R @ w
    
    # 1. Volatility (annualized)
    vol_ann = float(np.std(rp, ddof=1) * np.sqrt(252))
    
    # 2. Average correlation
    corr_matrix = np.corrcoef(R.T)
    # Remove diagonal and get upper triangle
    upper_tri = corr_matrix[np.triu_indices_from(corr_matrix, k=1)]
    avg_corr = float(np.mean(upper_tri[np.isfinite(upper_tri)]))
    
    # 3. Momentum (20-day)
    window = min(20, len(rp))
    if window >= 5:
        mom = float(np.mean(rp[-window:]))
    else:
        mom = 0.0
    
    # 4. Radar metrics (normalized 0-1)
    radar = {
        "volatility": float(np.clip(vol_ann / 0.4, 0, 1)),  # Normalize to 40% max
        "correlation": float(np.clip(avg_corr, 0, 1)),
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
