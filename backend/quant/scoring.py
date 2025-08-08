import numpy as np

def clip01(x: float) -> float:
    """Clip value to [0, 1] range"""
    return float(np.clip(x, 0, 1))

def weighted_avg(values: dict[str, float], weights: dict[str, float]) -> float:
    """Calculate weighted average of values"""
    w_sum = sum(weights.get(k, 1.0) for k in values)
    return sum(values[k] * weights.get(k, 1.0) for k in values) / w_sum if w_sum else 0.0

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

    # ─── Stress-test metric ────────────────────────────────────────────────
    #  worst_loss_pct – dodatnia liczba % straty (np. 0.08 = -8 %)
    worst_loss_pct = abs(raw_metrics.get("stress_loss_pct", 0.0))
    stress_norm = worst_loss_pct / normalization["STRESS_5PCT_FULLSCORE"]
    scores["stress"] = clip01(1 - stress_norm)          # Invert: mniejsza strata = lepiej
    
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
    
    # 4. Calculate overall score with validation
    overall_score = weighted_avg(scores, weights)
    
    # Sanity check: ensure overall score is in valid range
    if not (0.0 <= overall_score <= 1.0):
        print(f"Warning: Overall score out of range: {overall_score}, clipping to [0,1]")
        overall_score = clip01(overall_score)
    
    scores["overall"] = overall_score
    
    return scores, contrib_pct


def test_risk_mix_overall():
    """Unit test for risk_mix function"""
    # Mock data
    raw_metrics = {
        "hhi": 0.3,
        "vol_ann_pct": 15.0,
        "beta_market": 0.8,
        "avg_pair_corr": 0.2,
        "max_drawdown_pct": -5.0,
        "factor_l1": 0.5
    }
    
    normalization = {
        "HHI_LOW": 0.1,
        "HHI_HIGH": 0.5,
        "VOL_MAX": 50.0,
        "BETA_ABS_MAX": 2.0,
        "STRESS_5PCT_FULLSCORE": 20.0,
        "FACTOR_L1_MAX": 2.0
    }
    
    weights = {
        "concentration": 0.3,
        "volatility": 0.25,
        "beta": 0.2,
        "correlation": 0.15,
        "drawdown": 0.1
    }
    
    scores, contrib = risk_mix(raw_metrics, normalization, weights)
    
    # Assertions
    assert "overall" in scores, "Overall score should be present"
    assert 0.0 <= scores["overall"] <= 1.0, f"Overall score should be in [0,1], got {scores['overall']}"
    assert abs(sum(contrib.values()) - 100.0) < 1e-6, f"Contributions should sum to 100%, got {sum(contrib.values())}"
    
    print("✅ risk_mix unit test passed!")
    print(f"Overall score: {scores['overall']:.3f}")
    print(f"Contributions sum: {sum(contrib.values()):.1f}%")
    
    return True


if __name__ == "__main__":
    test_risk_mix_overall()
