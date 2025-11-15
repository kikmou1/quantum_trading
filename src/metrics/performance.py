"""
Performance metrics for portfolio backtesting.
Calculate returns, Sharpe ratio, and other performance indicators.
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """
    Calculate portfolio performance metrics.
    """

    def __init__(self, risk_free_rate: float = 0.04, periods_per_year: int = 252):
        """
        Initialize performance metrics calculator.

        Args:
            risk_free_rate: Annual risk-free rate
            periods_per_year: Number of periods per year (252 for daily, 12 for monthly)
        """
        self.risk_free_rate = risk_free_rate
        self.periods_per_year = periods_per_year

    def total_return(self, returns: pd.Series) -> float:
        """
        Calculate total return.

        Args:
            returns: Series of returns

        Returns:
            Total return as decimal
        """
        return (1 + returns).prod() - 1

    def annualized_return(self, returns: pd.Series) -> float:
        """
        Calculate annualized return (CAGR).

        Args:
            returns: Series of returns

        Returns:
            Annualized return
        """
        total_ret = self.total_return(returns)
        n_periods = len(returns)
        n_years = n_periods / self.periods_per_year

        if n_years > 0:
            return (1 + total_ret) ** (1 / n_years) - 1
        else:
            return 0.0

    def annualized_volatility(self, returns: pd.Series) -> float:
        """
        Calculate annualized volatility.

        Args:
            returns: Series of returns

        Returns:
            Annualized standard deviation
        """
        return returns.std() * np.sqrt(self.periods_per_year)

    def sharpe_ratio(self, returns: pd.Series) -> float:
        """
        Calculate Sharpe ratio.

        Args:
            returns: Series of returns

        Returns:
            Sharpe ratio
        """
        ann_return = self.annualized_return(returns)
        ann_vol = self.annualized_volatility(returns)

        if ann_vol > 0:
            return (ann_return - self.risk_free_rate) / ann_vol
        else:
            return 0.0

    def sortino_ratio(self, returns: pd.Series) -> float:
        """
        Calculate Sortino ratio (only penalizes downside volatility).

        Args:
            returns: Series of returns

        Returns:
            Sortino ratio
        """
        ann_return = self.annualized_return(returns)
        downside_returns = returns[returns < 0]

        if len(downside_returns) > 0:
            downside_vol = downside_returns.std() * np.sqrt(self.periods_per_year)
            if downside_vol > 0:
                return (ann_return - self.risk_free_rate) / downside_vol
        return 0.0

    def calmar_ratio(self, returns: pd.Series) -> float:
        """
        Calculate Calmar ratio (return / max drawdown).

        Args:
            returns: Series of returns

        Returns:
            Calmar ratio
        """
        ann_return = self.annualized_return(returns)
        max_dd = self.maximum_drawdown(returns)

        if max_dd < 0:
            return ann_return / abs(max_dd)
        else:
            return 0.0

    def maximum_drawdown(self, returns: pd.Series) -> float:
        """
        Calculate maximum drawdown.

        Args:
            returns: Series of returns

        Returns:
            Maximum drawdown as negative decimal
        """
        cum_returns = (1 + returns).cumprod()
        running_max = cum_returns.expanding().max()
        drawdown = (cum_returns - running_max) / running_max

        return drawdown.min()

    def drawdown_series(self, returns: pd.Series) -> pd.Series:
        """
        Calculate drawdown time series.

        Args:
            returns: Series of returns

        Returns:
            Series of drawdowns
        """
        cum_returns = (1 + returns).cumprod()
        running_max = cum_returns.expanding().max()
        drawdown = (cum_returns - running_max) / running_max

        return drawdown

    def win_rate(self, returns: pd.Series) -> float:
        """
        Calculate win rate (percentage of positive periods).

        Args:
            returns: Series of returns

        Returns:
            Win rate as decimal
        """
        return (returns > 0).sum() / len(returns)

    def omega_ratio(self, returns: pd.Series, threshold: float = 0.0) -> float:
        """
        Calculate Omega ratio.

        Args:
            returns: Series of returns
            threshold: Threshold return (default 0)

        Returns:
            Omega ratio
        """
        excess_returns = returns - threshold / self.periods_per_year

        gains = excess_returns[excess_returns > 0].sum()
        losses = abs(excess_returns[excess_returns < 0].sum())

        if losses > 0:
            return gains / losses
        else:
            return np.inf if gains > 0 else 0.0

    def information_ratio(
        self,
        returns: pd.Series,
        benchmark_returns: pd.Series
    ) -> float:
        """
        Calculate Information ratio vs benchmark.

        Args:
            returns: Portfolio returns
            benchmark_returns: Benchmark returns

        Returns:
            Information ratio
        """
        excess_returns = returns - benchmark_returns
        tracking_error = excess_returns.std() * np.sqrt(self.periods_per_year)

        if tracking_error > 0:
            return (excess_returns.mean() * self.periods_per_year) / tracking_error
        else:
            return 0.0

    def alpha_beta(
        self,
        returns: pd.Series,
        benchmark_returns: pd.Series
    ) -> tuple:
        """
        Calculate alpha and beta vs benchmark.

        Args:
            returns: Portfolio returns
            benchmark_returns: Benchmark returns

        Returns:
            Tuple of (alpha, beta)
        """
        # Ensure aligned indices
        aligned = pd.DataFrame({'portfolio': returns, 'benchmark': benchmark_returns}).dropna()

        if len(aligned) < 2:
            return 0.0, 1.0

        portfolio_ret = aligned['portfolio']
        benchmark_ret = aligned['benchmark']

        # Calculate beta
        covariance = portfolio_ret.cov(benchmark_ret)
        benchmark_variance = benchmark_ret.var()

        if benchmark_variance > 0:
            beta = covariance / benchmark_variance
        else:
            beta = 1.0

        # Calculate alpha
        portfolio_mean = portfolio_ret.mean() * self.periods_per_year
        benchmark_mean = benchmark_ret.mean() * self.periods_per_year

        alpha = portfolio_mean - self.risk_free_rate - beta * (benchmark_mean - self.risk_free_rate)

        return alpha, beta

    def calculate_all_metrics(
        self,
        returns: pd.Series,
        benchmark_returns: Optional[pd.Series] = None
    ) -> Dict[str, float]:
        """
        Calculate all performance metrics.

        Args:
            returns: Portfolio returns
            benchmark_returns: Optional benchmark returns

        Returns:
            Dictionary of all metrics
        """
        metrics = {
            'total_return': self.total_return(returns),
            'annualized_return': self.annualized_return(returns),
            'annualized_volatility': self.annualized_volatility(returns),
            'sharpe_ratio': self.sharpe_ratio(returns),
            'sortino_ratio': self.sortino_ratio(returns),
            'calmar_ratio': self.calmar_ratio(returns),
            'maximum_drawdown': self.maximum_drawdown(returns),
            'win_rate': self.win_rate(returns),
            'omega_ratio': self.omega_ratio(returns)
        }

        if benchmark_returns is not None:
            alpha, beta = self.alpha_beta(returns, benchmark_returns)
            metrics['alpha'] = alpha
            metrics['beta'] = beta
            metrics['information_ratio'] = self.information_ratio(returns, benchmark_returns)

        return metrics

    def rolling_sharpe(
        self,
        returns: pd.Series,
        window: int = 252
    ) -> pd.Series:
        """
        Calculate rolling Sharpe ratio.

        Args:
            returns: Series of returns
            window: Rolling window size

        Returns:
            Series of rolling Sharpe ratios
        """
        rolling_return = returns.rolling(window).mean() * self.periods_per_year
        rolling_vol = returns.rolling(window).std() * np.sqrt(self.periods_per_year)

        rolling_sharpe = (rolling_return - self.risk_free_rate) / rolling_vol

        return rolling_sharpe


if __name__ == "__main__":
    # Example usage
    np.random.seed(42)

    # Generate sample returns
    dates = pd.date_range('2020-01-01', '2023-01-01', freq='D')
    returns = pd.Series(np.random.randn(len(dates)) * 0.01 + 0.0003, index=dates)

    # Calculate metrics
    metrics_calc = PerformanceMetrics(risk_free_rate=0.04, periods_per_year=252)
    metrics = metrics_calc.calculate_all_metrics(returns)

    print("Performance Metrics:")
    for key, value in metrics.items():
        if 'ratio' in key or 'return' in key or 'volatility' in key:
            print(f"{key:25s}: {value:8.4f}")
        else:
            print(f"{key:25s}: {value:8.4f}")
