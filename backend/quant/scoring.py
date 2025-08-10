import numpy as np

def clip01(x: float) -> float:
    """Clip value to [0, 1] range"""
    return float(np.clip(x, 0, 1))

def weighted_avg(values: dict[str, float], weights: dict[str, float]) -> float:
    """Calculate weighted average of values"""
    w_sum = sum(weights.get(k, 1.0) for k in values)
    return sum(values[k] * weights.get(k, 1.0) for k in values) / w_sum if w_sum else 0.0

def risk_mix(raw: dict, norm: dict, weights: dict) -> tuple[dict, dict]:
    """
    Normalize metrics to [0,1] (1 = better), calculate weighted score and component contributions.
    Expected input keys (raw):
      hhi, vol_ann_pct, beta_market, avg_pair_corr, max_drawdown_pct, factor_l1, stress_loss_pct
    Weights keys: concentration, volatility, market, correlation, drawdown, factor, stress
    """
    # 1) Normalizations -> [0..1] scales, where 1=better
    # HHI: smaller is better
    hhi_norm = (raw.get("hhi", 0.0) - norm["HHI_LOW"]) / (norm["HHI_HIGH"] - norm["HHI_LOW"])
    concentration = clip01(1.0 - hhi_norm)

    # Vol: smaller is better
    vol_norm = raw.get("vol_ann_pct", 0.0) / norm["VOL_MAX"]
    volatility = clip01(1.0 - vol_norm)

    # Beta: |beta| smaller is better
    beta_norm = abs(raw.get("beta_market", 0.0)) / norm["BETA_ABS_MAX"]
    market = clip01(1.0 - beta_norm)

    # Corr: map [-1,1] -> [0,1] and invert (lower correlation is better)
    corr = float(raw.get("avg_pair_corr", 0.0))
    corr_01 = (corr + 1.0) * 0.5
    correlation = clip01(1.0 - corr_01)

    # Max DD: larger drawdown is worse - HAVE SEPARATE threshold in normalization!
    dd_full = norm.get("MAXDD_FULLSCORE", norm["STRESS_5PCT_FULLSCORE"])  # fallback to old
    dd_norm = abs(raw.get("max_drawdown_pct", 0.0)) / dd_full
    drawdown = clip01(1.0 - dd_norm)

    # Factor L1: lower is better
    factor_norm = raw.get("factor_l1", 0.0) / norm["FACTOR_L1_MAX"]
    factor = clip01(1.0 - factor_norm)

    # Stress: larger (positive) loss is worse
    worst_loss = abs(raw.get("stress_loss_pct", 0.0))  # e.g. 0.08 = -8%
    stress_norm = worst_loss / norm["STRESS_5PCT_FULLSCORE"]
    stress = clip01(1.0 - stress_norm)

    scores = {
        "concentration": concentration,
        "volatility":   volatility,
        "market":       market,
        "correlation":  correlation,
        "drawdown":     drawdown,
        "factor":       factor,
        "stress":       stress,
    }

    # 2) Apply weights only to known keys
    w_used = {k: float(weights.get(k, 0.0)) for k in scores.keys()}
    w_sum = sum(w_used.values()) or 1.0
    weighted_scores = {k: scores[k] * w_used[k] for k in scores}

    # 3) Percentage contribution (sums to 100%)
    total_weighted = sum(weighted_scores.values())
    contrib_pct = {k: (weighted_scores[k] / total_weighted * 100.0) if total_weighted > 0 else 0.0
                   for k in scores}

    # 4) Overall = sum(score*weight) / sum(weights)
    overall = sum(weighted_scores.values()) / w_sum
    scores["overall"] = clip01(float(overall))
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
        "FACTOR_L1_MAX": 2.0,
        "MAXDD_FULLSCORE": 20.0
    }
    
    weights = {
        "concentration": 0.25,
        "volatility": 0.20,
        "factor": 0.20,
        "correlation": 0.15,
        "market": 0.10,
        "stress": 0.10
    }
    
    scores, contrib = risk_mix(raw_metrics, normalization, weights)
    
    # Assertions
    assert "overall" in scores, "Overall score should be present"
    assert 0.0 <= scores["overall"] <= 1.0, f"Overall score should be in [0,1], got {scores['overall']}"
    assert abs(sum(contrib.values()) - 100.0) < 1e-6, f"Contributions should sum to 100%, got {sum(contrib.values())}"
    
    print("risk_mix unit test passed!")
    print(f"Overall score: {scores['overall']:.3f}")
    print(f"Contributions sum: {sum(contrib.values()):.1f}%")
    
    return True


if __name__ == "__main__":
    test_risk_mix_overall()
