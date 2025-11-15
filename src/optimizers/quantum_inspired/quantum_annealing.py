"""
Quantum Annealing for portfolio optimization.
Uses D-Wave Ocean SDK (simulated annealing for local execution).
"""

import pandas as pd
import numpy as np
from typing import Optional
import logging

try:
    import dimod
    from dwave.system import DWaveSampler, EmbeddingComposite
    from neal import SimulatedAnnealingSampler
    DWAVE_AVAILABLE = True
except ImportError:
    DWAVE_AVAILABLE = False
    logging.warning("D-Wave Ocean SDK not available.")

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from base import BaseOptimizer

logger = logging.getLogger(__name__)


class QuantumAnnealingOptimizer(BaseOptimizer):
    """
    Portfolio optimization using simulated quantum annealing.
    Uses D-Wave's neal sampler for classical simulation.
    """

    def __init__(
        self,
        num_reads: int = 100,
        risk_factor: float = 0.5,
        use_cloud: bool = False
    ):
        super().__init__(name="QuantumAnnealing")

        if not DWAVE_AVAILABLE:
            raise ImportError("D-Wave Ocean SDK required for quantum annealing")

        self.num_reads = num_reads
        self.risk_factor = risk_factor
        self.use_cloud = use_cloud

    def optimize(self, returns: pd.DataFrame, **kwargs) -> pd.Series:
        """
        Optimize portfolio using simulated quantum annealing.
        """
        n_assets = len(returns.columns)

        # Calculate expected returns and covariance
        mu = returns.mean() * 252
        cov = returns.cov() * 252

        # Build QUBO formulation
        Q = self._build_qubo(mu, cov)

        # Solve using simulated annealing
        sampler = SimulatedAnnealingSampler()
        response = sampler.sample_qubo(Q, num_reads=self.num_reads)

        # Get best solution
        best_sample = response.first.sample

        # Convert to weights
        weights = np.zeros(n_assets)
        for i in range(n_assets):
            if best_sample.get(i, 0) == 1:
                weights[i] = 1.0

        # Normalize
        if weights.sum() > 0:
            weights = weights / weights.sum()
        else:
            weights = np.ones(n_assets) / n_assets

        weights_series = pd.Series(weights, index=returns.columns)

        # Store metadata
        self.metadata['energy'] = response.first.energy
        self.metadata['num_occurrences'] = response.first.num_occurrences

        return weights_series

    def _build_qubo(self, mu: pd.Series, cov: pd.DataFrame) -> dict:
        """
        Build QUBO dictionary for D-Wave.
        Q = {(i,j): value} where i,j are variable indices.
        """
        n = len(mu)

        # Normalize
        mu_norm = (mu - mu.min()) / (mu.max() - mu.min() + 1e-8)
        cov_norm = cov / (cov.max().max() + 1e-8)

        Q = {}

        # Risk terms (quadratic)
        for i in range(n):
            for j in range(n):
                value = self.risk_factor * cov_norm.iloc[i, j]
                if value != 0:
                    Q[(i, j)] = float(value)

        # Return terms (linear - on diagonal)
        for i in range(n):
            current = Q.get((i, i), 0.0)
            Q[(i, i)] = current - (1 - self.risk_factor) * mu_norm.iloc[i]

        return Q


class HybridAnnealingOptimizer(BaseOptimizer):
    """
    Hybrid quantum-classical annealing.
    Combines quantum annealing for selection with classical optimization for weights.
    """

    def __init__(
        self,
        num_reads: int = 100,
        risk_factor: float = 0.5
    ):
        super().__init__(name="HybridAnnealing")
        self.num_reads = num_reads
        self.risk_factor = risk_factor

    def optimize(self, returns: pd.DataFrame, **kwargs) -> pd.Series:
        """
        Two-stage optimization:
        1. Use quantum annealing to select assets
        2. Use classical mean-variance to determine weights
        """
        if not DWAVE_AVAILABLE:
            # Fallback to pure classical
            from scipy.optimize import minimize

            n_assets = len(returns.columns)
            mu = returns.mean() * 252
            cov = returns.cov() * 252

            def objective(w):
                portfolio_return = w @ mu
                portfolio_risk = np.sqrt(w @ cov @ w)
                return self.risk_factor * portfolio_risk - (1 - self.risk_factor) * portfolio_return

            constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}]
            bounds = [(0, 1) for _ in range(n_assets)]
            w0 = np.ones(n_assets) / n_assets

            result = minimize(objective, w0, method='SLSQP', bounds=bounds, constraints=constraints)
            return pd.Series(result.x, index=returns.columns)

        # Stage 1: Asset selection using quantum annealing
        qa_opt = QuantumAnnealingOptimizer(num_reads=self.num_reads, risk_factor=self.risk_factor)
        selection = qa_opt.optimize(returns)

        # Get selected assets
        selected_assets = selection[selection > 0].index.tolist()

        if len(selected_assets) == 0:
            logger.warning("No assets selected by quantum annealing, using all assets")
            selected_assets = returns.columns.tolist()

        # Stage 2: Classical optimization on selected assets
        returns_selected = returns[selected_assets]
        mu = returns_selected.mean() * 252
        cov = returns_selected.cov() * 252

        # Solve mean-variance optimization
        from scipy.optimize import minimize

        def objective(w):
            portfolio_return = w @ mu
            portfolio_risk = np.sqrt(w @ cov @ w)
            return self.risk_factor * portfolio_risk - (1 - self.risk_factor) * portfolio_return

        n_selected = len(selected_assets)
        constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}]
        bounds = [(0, 1) for _ in range(n_selected)]
        w0 = np.ones(n_selected) / n_selected

        result = minimize(objective, w0, method='SLSQP', bounds=bounds, constraints=constraints)

        # Map back to full portfolio
        weights = pd.Series(0.0, index=returns.columns)
        for i, asset in enumerate(selected_assets):
            weights[asset] = result.x[i]

        return weights


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    np.random.seed(42)
    dates = pd.date_range('2020-01-01', '2023-01-01', freq='D')
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA']

    returns = pd.DataFrame(
        np.random.randn(len(dates), len(tickers)) * 0.01,
        index=dates,
        columns=tickers
    )

    if DWAVE_AVAILABLE:
        print("Testing Quantum Annealing Optimizer...")
        opt = QuantumAnnealingOptimizer(num_reads=50)
        opt.fit(returns)
        weights = opt.get_weights()
        print(f"\nWeights:")
        print(weights[weights > 0].sort_values(ascending=False))
        print(f"Execution time: {opt.execution_time:.4f}s")

        print("\n\nTesting Hybrid Annealing Optimizer...")
        opt_hybrid = HybridAnnealingOptimizer(num_reads=50)
        opt_hybrid.fit(returns)
        weights_hybrid = opt_hybrid.get_weights()
        print(f"\nWeights:")
        print(weights_hybrid[weights_hybrid > 0].sort_values(ascending=False))
        print(f"Execution time: {opt_hybrid.execution_time:.4f}s")
    else:
        print("D-Wave Ocean SDK not available. Install with: pip install dwave-ocean-sdk")
