"""Correlation/covariance estimators.

Args/Inputs:
- R: returns matrix (T x N), lam for EWMA.

Provides:
- ewma_corr: EWMA correlation with PD enforcement and renormalized diagonal.

Returns:
- np.ndarray [N x N].
"""

import numpy as np

def ewma_corr(R: np.ndarray, lam: float = 0.94) -> np.ndarray:
    """
    Calculate EWMA correlation matrix from returns matrix R [T x N]
    Returns: correlation matrix [N x N]
    """
    if R.size == 0 or R.shape[0] < 30:
        # Fallback to diagonal correlation if insufficient data
        n_assets = R.shape[1] if R.size > 0 else 0
        return np.eye(n_assets)
    
    T, n_assets = R.shape
    corr_matrix = np.eye(n_assets)
    
    # Initialize with sample correlation
    sample_corr = np.corrcoef(R.T)
    sample_corr = np.where(np.isfinite(sample_corr), sample_corr, 0.0)
    sample_corr = np.where(np.eye(n_assets) == 1, 1.0, sample_corr)
    
    # EWMA correlation update
    for t in range(30, T):
        # Standardize returns
        std_returns = R[t] / np.sqrt(np.var(R[t], ddof=1))
        std_returns = np.where(np.isfinite(std_returns), std_returns, 0.0)
        
        # Outer product for correlation update
        outer_prod = np.outer(std_returns, std_returns)
        
        # EWMA update
        corr_matrix = lam * corr_matrix + (1 - lam) * outer_prod
    
    # Ensure diagonal is 1 and matrix is symmetric
    corr_matrix = np.where(np.eye(n_assets) == 1, 1.0, corr_matrix)
    corr_matrix = (corr_matrix + corr_matrix.T) / 2  # Symmetrize
    
    # Ensure positive definiteness (clamp eigenvalues)
    eigenvals, eigenvecs = np.linalg.eigh(corr_matrix)
    eigenvals = np.maximum(eigenvals, 1e-6)  # Floor at small positive value
    corr_matrix = eigenvecs @ np.diag(eigenvals) @ eigenvecs.T
    
    # Re-normalize diagonal to 1
    diag_sqrt = np.sqrt(np.diag(corr_matrix))
    corr_matrix = corr_matrix / np.outer(diag_sqrt, diag_sqrt)
    
    return corr_matrix
