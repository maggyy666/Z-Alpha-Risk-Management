import numpy as np

def clip01(x: float) -> float:
    """Clip value to [0, 1] range"""
    return float(np.clip(x, 0, 1))

def risk_mix(raw_metrics: dict, normalization: dict, weights: dict) -> tuple[dict, dict]:
    """
    Normalize and mix risk metrics into scores
    Returns: (component_scores, risk_contribution_pct)
    """
    # 1. Normalize raw metrics to 0-1 scale
    scores = {}
    
    # Concentration metrics
    hhi_norm = (raw_metrics["hhi"] - normalization["HHI_LOW"]) / (normalization["HHI_HIGH"] - normalization["HHI_LOW"])
    scores["concentration"] = clip01(1 - hhi_norm)  # Invert: lower HHI = better
    
    # Volatility metric
    vol_norm = raw_metrics["vol_ann_pct"] / normalization["VOL_MAX"]
    scores["volatility"] = clip01(1 - vol_norm)  # Invert: lower vol = better
    
    # Beta metric
    beta_norm = abs(raw_metrics["beta_market"]) / normalization["BETA_ABS_MAX"]
    scores["beta"] = clip01(1 - beta_norm)  # Invert: lower beta = better
    
    # Correlation metric
    corr_norm = raw_metrics["avg_pair_corr"]
    scores["correlation"] = clip01(1 - corr_norm)  # Invert: lower corr = better
    
    # Drawdown metric
    dd_norm = abs(raw_metrics["max_drawdown_pct"]) / normalization["STRESS_5PCT_FULLSCORE"]
    scores["drawdown"] = clip01(1 - dd_norm)  # Invert: lower DD = better
    
    # Factor exposure metric
    factor_norm = raw_metrics.get("factor_l1", 0) / normalization["FACTOR_L1_MAX"]
    scores["factor_exposure"] = clip01(1 - factor_norm)  # Invert: lower exposure = better
    
    # 2. Calculate weighted scores
    weighted_scores = {}
    for component, score in scores.items():
        weight = weights.get(component, 1.0)
        weighted_scores[component] = score * weight
    
    # 3. Calculate risk contribution percentages
    total_weighted = sum(weighted_scores.values())
    contrib_pct = {}
    for component, weighted_score in weighted_scores.items():
        contrib_pct[component] = (weighted_score / total_weighted * 100) if total_weighted > 0 else 0
    
    return scores, contrib_pct
