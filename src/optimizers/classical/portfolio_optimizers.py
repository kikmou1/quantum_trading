"""
Classical portfolio optimization methods.
Uses PyPortfolioOpt, cvxpy, and custom implementations.
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict
import logging

from pypfopt import EfficientFrontier, risk_models, expected_returns
from pypfopt import HRPOpt, RiskParityOpt, BlackLittermanModel
from pypfopt import objective_functions
import cvxpy as cp

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from base import BaseOptimizer

logger = logging.getLogger(__name__)


class EqualWeightOptimizer(BaseOptimizer):
    """
    Baseline: Equal weight portfolio (1/N).
    """

    def __init__(self):
        super().__init__(name="EqualWeight")

    def optimize(self, returns: pd.DataFrame, **kwargs) -> pd.Series:
        """
        Assign equal weights to all assets.
        """
        n_assets = len(returns.columns)
        weights = pd.Series(1.0 / n_assets, index=returns.columns)
        return weights


class MeanVarianceOptimizer(BaseOptimizer):
    """
    Mean-Variance Optimization (Markowitz).
    """

    def __init__(
        self,
        risk_free_rate: float = 0.04,
        gamma: float = 0.5,
        allow_short: bool = False
    ):
        super().__init__(name="MeanVariance")
        self.risk_free_rate = risk_free_rate
        self.gamma = gamma
        self.allow_short = allow_short

    def optimize(self, returns: pd.DataFrame, **kwargs) -> pd.Series:
        """
        Optimize using mean-variance framework.
        """
        # Calculate expected returns and covariance
        mu = expected_returns.mean_historical_return(returns)
        S = risk_models.sample_cov(returns)

        # Set weight bounds
        weight_bounds = (-1, 1) if self.allow_short else (0, 1)

        # Create efficient frontier
        ef = EfficientFrontier(mu, S, weight_bounds=weight_bounds)

        # Optimize for risk-return tradeoff
        # gamma = 0: min variance, gamma = 1: max return
        ef.max_quadratic_utility(risk_aversion=1 - self.gamma)

        weights = ef.clean_weights()
        weights_series = pd.Series(weights)

        # Store metadata
        self.metadata['expected_return'] = ef.portfolio_performance()[0]
        self.metadata['volatility'] = ef.portfolio_performance()[1]
        self.metadata['sharpe_ratio'] = ef.portfolio_performance()[2]

        return weights_series


class MinimumVarianceOptimizer(BaseOptimizer):
    """
    Minimum Variance Portfolio.
    """

    def __init__(self, allow_short: bool = False):
        super().__init__(name="MinimumVariance")
        self.allow_short = allow_short

    def optimize(self, returns: pd.DataFrame, **kwargs) -> pd.Series:
        """
        Minimize portfolio variance.
        """
        # Calculate covariance
        S = risk_models.sample_cov(returns)

        # Set weight bounds
        weight_bounds = (-1, 1) if self.allow_short else (0, 1)

        # Create efficient frontier
        ef = EfficientFrontier(None, S, weight_bounds=weight_bounds)

        # Minimize variance
        ef.min_volatility()

        weights = ef.clean_weights()
        weights_series = pd.Series(weights)

        # Store metadata
        self.metadata['volatility'] = ef.portfolio_performance()[1]

        return weights_series


class MaximumSharpeOptimizer(BaseOptimizer):
    """
    Maximum Sharpe Ratio Portfolio.
    """

    def __init__(self, risk_free_rate: float = 0.04, allow_short: bool = False):
        super().__init__(name="MaximumSharpe")
        self.risk_free_rate = risk_free_rate
        self.allow_short = allow_short

    def optimize(self, returns: pd.DataFrame, **kwargs) -> pd.Series:
        """
        Maximize Sharpe ratio.
        """
        # Calculate expected returns and covariance
        mu = expected_returns.mean_historical_return(returns)
        S = risk_models.sample_cov(returns)

        # Set weight bounds
        weight_bounds = (-1, 1) if self.allow_short else (0, 1)

        # Create efficient frontier
        ef = EfficientFrontier(mu, S, weight_bounds=weight_bounds)

        # Maximize Sharpe ratio
        ef.max_sharpe(risk_free_rate=self.risk_free_rate)

        weights = ef.clean_weights()
        weights_series = pd.Series(weights)

        # Store metadata
        perf = ef.portfolio_performance(risk_free_rate=self.risk_free_rate)
        self.metadata['expected_return'] = perf[0]
        self.metadata['volatility'] = perf[1]
        self.metadata['sharpe_ratio'] = perf[2]

        return weights_series


class HierarchicalRiskParityOptimizer(BaseOptimizer):
    """
    Hierarchical Risk Parity (HRP).
    Modern approach using clustering.
    """

    def __init__(self, linkage_method: str = "single"):
        super().__init__(name="HierarchicalRiskParity")
        self.linkage_method = linkage_method

    def optimize(self, returns: pd.DataFrame, **kwargs) -> pd.Series:
        """
        Optimize using HRP.
        """
        hrp = HRPOpt(returns)
        hrp.optimize()

        weights = hrp.clean_weights()
        weights_series = pd.Series(weights)

        # Store metadata
        perf = hrp.portfolio_performance()
        self.metadata['expected_return'] = perf[0]
        self.metadata['volatility'] = perf[1]
        self.metadata['sharpe_ratio'] = perf[2]

        return weights_series


class RiskParityOptimizer(BaseOptimizer):
    """
    Risk Parity - Equal risk contribution.
    """

    def __init__(self):
        super().__init__(name="RiskParity")

    def optimize(self, returns: pd.DataFrame, **kwargs) -> pd.Series:
        """
        Optimize for equal risk contribution.
        """
        # Calculate covariance
        S = risk_models.sample_cov(returns)

        # Use pypfopt's risk parity
        rp = RiskParityOpt(S)
        rp.optimize()

        weights = rp.clean_weights()
        weights_series = pd.Series(weights)

        return weights_series


class BlackLittermanOptimizer(BaseOptimizer):
    """
    Black-Litterman Model.
    Bayesian approach combining market equilibrium with investor views.
    """

    def __init__(
        self,
        risk_free_rate: float = 0.04,
        tau: float = 0.05,
        market_caps: Optional[Dict] = None
    ):
        super().__init__(name="BlackLitterman")
        self.risk_free_rate = risk_free_rate
        self.tau = tau
        self.market_caps = market_caps

    def optimize(self, returns: pd.DataFrame, **kwargs) -> pd.Series:
        """
        Optimize using Black-Litterman model.
        """
        # Calculate covariance
        S = risk_models.sample_cov(returns)

        # Market-cap weights (or equal weight if not provided)
        if self.market_caps is not None:
            market_caps_series = pd.Series(self.market_caps)
            market_prior = market_caps_series / market_caps_series.sum()
        else:
            market_prior = pd.Series(1.0 / len(returns.columns), index=returns.columns)

        # Black-Litterman without views (default to market equilibrium)
        bl = BlackLittermanModel(S, pi=market_prior, tau=self.tau)

        # Get posterior returns
        ret_bl = bl.bl_returns()

        # Optimize using Black-Litterman returns
        ef = EfficientFrontier(ret_bl, S)
        ef.max_sharpe(risk_free_rate=self.risk_free_rate)

        weights = ef.clean_weights()
        weights_series = pd.Series(weights)

        # Store metadata
        perf = ef.portfolio_performance(risk_free_rate=self.risk_free_rate)
        self.metadata['expected_return'] = perf[0]
        self.metadata['volatility'] = perf[1]
        self.metadata['sharpe_ratio'] = perf[2]

        return weights_series


class TargetReturnOptimizer(BaseOptimizer):
    """
    Minimize variance for a target return.
    """

    def __init__(self, target_return: float = 0.12, allow_short: bool = False):
        super().__init__(name="TargetReturn")
        self.target_return = target_return
        self.allow_short = allow_short

    def optimize(self, returns: pd.DataFrame, **kwargs) -> pd.Series:
        """
        Minimize variance subject to target return constraint.
        """
        # Calculate expected returns and covariance
        mu = expected_returns.mean_historical_return(returns)
        S = risk_models.sample_cov(returns)

        # Set weight bounds
        weight_bounds = (-1, 1) if self.allow_short else (0, 1)

        # Create efficient frontier
        ef = EfficientFrontier(mu, S, weight_bounds=weight_bounds)

        # Minimize variance for target return
        try:
            ef.efficient_return(target_return=self.target_return)
            weights = ef.clean_weights()
            weights_series = pd.Series(weights)

            # Store metadata
            perf = ef.portfolio_performance()
            self.metadata['expected_return'] = perf[0]
            self.metadata['volatility'] = perf[1]
            self.metadata['sharpe_ratio'] = perf[2]

            return weights_series

        except Exception as e:
            logger.warning(f"Could not achieve target return {self.target_return}: {e}")
            logger.warning("Falling back to maximum Sharpe ratio")

            # Fallback to max Sharpe
            ef = EfficientFrontier(mu, S, weight_bounds=weight_bounds)
            ef.max_sharpe()
            weights = ef.clean_weights()
            return pd.Series(weights)


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

    # Test each optimizer
    optimizers = [
        EqualWeightOptimizer(),
        MeanVarianceOptimizer(),
        MinimumVarianceOptimizer(),
        MaximumSharpeOptimizer(),
        HierarchicalRiskParityOptimizer(),
        RiskParityOptimizer()
    ]

    for opt in optimizers:
        opt.fit(returns)
        weights = opt.get_weights()
        print(f"\n{opt.name}:")
        print(weights.sort_values(ascending=False))
        print(f"Execution time: {opt.execution_time:.4f}s")
