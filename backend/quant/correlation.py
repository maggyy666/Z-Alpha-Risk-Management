import numpy as np

def avg_and_high_corr(R: np.ndarray, threshold: float = 0.7) -> tuple[float, int, int]:
    """
    Calculate average correlation and count high correlation pairs
    Returns: (avg_correlation, total_pairs, high_correlation_pairs)
    """
    if R.size == 0 or R.shape[1] < 2:
        return 0.0, 0, 0
    
    # Drop zero-variance columns
    var_mask = np.var(R, axis=0) > 1e-12
    R_sub = R[:, var_mask]
    
    if R_sub.shape[1] < 2:
        return 0.0, 0, 0
    
    # Calculate correlation matrix
    C = np.corrcoef(R_sub, rowvar=False)
    C = np.where(np.isfinite(C), C, 0.0)
    
    # Get upper triangle values (excluding diagonal)
    n = C.shape[0]
    vals = []
    for i in range(n):
        for j in range(i+1, n):
            c = C[i, j]
            vals.append(c)
    
    if not vals:
        return 0.0, 0, 0
    
    # Calculate metrics
    avg_correlation = float(np.mean(vals))
    total_pairs = len(vals)
    high_correlation_pairs = sum(1 for c in vals if c > threshold)
    
    return avg_correlation, total_pairs, high_correlation_pairs
