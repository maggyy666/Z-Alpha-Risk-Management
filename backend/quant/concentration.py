import numpy as np

def concentration_metrics(weights: np.ndarray) -> tuple[float, float, float, float, float, float]:
    """
    Long/short-safe concentration metrics based on absolute weights.
    
    Args:
        weights: portfolio weights (can be negative for short positions)
    
    Returns:
        (largest_position, top3_concentration, top5_concentration, top10_concentration, hhi, effective_positions)
    """
    w = np.asarray(weights, dtype=float)
    w_abs = np.abs(w)
    s = w_abs.sum()
    if s <= 0:
        return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0

    w_abs = w_abs / s
    sorted_w = np.sort(w_abs)[::-1]

    largest_position = float(sorted_w[0]) if len(sorted_w) else 0.0
    top3_concentration = float(sorted_w[:3].sum())
    top5_concentration = float(sorted_w[:5].sum())
    top10_concentration = float(sorted_w[:10].sum())

    hhi = float((w_abs**2).sum())
    effective_positions = 1.0 / hhi if hhi > 0 else 0.0
    return largest_position, top3_concentration, top5_concentration, top10_concentration, hhi, effective_positions
