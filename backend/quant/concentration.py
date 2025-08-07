import numpy as np

def concentration_metrics(weights: np.ndarray) -> tuple[float, float, float, float, float, float]:
    """
    Calculate concentration metrics from portfolio weights
    Returns: (largest_position, top3_concentration, top5_concentration, top10_concentration, hhi, effective_positions)
    """
    if len(weights) == 0:
        return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    
    # Sort weights in descending order
    sorted_weights = np.sort(weights)[::-1]
    
    # Largest position
    largest_position = float(sorted_weights[0]) if len(sorted_weights) > 0 else 0.0
    
    # Top concentrations
    top3_concentration = float(np.sum(sorted_weights[:3]))
    top5_concentration = float(np.sum(sorted_weights[:5]))
    top10_concentration = float(np.sum(sorted_weights[:10]))
    
    # Herfindahl-Hirschman Index (HHI)
    hhi = float(np.sum(weights ** 2))
    
    # Effective number of positions
    effective_positions = 1.0 / hhi if hhi > 0 else 0.0
    
    return largest_position, top3_concentration, top5_concentration, top10_concentration, hhi, effective_positions
