"""
Risk metrics for portfolio backtesting.
Calculate VaR, CVaR, and other risk indicators.
"""

import pandas as pd
import numpy as np
from typing import Optional
from scipy import stats


class RiskMetrics:
    """
    Calculate portfolio risk metrics.
    """

    def __init__(self, confidence_level: float = 0.95):
        """
        Initialize risk metrics calculator.

        Args:
            confidence_level: Confidence level for VaR/CVaR (default 0.95)
        """
        self.confidence_level = confidence_level

    def value_at_risk(
        self,
        returns: pd.Series,
        method: str = "historical"
    ) -> float:
        """
        Calculate Value at Risk (VaR).

        Args:
            returns: Series of returns
            method: 'historical', 'parametric', or 'cornish_fisher'

        Returns:
            VaR as positive number (loss magnitude)
        """
        if method == "historical":
            return abs(returns.quantile(1 - self.confidence_level))

        elif method == "parametric":
            mean = returns.mean()
            std = returns.std()
            z_score = stats.norm.ppf(1 - self.confidence_level)
            return abs(mean + std * z_score)

        elif method == "cornish_fisher":
            mean = returns.mean()
            std = returns.std()
            skew = returns.skew()
            kurt = returns.kurtosis()

            # Cornish-Fisher expansion
            z = stats.norm.ppf(1 - self.confidence_level)
            cf_z = (z + (z**2 - 1) * skew / 6 +
                   (z**3 - 3*z) * kurt / 24 -
                   (2*z**3 - 5*z) * skew**2 / 36)

            return abs(mean + std * cf_z)

        else:
            raise ValueError(f"Unknown VaR method: {method}")

    def conditional_var(
        self,
        returns: pd.Series,
        method: str = "historical"
    ) -> float:
        """
        Calculate Conditional Value at Risk (CVaR / Expected Shortfall).

        Args:
            returns: Series of returns
            method: 'historical' or 'parametric'

        Returns:
            CVaR as positive number
        """
        if method == "historical":
            var = self.value_at_risk(returns, method="historical")
            # Average of returns worse than VaR
            tail_returns = returns[returns <= -var]
            if len(tail_returns) > 0:
                return abs(tail_returns.mean())
            else:
                return var

        elif method == "parametric":
            mean = returns.mean()
            std = returns.std()
            z_alpha = stats.norm.ppf(1 - self.confidence_level)

            # CVaR for normal distribution
            cvar = mean - std * stats.norm.pdf(z_alpha) / (1 - self.confidence_level)
            return abs(cvar)

        else:
            raise ValueError(f"Unknown CVaR method: {method}")

    def downside_deviation(
        self,
        returns: pd.Series,
        mar: float = 0.0
    ) -> float:
        """
        Calculate downside deviation (semi-deviation).

        Args:
            returns: Series of returns
            mar: Minimum acceptable return (default 0)

        Returns:
            Downside deviation
        """
        downside_returns = returns[returns < mar]
        if len(downside_returns) > 0:
            return downside_returns.std()
        else:
            return 0.0

    def max_consecutive_losses(self, returns: pd.Series) -> int:
        """
        Calculate maximum consecutive losing periods.

        Args:
            returns: Series of returns

        Returns:
            Maximum consecutive losses
        """
        is_loss = returns < 0
        consecutive = (is_loss != is_loss.shift()).cumsum()
        loss_streaks = is_loss.groupby(consecutive).sum()

        if len(loss_streaks) > 0:
            return int(loss_streaks.max())
        else:
            return 0

    def tail_ratio(self, returns: pd.Series) -> float:
        """
        Calculate tail ratio (95th percentile / 5th percentile).

        Args:
            returns: Series of returns

        Returns:
            Tail ratio
        """
        p95 = returns.quantile(0.95)
        p05 = returns.quantile(0.05)

        if p05 != 0:
            return abs(p95 / p05)
        else:
            return np.inf

    def skewness(self, returns: pd.Series) -> float:
        """
        Calculate skewness of returns.

        Args:
            returns: Series of returns

        Returns:
            Skewness
        """
        return returns.skew()

    def kurtosis(self, returns: pd.Series) -> float:
        """
        Calculate excess kurtosis of returns.

        Args:
            returns: Series of returns

        Returns:
            Excess kurtosis
        """
        return returns.kurtosis()

    def calculate_all_risk_metrics(self, returns: pd.Series) -> dict:
        """
        Calculate all risk metrics.

        Args:
            returns: Series of returns

        Returns:
            Dictionary of risk metrics
        """
        metrics = {
            'var_historical': self.value_at_risk(returns, method='historical'),
            'var_parametric': self.value_at_risk(returns, method='parametric'),
            'cvar_historical': self.conditional_var(returns, method='historical'),
            'cvar_parametric': self.conditional_var(returns, method='parametric'),
            'downside_deviation': self.downside_deviation(returns),
            'max_consecutive_losses': self.max_consecutive_losses(returns),
            'tail_ratio': self.tail_ratio(returns),
            'skewness': self.skewness(returns),
            'kurtosis': self.kurtosis(returns)
        }

        return metrics


if __name__ == "__main__":
    # Example usage
    np.random.seed(42)

    dates = pd.date_range('2020-01-01', '2023-01-01', freq='D')
    returns = pd.Series(np.random.randn(len(dates)) * 0.01, index=dates)

    risk_calc = RiskMetrics(confidence_level=0.95)
    metrics = risk_calc.calculate_all_risk_metrics(returns)

    print("Risk Metrics:")
    for key, value in metrics.items():
        print(f"{key:30s}: {value:8.4f}")
