"""
Backtesting engine for portfolio optimization strategies.
Simulates portfolio performance over time with rebalancing and transaction costs.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Callable
import logging
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))
from metrics.performance import PerformanceMetrics
from metrics.risk import RiskMetrics

logger = logging.getLogger(__name__)


class BacktestEngine:
    """
    Backtest portfolio optimization strategies.
    """

    def __init__(
        self,
        initial_capital: float = 100000.0,
        transaction_cost_pct: float = 0.0015,
        risk_free_rate: float = 0.04,
        rebalance_frequency: str = "monthly"
    ):
        """
        Initialize backtest engine.

        Args:
            initial_capital: Starting capital
            transaction_cost_pct: Transaction cost as percentage (e.g., 0.0015 = 15 bps)
            risk_free_rate: Risk-free rate for Sharpe calculation
            rebalance_frequency: 'daily', 'weekly', 'monthly', 'quarterly'
        """
        self.initial_capital = initial_capital
        self.transaction_cost_pct = transaction_cost_pct
        self.risk_free_rate = risk_free_rate
        self.rebalance_frequency = rebalance_frequency

        self.performance_calc = PerformanceMetrics(risk_free_rate=risk_free_rate)
        self.risk_calc = RiskMetrics()

    def run_backtest(
        self,
        returns: pd.DataFrame,
        optimizer,
        lookback_window: int = 252,
        benchmark_returns: Optional[pd.Series] = None,
        **optimizer_kwargs
    ) -> Dict:
        """
        Run backtest for a single optimizer.

        Args:
            returns: DataFrame of asset returns
            optimizer: Optimizer instance
            lookback_window: Number of periods to use for optimization
            benchmark_returns: Optional benchmark returns for alpha, beta
                and information ratio
            **optimizer_kwargs: Additional kwargs for optimizer

        Returns:
            Dictionary with backtest results
        """
        # Determine rebalancing dates
        rebalance_dates = self._get_rebalance_dates(returns.index)

        # Initialize tracking
        portfolio_values = []
        portfolio_weights_over_time = []
        turnover_list = []

        current_weights = None
        current_value = self.initial_capital

        for i, date in enumerate(returns.index):
            # Check if we need to rebalance
            if date in rebalance_dates and i >= lookback_window:
                # Get training data
                train_returns = returns.iloc[i-lookback_window:i]

                # Optimize
                try:
                    new_weights = optimizer.optimize(train_returns, **optimizer_kwargs)

                    # Calculate turnover
                    if current_weights is not None:
                        turnover = self._calculate_turnover(current_weights, new_weights)
                        turnover_list.append(turnover)

                        # Apply transaction costs
                        transaction_cost = turnover * self.transaction_cost_pct * current_value
                        current_value -= transaction_cost
                    else:
                        turnover_list.append(0.0)

                    current_weights = new_weights

                    portfolio_weights_over_time.append({
                        'date': date,
                        'weights': new_weights.to_dict()
                    })

                except Exception as e:
                    logger.error(f"Optimization failed on {date}: {e}")
                    if current_weights is None:
                        # Equal weight fallback
                        current_weights = pd.Series(
                            1.0 / len(returns.columns),
                            index=returns.columns
                        )

            # Calculate portfolio return for this period
            if current_weights is not None and i > 0:
                period_return = (returns.iloc[i] * current_weights).sum()
                current_value *= (1 + period_return)

            portfolio_values.append({
                'date': date,
                'value': current_value
            })

        # Convert to DataFrames. Performance is measured from the first
        # allocation; before it the portfolio is uninvested during the
        # lookback window, and those flat days would dilute every metric.
        portfolio_values_df = pd.DataFrame(portfolio_values).set_index('date')
        if portfolio_weights_over_time:
            # Start one day earlier so the first invested day's return counts
            first_allocation = portfolio_weights_over_time[0]['date']
            start = max(portfolio_values_df.index.get_loc(first_allocation) - 1, 0)
            portfolio_values_df = portfolio_values_df.iloc[start:]
        portfolio_returns = portfolio_values_df['value'].pct_change().dropna()

        # Calculate metrics
        if benchmark_returns is not None:
            benchmark_returns = benchmark_returns.reindex(portfolio_returns.index)
        performance_metrics = self.performance_calc.calculate_all_metrics(
            portfolio_returns, benchmark_returns
        )
        risk_metrics = self.risk_calc.calculate_all_risk_metrics(portfolio_returns)

        # Additional metrics
        avg_turnover = np.mean(turnover_list) if turnover_list else 0.0

        results = {
            'optimizer_name': optimizer.name,
            'portfolio_values': portfolio_values_df,
            'portfolio_returns': portfolio_returns,
            'weights_over_time': portfolio_weights_over_time,
            'final_value': current_value,
            'total_return_pct': (current_value / self.initial_capital - 1) * 100,
            'avg_turnover': avg_turnover,
            'n_rebalances': len(rebalance_dates),
            **performance_metrics,
            **risk_metrics
        }

        return results

    def run_multiple_backtests(
        self,
        returns: pd.DataFrame,
        optimizers: List,
        lookback_window: int = 252,
        benchmark_returns: Optional[pd.Series] = None
    ) -> pd.DataFrame:
        """
        Run backtests for multiple optimizers and compare.

        Args:
            returns: DataFrame of asset returns
            optimizers: List of optimizer instances
            lookback_window: Number of periods for optimization
            benchmark_returns: Optional benchmark returns for comparison

        Returns:
            DataFrame with comparison of all optimizers
        """
        results_list = []

        for optimizer in optimizers:
            logger.info(f"Running backtest for {optimizer.name}...")

            try:
                result = self.run_backtest(
                    returns,
                    optimizer,
                    lookback_window=lookback_window,
                    benchmark_returns=benchmark_returns
                )

                # Add benchmark comparison if available
                if benchmark_returns is not None:
                    portfolio_returns = result['portfolio_returns']

                    # Align returns
                    aligned = pd.DataFrame({
                        'portfolio': portfolio_returns,
                        'benchmark': benchmark_returns
                    }).dropna()

                    if len(aligned) > 0:
                        excess_returns = aligned['portfolio'] - aligned['benchmark']
                        result['excess_return'] = excess_returns.mean() * 252
                        result['tracking_error'] = excess_returns.std() * np.sqrt(252)

                results_list.append(result)

            except Exception as e:
                logger.error(f"Backtest failed for {optimizer.name}: {e}")
                continue

        # Create comparison DataFrame
        comparison_metrics = [
            'optimizer_name',
            'final_value',
            'total_return_pct',
            'annualized_return',
            'annualized_volatility',
            'sharpe_ratio',
            'sortino_ratio',
            'calmar_ratio',
            'maximum_drawdown',
            'var_historical',
            'cvar_historical',
            'win_rate',
            'avg_turnover'
        ]

        if benchmark_returns is not None:
            comparison_metrics.extend(
                ['excess_return', 'tracking_error', 'alpha', 'beta', 'information_ratio']
            )

        comparison = []
        for result in results_list:
            row = {metric: result.get(metric, np.nan) for metric in comparison_metrics}
            comparison.append(row)

        comparison_df = pd.DataFrame(comparison)

        return comparison_df, results_list

    def _get_rebalance_dates(self, dates: pd.DatetimeIndex) -> List:
        """
        Get rebalancing dates based on frequency.

        Args:
            dates: DatetimeIndex of all dates

        Returns:
            List of rebalancing dates
        """
        if self.rebalance_frequency == "daily":
            return dates.tolist()

        elif self.rebalance_frequency == "weekly":
            # First day of each week
            return [dates[i] for i in range(len(dates)) if dates[i].dayofweek == 0]

        elif self.rebalance_frequency == "monthly":
            # First trading day of each month
            rebalance_dates = []
            current_month = None

            for date in dates:
                if current_month != date.month:
                    rebalance_dates.append(date)
                    current_month = date.month

            return rebalance_dates

        elif self.rebalance_frequency == "quarterly":
            # First trading day of each quarter
            rebalance_dates = []
            current_quarter = None

            for date in dates:
                quarter = (date.month - 1) // 3
                if current_quarter != quarter:
                    rebalance_dates.append(date)
                    current_quarter = quarter

            return rebalance_dates

        else:
            raise ValueError(f"Unknown rebalance frequency: {self.rebalance_frequency}")

    def _calculate_turnover(self, old_weights: pd.Series, new_weights: pd.Series) -> float:
        """
        Calculate portfolio turnover.

        Args:
            old_weights: Previous weights
            new_weights: New weights

        Returns:
            Turnover as decimal
        """
        # Align indices
        all_assets = old_weights.index.union(new_weights.index)
        old_weights = old_weights.reindex(all_assets, fill_value=0)
        new_weights = new_weights.reindex(all_assets, fill_value=0)

        # Turnover is the sum of absolute changes
        turnover = (old_weights - new_weights).abs().sum() / 2

        return turnover


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Generate sample data
    np.random.seed(42)
    dates = pd.date_range('2020-01-01', '2023-01-01', freq='D')
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA']

    returns = pd.DataFrame(
        np.random.randn(len(dates), len(tickers)) * 0.01 + 0.0003,
        index=dates,
        columns=tickers
    )

    # Import optimizers
    sys.path.append(str(Path(__file__).parent.parent / 'optimizers'))
    from classical.portfolio_optimizers import (
        EqualWeightOptimizer,
        MaximumSharpeOptimizer
    )

    # Run backtest
    engine = BacktestEngine(
        initial_capital=100000,
        transaction_cost_pct=0.0015,
        rebalance_frequency="monthly"
    )

    optimizers = [
        EqualWeightOptimizer(),
        MaximumSharpeOptimizer()
    ]

    comparison, results = engine.run_multiple_backtests(
        returns,
        optimizers,
        lookback_window=126
    )

    print("\nBacktest Comparison:")
    print(comparison.to_string())
