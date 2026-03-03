# physics.py, volatility, correlation structure, market factor, sector blocks, Heston model, Cholesky decomposition
import numpy as np
from scipy.linalg import block_diag
import config

class MarketPhysics:
    def __init__(self):
        self.cov_matrix = self._build_correlation_structure()
        self.L = np.linalg.cholesky(self.cov_matrix)

    def _build_correlation_structure(self):
        """Creates a block-diagonal matrix (Sectors) + Market Factor."""
        # Create 4 distinct sectors
        block_size = config.N_ASSETS // 4
        blocks = []
        for _ in range(4):
            # Internal sector correlation (~0.65)
            base = 0.65
            noise = np.random.uniform(-0.05, 0.05, (block_size, block_size))
            block = np.full((block_size, block_size), base) + noise
            np.fill_diagonal(block, 1.0)
            blocks.append(block)
            
        matrix = block_diag(*blocks)
        matrix += 0.25 # Market-wide correlation (Beta)
        
        # Normalize to ensure valid correlation matrix
        d = np.sqrt(np.diag(matrix))
        matrix = matrix / np.outer(d, d)
        
        # Ensure Positive Semi-Definite (Fix float errors)
        eigvals, eigvecs = np.linalg.eigh(matrix)
        eigvals = np.maximum(eigvals, 1e-8)
        return eigvecs @ np.diag(eigvals) @ eigvecs.T

    def get_volatility_path(self):
        """Generates the Heston volatility path for the year."""
        v = np.zeros(config.N_DAYS)
        v[0] = config.INITIAL_VARIANCE
        dt = config.DT
        
        for t in range(1, config.N_DAYS):
            # dV = kappa(theta - V)dt + xi*sqrt(V)*dW
            drift = config.MEAN_REVERSION_SPEED * (config.LONG_TERM_VARIANCE - v[t-1]) * dt
            shock = config.VOL_OF_VOL * np.sqrt(max(v[t-1], 0)) * np.sqrt(dt) * np.random.normal()
            v[t] = max(v[t-1] + drift + shock, 1e-6)
            
        return np.sqrt(v) # Return Sigma (Volatility)