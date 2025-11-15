"""
Base optimizer class for all portfolio optimization algorithms.
"""

from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any
import time


class BaseOptimizer(ABC):
    """
    Abstract base class for all portfolio optimizers.
    """

    def __init__(self, name: str = "BaseOptimizer"):
        """
        Initialize optimizer.

        Args:
            name: Name of the optimizer
        """
        self.name = name
        self.weights = None
        self.execution_time = None
        self.metadata = {}

    @abstractmethod
    def optimize(
        self,
        returns: pd.DataFrame,
        **kwargs
    ) -> pd.Series:
        """
        Optimize portfolio weights.

        Args:
            returns: DataFrame of asset returns
            **kwargs: Additional parameters

        Returns:
            Series of optimal weights (indexed by asset)
        """
        pass

    def fit(self, returns: pd.DataFrame, **kwargs) -> 'BaseOptimizer':
        """
        Fit the optimizer (scikit-learn style interface).

        Args:
            returns: DataFrame of asset returns
            **kwargs: Additional parameters

        Returns:
            self
        """
        start_time = time.time()
        self.weights = self.optimize(returns, **kwargs)
        self.execution_time = time.time() - start_time
        return self

    def get_weights(self) -> pd.Series:
        """
        Get the optimized weights.

        Returns:
            Series of weights
        """
        if self.weights is None:
            raise ValueError("Optimizer has not been fitted yet")
        return self.weights

    def normalize_weights(self, weights: pd.Series) -> pd.Series:
        """
        Normalize weights to sum to 1.

        Args:
            weights: Raw weights

        Returns:
            Normalized weights
        """
        weight_sum = weights.abs().sum()
        if weight_sum > 0:
            return weights / weight_sum
        else:
            # Equal weight if all weights are zero
            return pd.Series(1.0 / len(weights), index=weights.index)

    def apply_constraints(
        self,
        weights: pd.Series,
        min_weight: float = 0.0,
        max_weight: float = 1.0
    ) -> pd.Series:
        """
        Apply weight constraints and renormalize.

        Args:
            weights: Input weights
            min_weight: Minimum weight per asset
            max_weight: Maximum weight per asset

        Returns:
            Constrained weights
        """
        weights_constrained = weights.clip(lower=min_weight, upper=max_weight)
        return self.normalize_weights(weights_constrained)

    def get_metadata(self) -> Dict[str, Any]:
        """
        Get optimizer metadata.

        Returns:
            Dictionary with metadata
        """
        return {
            'name': self.name,
            'execution_time': self.execution_time,
            **self.metadata
        }

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"
