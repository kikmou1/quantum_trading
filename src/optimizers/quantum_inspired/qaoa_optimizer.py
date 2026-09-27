"""
QAOA-inspired portfolio optimization.

Note: no quantum circuit is built or simulated here. QAOAPortfolioOptimizer
formulates asset selection as a QUBO and solves it with classical simulated
annealing; QAOAContinuousOptimizer is a classical SLSQP risk/return trade-off.
Qiskit is only required as an installation check for QAOAPortfolioOptimizer.
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict
import logging

try:
    # qiskit.primitives.Sampler was removed in Qiskit 2.0, so only import
    # names that exist in both Qiskit 1.x and 2.x.
    import qiskit  # noqa: F401
    import qiskit_algorithms  # noqa: F401
    import qiskit_optimization  # noqa: F401
    QISKIT_AVAILABLE = True
except ImportError:
    QISKIT_AVAILABLE = False
    logging.warning("Qiskit not available. QAOA optimizer will not work.")

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from base import BaseOptimizer

logger = logging.getLogger(__name__)


class QAOAPortfolioOptimizer(BaseOptimizer):
    """
    QAOA-based portfolio optimization.

    Formulates portfolio optimization as a QUBO problem:
    H = risk_factor * Σᵢⱼ σᵢⱼ·xᵢ·xⱼ - (1-risk_factor) * Σᵢ rᵢ·xᵢ + penalty * (Σᵢ xᵢ - 1)²

    where:
    - σᵢⱼ is the covariance matrix
    - rᵢ is the expected return
    - xᵢ are binary variables representing asset selection
    - risk_factor balances risk vs return (0-1)
    """

    def __init__(
        self,
        p_layers: int = 3,
        optimizer: str = "COBYLA",
        max_iterations: int = 100,
        risk_factor: float = 0.5,
        penalty_multiplier: float = 10.0,
        n_shots: int = 1024
    ):
        super().__init__(name="QAOA")

        if not QISKIT_AVAILABLE:
            raise ImportError("Qiskit is required for QAOA optimizer")

        self.p_layers = p_layers
        self.optimizer_name = optimizer
        self.max_iterations = max_iterations
        self.risk_factor = risk_factor
        self.penalty_multiplier = penalty_multiplier
        self.n_shots = n_shots

    def optimize(self, returns: pd.DataFrame, **kwargs) -> pd.Series:
        """
        Optimize portfolio using QAOA.

        Note: This is a simplified implementation that selects a subset of assets
        with equal weights, rather than continuous weight optimization.
        """
        n_assets = len(returns.columns)

        # For small portfolios, use classical QUBO solver
        # For larger portfolios, this would require actual quantum hardware
        if n_assets > 10:
            logger.warning(f"QAOA with {n_assets} assets may be slow. Consider reducing portfolio size.")

        # Calculate expected returns and covariance
        mu = returns.mean() * 252  # Annualized
        cov = returns.cov() * 252  # Annualized

        # Formulate as QUBO problem
        weights = self._solve_qubo(mu, cov, n_assets)

        return weights

    def _solve_qubo(self, mu: pd.Series, cov: pd.DataFrame, n_assets: int) -> pd.Series:
        """
        Solve the QUBO problem using classical simulation of QAOA.

        For production use, this would be replaced with actual quantum hardware.
        """
        # Normalize returns and risk
        mu_norm = (mu - mu.min()) / (mu.max() - mu.min() + 1e-8)
        cov_norm = cov / (cov.max().max() + 1e-8)

        # Create QUBO matrix: Q[i,j] represents interaction between assets i and j
        Q = np.zeros((n_assets, n_assets))

        # Risk term (quadratic)
        Q += self.risk_factor * cov_norm.values

        # Return term (linear, on diagonal)
        for i in range(n_assets):
            Q[i, i] -= (1 - self.risk_factor) * mu_norm.iloc[i]

        # Solve using simulated annealing (classical approximation of QAOA)
        # This mimics what QAOA would do on quantum hardware
        best_solution = self._simulated_annealing_qubo(Q, n_assets)

        # Convert binary solution to weights
        weights = pd.Series(best_solution, index=mu.index)

        # Normalize to sum to 1
        if weights.sum() > 0:
            weights = weights / weights.sum()
        else:
            # If no assets selected, use equal weight
            weights = pd.Series(1.0 / n_assets, index=mu.index)

        return weights

    def _simulated_annealing_qubo(
        self,
        Q: np.ndarray,
        n_assets: int,
        n_iterations: int = 1000,
        temperature_start: float = 10.0,
        temperature_end: float = 0.01
    ) -> np.ndarray:
        """
        Solve QUBO using simulated annealing (classical approximation).

        This simulates what QAOA would do on quantum hardware.
        """
        # Target number of assets (portfolio size constraint)
        target_assets = max(3, n_assets // 3)  # Select ~1/3 of assets

        # Initialize with random solution
        solution = np.random.rand(n_assets) > 0.5
        # Ensure we have target number of assets
        if solution.sum() != target_assets:
            solution = np.zeros(n_assets, dtype=bool)
            selected = np.random.choice(n_assets, target_assets, replace=False)
            solution[selected] = True

        best_solution = solution.copy()
        best_energy = self._evaluate_qubo(Q, solution)

        # Simulated annealing
        for it in range(n_iterations):
            # Temperature schedule
            t = temperature_start * (temperature_end / temperature_start) ** (it / n_iterations)

            # Propose new solution (flip one bit)
            new_solution = solution.copy()

            # Swap strategy: turn one ON and one OFF to maintain portfolio size
            on_indices = np.where(new_solution)[0]
            off_indices = np.where(~new_solution)[0]

            if len(on_indices) > 0 and len(off_indices) > 0:
                turn_off = np.random.choice(on_indices)
                turn_on = np.random.choice(off_indices)
                new_solution[turn_off] = False
                new_solution[turn_on] = True

            # Evaluate energy
            new_energy = self._evaluate_qubo(Q, new_solution)
            current_energy = self._evaluate_qubo(Q, solution)

            # Accept or reject
            delta_e = new_energy - current_energy
            if delta_e < 0 or np.random.rand() < np.exp(-delta_e / t):
                solution = new_solution

                # Update best
                if new_energy < best_energy:
                    best_energy = new_energy
                    best_solution = new_solution.copy()

        return best_solution.astype(float)

    def _evaluate_qubo(self, Q: np.ndarray, solution: np.ndarray) -> float:
        """
        Evaluate QUBO objective function: x^T Q x
        """
        x = solution.astype(float)
        energy = x @ Q @ x
        return energy


class QAOAContinuousOptimizer(BaseOptimizer):
    """
    Continuous weight version of QAOA.
    Uses QAOA-inspired optimization but outputs continuous weights.
    """

    def __init__(
        self,
        risk_factor: float = 0.5,
        max_iterations: int = 200
    ):
        super().__init__(name="QAOA_Continuous")
        self.risk_factor = risk_factor
        self.max_iterations = max_iterations

    def optimize(self, returns: pd.DataFrame, **kwargs) -> pd.Series:
        """
        Optimize using QAOA-inspired continuous optimization.
        """
        from scipy.optimize import minimize

        n_assets = len(returns.columns)

        # Calculate expected returns and covariance
        mu = returns.mean() * 252  # Annualized
        cov = returns.cov() * 252  # Annualized

        # Objective function: risk - return tradeoff
        def objective(w):
            portfolio_return = w @ mu
            portfolio_risk = np.sqrt(w @ cov @ w)
            # Minimize: risk_factor * risk - (1 - risk_factor) * return
            return self.risk_factor * portfolio_risk - (1 - self.risk_factor) * portfolio_return

        # Constraints: weights sum to 1
        constraints = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}
        ]

        # Bounds: weights between 0 and 1
        bounds = [(0, 1) for _ in range(n_assets)]

        # Initial guess: equal weight
        w0 = np.ones(n_assets) / n_assets

        # Optimize
        result = minimize(
            objective,
            w0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
            options={'maxiter': self.max_iterations}
        )

        if not result.success:
            logger.warning(f"Optimization did not converge: {result.message}")

        weights = pd.Series(result.x, index=returns.columns)

        # Store metadata
        self.metadata['converged'] = result.success
        self.metadata['iterations'] = result.nit

        return weights


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Generate sample returns
    np.random.seed(42)
    dates = pd.date_range('2020-01-01', '2023-01-01', freq='D')
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA']

    returns = pd.DataFrame(
        np.random.randn(len(dates), len(tickers)) * 0.01,
        index=dates,
        columns=tickers
    )

    # Test QAOA continuous (faster, more practical)
    print("Testing QAOA Continuous Optimizer...")
    opt = QAOAContinuousOptimizer(risk_factor=0.5)
    opt.fit(returns)
    weights = opt.get_weights()
    print(f"\nWeights:")
    print(weights.sort_values(ascending=False))
    print(f"Execution time: {opt.execution_time:.4f}s")

    # Test QAOA binary (if Qiskit available)
    if QISKIT_AVAILABLE:
        print("\n\nTesting QAOA Binary Optimizer...")
        opt_binary = QAOAPortfolioOptimizer(p_layers=2, max_iterations=50)
        opt_binary.fit(returns)
        weights_binary = opt_binary.get_weights()
        print(f"\nWeights:")
        print(weights_binary[weights_binary > 0].sort_values(ascending=False))
        print(f"Execution time: {opt_binary.execution_time:.4f}s")
