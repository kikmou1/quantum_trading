"""
Visualization module for backtest results.
Generate charts and plots for analysis.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Dict, Optional
from pathlib import Path

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)


class BacktestVisualizer:
    """
    Create visualizations for backtest results.
    """

    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize visualizer.

        Args:
            output_dir: Directory to save plots
        """
        self.output_dir = output_dir or Path("results/figures")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def plot_equity_curves(
        self,
        results_list: List[Dict],
        benchmark_values: Optional[pd.Series] = None,
        save: bool = True
    ):
        """
        Plot equity curves for all strategies.

        Args:
            results_list: List of backtest results
            benchmark_values: Optional benchmark equity curve
            save: Whether to save the plot
        """
        fig, ax = plt.subplots(figsize=(14, 7))

        for result in results_list:
            portfolio_values = result['portfolio_values']['value']
            ax.plot(
                portfolio_values.index,
                portfolio_values.values,
                label=result['optimizer_name'],
                linewidth=2
            )

        if benchmark_values is not None:
            ax.plot(
                benchmark_values.index,
                benchmark_values.values,
                label='Benchmark',
                linewidth=2,
                linestyle='--',
                color='black',
                alpha=0.7
            )

        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Portfolio Value ($)', fontsize=12)
        ax.set_title('Portfolio Equity Curves', fontsize=14, fontweight='bold')
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if save:
            plt.savefig(self.output_dir / 'equity_curves.png', dpi=300, bbox_inches='tight')
            print(f"Saved: {self.output_dir / 'equity_curves.png'}")

        plt.show()

    def plot_drawdowns(
        self,
        results_list: List[Dict],
        save: bool = True
    ):
        """
        Plot drawdowns for all strategies.

        Args:
            results_list: List of backtest results
            save: Whether to save the plot
        """
        fig, ax = plt.subplots(figsize=(14, 7))

        for result in results_list:
            returns = result['portfolio_returns']
            cum_returns = (1 + returns).cumprod()
            running_max = cum_returns.expanding().max()
            drawdown = (cum_returns - running_max) / running_max * 100

            ax.plot(
                drawdown.index,
                drawdown.values,
                label=result['optimizer_name'],
                linewidth=2
            )

        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Drawdown (%)', fontsize=12)
        ax.set_title('Portfolio Drawdowns', fontsize=14, fontweight='bold')
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)

        plt.tight_layout()

        if save:
            plt.savefig(self.output_dir / 'drawdowns.png', dpi=300, bbox_inches='tight')
            print(f"Saved: {self.output_dir / 'drawdowns.png'}")

        plt.show()

    def plot_risk_return_scatter(
        self,
        comparison_df: pd.DataFrame,
        save: bool = True
    ):
        """
        Plot risk-return scatter plot.

        Args:
            comparison_df: DataFrame with comparison metrics
            save: Whether to save the plot
        """
        fig, ax = plt.subplots(figsize=(10, 8))

        # Scatter plot
        scatter = ax.scatter(
            comparison_df['annualized_volatility'] * 100,
            comparison_df['annualized_return'] * 100,
            s=200,
            alpha=0.6,
            c=comparison_df['sharpe_ratio'],
            cmap='viridis'
        )

        # Add labels for each point
        for idx, row in comparison_df.iterrows():
            ax.annotate(
                row['optimizer_name'],
                (row['annualized_volatility'] * 100, row['annualized_return'] * 100),
                xytext=(5, 5),
                textcoords='offset points',
                fontsize=9
            )

        ax.set_xlabel('Annualized Volatility (%)', fontsize=12)
        ax.set_ylabel('Annualized Return (%)', fontsize=12)
        ax.set_title('Risk-Return Profile', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)

        # Add colorbar
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label('Sharpe Ratio', fontsize=11)

        plt.tight_layout()

        if save:
            plt.savefig(self.output_dir / 'risk_return_scatter.png', dpi=300, bbox_inches='tight')
            print(f"Saved: {self.output_dir / 'risk_return_scatter.png'}")

        plt.show()

    def plot_metrics_comparison(
        self,
        comparison_df: pd.DataFrame,
        metrics: List[str],
        save: bool = True
    ):
        """
        Plot bar chart comparing metrics across strategies.

        Args:
            comparison_df: DataFrame with comparison metrics
            metrics: List of metrics to plot
            save: Whether to save the plot
        """
        n_metrics = len(metrics)
        fig, axes = plt.subplots(
            nrows=(n_metrics + 1) // 2,
            ncols=2,
            figsize=(14, 4 * ((n_metrics + 1) // 2))
        )

        axes = axes.flatten() if n_metrics > 1 else [axes]

        for idx, metric in enumerate(metrics):
            ax = axes[idx]

            comparison_df.plot(
                x='optimizer_name',
                y=metric,
                kind='bar',
                ax=ax,
                legend=False
            )

            ax.set_xlabel('')
            ax.set_ylabel(metric.replace('_', ' ').title(), fontsize=11)
            ax.set_title(f'{metric.replace("_", " ").title()}', fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3, axis='y')
            ax.set_xticklabels(comparison_df['optimizer_name'], rotation=45, ha='right')

        # Hide unused subplots
        for idx in range(len(metrics), len(axes)):
            axes[idx].axis('off')

        plt.tight_layout()

        if save:
            plt.savefig(self.output_dir / 'metrics_comparison.png', dpi=300, bbox_inches='tight')
            print(f"Saved: {self.output_dir / 'metrics_comparison.png'}")

        plt.show()

    def plot_returns_distribution(
        self,
        results_list: List[Dict],
        save: bool = True
    ):
        """
        Plot distribution of returns for all strategies.

        Args:
            results_list: List of backtest results
            save: Whether to save the plot
        """
        fig, ax = plt.subplots(figsize=(14, 7))

        for result in results_list:
            returns = result['portfolio_returns'] * 100  # Convert to percentage

            ax.hist(
                returns,
                bins=50,
                alpha=0.5,
                label=result['optimizer_name']
            )

        ax.set_xlabel('Daily Returns (%)', fontsize=12)
        ax.set_ylabel('Frequency', fontsize=12)
        ax.set_title('Returns Distribution', fontsize=14, fontweight='bold')
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3, axis='y')
        ax.axvline(x=0, color='black', linestyle='--', linewidth=1)

        plt.tight_layout()

        if save:
            plt.savefig(self.output_dir / 'returns_distribution.png', dpi=300, bbox_inches='tight')
            print(f"Saved: {self.output_dir / 'returns_distribution.png'}")

        plt.show()

    def plot_rolling_sharpe(
        self,
        results_list: List[Dict],
        window: int = 252,
        save: bool = True
    ):
        """
        Plot rolling Sharpe ratio.

        Args:
            results_list: List of backtest results
            window: Rolling window size
            save: Whether to save the plot
        """
        fig, ax = plt.subplots(figsize=(14, 7))

        for result in results_list:
            returns = result['portfolio_returns']

            rolling_return = returns.rolling(window).mean() * 252
            rolling_vol = returns.rolling(window).std() * np.sqrt(252)
            rolling_sharpe = rolling_return / rolling_vol

            ax.plot(
                rolling_sharpe.index,
                rolling_sharpe.values,
                label=result['optimizer_name'],
                linewidth=2
            )

        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Rolling Sharpe Ratio', fontsize=12)
        ax.set_title(f'Rolling Sharpe Ratio ({window}-day window)', fontsize=14, fontweight='bold')
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)
        ax.axhline(y=0, color='black', linestyle='--', linewidth=1)

        plt.tight_layout()

        if save:
            plt.savefig(self.output_dir / 'rolling_sharpe.png', dpi=300, bbox_inches='tight')
            print(f"Saved: {self.output_dir / 'rolling_sharpe.png'}")

        plt.show()

    def create_summary_dashboard(
        self,
        results_list: List[Dict],
        comparison_df: pd.DataFrame,
        benchmark_values: Optional[pd.Series] = None
    ):
        """
        Create a comprehensive dashboard with all key visualizations.

        Args:
            results_list: List of backtest results
            comparison_df: DataFrame with comparison metrics
            benchmark_values: Optional benchmark equity curve
        """
        print("Generating comprehensive dashboard...")

        self.plot_equity_curves(results_list, benchmark_values, save=True)
        self.plot_drawdowns(results_list, save=True)
        self.plot_risk_return_scatter(comparison_df, save=True)

        metrics_to_compare = [
            'sharpe_ratio',
            'sortino_ratio',
            'maximum_drawdown',
            'calmar_ratio',
            'win_rate',
            'avg_turnover'
        ]

        self.plot_metrics_comparison(comparison_df, metrics_to_compare, save=True)
        self.plot_returns_distribution(results_list, save=True)
        self.plot_rolling_sharpe(results_list, save=True)

        print(f"\nAll visualizations saved to: {self.output_dir}")


if __name__ == "__main__":
    # Example usage would require actual backtest results
    print("Visualization module loaded successfully")
