#!/usr/bin/env python3
"""
Main script to run comprehensive portfolio optimization backtesting.
Compares classical and quantum-inspired algorithms.
"""

import sys
from pathlib import Path
import logging
import yaml
import pandas as pd
import numpy as np
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from data_collection.fetchers import DataFetcher, load_tickers_from_config
from data_collection.preprocessors import DataPreprocessor
from optimizers.classical.portfolio_optimizers import (
    EqualWeightOptimizer,
    MeanVarianceOptimizer,
    MinimumVarianceOptimizer,
    MaximumSharpeOptimizer,
    HierarchicalRiskParityOptimizer,
    RiskParityOptimizer
)
from optimizers.quantum_inspired.qaoa_optimizer import QAOAContinuousOptimizer
from optimizers.quantum_inspired.quantum_annealing import (
    QuantumAnnealingOptimizer,
    HybridAnnealingOptimizer
)
from backtesting.engine import BacktestEngine
from visualization.plots import BacktestVisualizer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backtest.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def load_config(config_path: Path) -> dict:
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def main():
    """Main execution function."""
    print("=" * 80)
    print("QUANTUM-INSPIRED PORTFOLIO OPTIMIZATION BACKTEST")
    print("=" * 80)
    print()

    # Load configurations
    logger.info("Loading configurations...")
    config_dir = Path("config")
    assets_config = load_config(config_dir / "assets.yaml")
    backtest_config = load_config(config_dir / "backtest.yaml")
    params_config = load_config(config_dir / "parameters.yaml")

    # Select portfolio
    portfolio_name = "small_portfolio"  # Start with small portfolio
    tickers = assets_config[portfolio_name]['tickers']

    logger.info(f"Selected portfolio: {assets_config[portfolio_name]['name']}")
    logger.info(f"Number of assets: {len(tickers)}")
    logger.info(f"Tickers: {', '.join(tickers)}")

    # Fetch data
    logger.info("\nFetching market data...")
    fetcher = DataFetcher(primary_source="yahoo")

    start_date = backtest_config['period']['start_date']
    end_date = backtest_config['period']['end_date']

    try:
        prices = fetcher.get_prices(tickers, start_date, end_date)
        logger.info(f"Downloaded {len(prices)} days of data")
    except Exception as e:
        logger.error(f"Failed to fetch data: {e}")
        return

    # Preprocess data
    logger.info("Preprocessing data...")
    preprocessor = DataPreprocessor(min_history=126)
    prices_clean = preprocessor.clean_prices(prices)
    returns = preprocessor.calculate_returns(prices_clean, method='simple')

    logger.info(f"Clean data: {len(returns)} days, {len(returns.columns)} assets")

    # Fetch benchmark data
    benchmark_ticker = assets_config['benchmark']['ticker']
    logger.info(f"\nFetching benchmark data ({benchmark_ticker})...")
    benchmark_prices = fetcher.get_prices([benchmark_ticker], start_date, end_date)
    benchmark_returns = preprocessor.calculate_returns(benchmark_prices, method='simple')
    benchmark_returns = benchmark_returns[benchmark_ticker]

    # Initialize optimizers
    logger.info("\nInitializing optimizers...")

    classical_optimizers = [
        EqualWeightOptimizer(),
        MinimumVarianceOptimizer(),
        MaximumSharpeOptimizer(risk_free_rate=params_config['classical']['maximum_sharpe']['risk_free_rate']),
        HierarchicalRiskParityOptimizer(),
        RiskParityOptimizer()
    ]

    quantum_optimizers = []

    # Try to add quantum-inspired optimizers
    try:
        quantum_optimizers.append(QAOAContinuousOptimizer(
            risk_factor=params_config['quantum_inspired']['qaoa']['risk_factor']
        ))
        logger.info("  ✓ QAOA optimizer loaded")
    except Exception as e:
        logger.warning(f"  ✗ QAOA optimizer not available: {e}")

    try:
        quantum_optimizers.append(HybridAnnealingOptimizer(
            num_reads=params_config['quantum_inspired']['quantum_annealing']['num_reads']
        ))
        logger.info("  ✓ Hybrid Annealing optimizer loaded")
    except Exception as e:
        logger.warning(f"  ✗ Hybrid Annealing optimizer not available: {e}")

    all_optimizers = classical_optimizers + quantum_optimizers

    logger.info(f"\nTotal optimizers to test: {len(all_optimizers)}")
    for opt in all_optimizers:
        logger.info(f"  - {opt.name}")

    # Setup backtest engine
    logger.info("\nSetting up backtest engine...")
    engine = BacktestEngine(
        initial_capital=backtest_config['capital']['initial'],
        transaction_cost_pct=backtest_config['transaction_costs']['total_cost_pct'],
        risk_free_rate=backtest_config['performance']['risk_free_rate'],
        rebalance_frequency=backtest_config['rebalancing']['frequency']
    )

    # Run backtests
    logger.info("\n" + "=" * 80)
    logger.info("RUNNING BACKTESTS")
    logger.info("=" * 80)

    comparison_df, results_list = engine.run_multiple_backtests(
        returns=returns,
        optimizers=all_optimizers,
        lookback_window=backtest_config['rebalancing']['lookback_window'],
        benchmark_returns=benchmark_returns
    )

    # Display results
    logger.info("\n" + "=" * 80)
    logger.info("BACKTEST RESULTS")
    logger.info("=" * 80)

    # Sort by Sharpe ratio
    comparison_df_sorted = comparison_df.sort_values('sharpe_ratio', ascending=False)

    print("\n📊 PERFORMANCE SUMMARY")
    print("=" * 80)

    # Display key metrics
    display_cols = [
        'optimizer_name',
        'final_value',
        'total_return_pct',
        'annualized_return',
        'annualized_volatility',
        'sharpe_ratio',
        'maximum_drawdown',
        'win_rate'
    ]

    print(comparison_df_sorted[display_cols].to_string(index=False))

    # Save detailed results
    output_dir = Path(backtest_config['outputs']['results_dir'])
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save comparison CSV
    comparison_file = output_dir / f"comparison_{timestamp}.csv"
    comparison_df_sorted.to_csv(comparison_file, index=False)
    logger.info(f"\n✓ Saved comparison to: {comparison_file}")

    # Save detailed results
    for result in results_list:
        optimizer_name = result['optimizer_name'].replace(' ', '_').lower()

        # Save portfolio values
        values_file = output_dir / f"{optimizer_name}_values_{timestamp}.csv"
        result['portfolio_values'].to_csv(values_file)

        # Save returns
        returns_file = output_dir / f"{optimizer_name}_returns_{timestamp}.csv"
        result['portfolio_returns'].to_csv(returns_file)

    logger.info(f"✓ Saved detailed results to: {output_dir}")

    # Generate visualizations
    logger.info("\n" + "=" * 80)
    logger.info("GENERATING VISUALIZATIONS")
    logger.info("=" * 80)

    visualizer = BacktestVisualizer(output_dir=Path(backtest_config['outputs']['figures_dir']))

    # Calculate benchmark equity curve
    benchmark_values = (1 + benchmark_returns).cumprod() * backtest_config['capital']['initial']

    try:
        visualizer.create_summary_dashboard(
            results_list=results_list,
            comparison_df=comparison_df_sorted,
            benchmark_values=benchmark_values
        )
        logger.info("✓ All visualizations generated successfully")
    except Exception as e:
        logger.error(f"Error generating visualizations: {e}")

    # Print conclusions
    print("\n" + "=" * 80)
    print("🎯 KEY FINDINGS")
    print("=" * 80)

    best_sharpe = comparison_df_sorted.iloc[0]
    print(f"\n🏆 Best Sharpe Ratio: {best_sharpe['optimizer_name']}")
    print(f"   Sharpe Ratio: {best_sharpe['sharpe_ratio']:.4f}")
    print(f"   Annual Return: {best_sharpe['annualized_return']*100:.2f}%")
    print(f"   Volatility: {best_sharpe['annualized_volatility']*100:.2f}%")

    best_return = comparison_df_sorted.nlargest(1, 'annualized_return').iloc[0]
    print(f"\n💰 Highest Return: {best_return['optimizer_name']}")
    print(f"   Annual Return: {best_return['annualized_return']*100:.2f}%")
    print(f"   Total Return: {best_return['total_return_pct']:.2f}%")

    # Drawdowns are negative, so the least severe one is the largest value
    lowest_dd = comparison_df_sorted.nlargest(1, 'maximum_drawdown').iloc[0]
    print(f"\n🛡️  Lowest Drawdown: {lowest_dd['optimizer_name']}")
    print(f"   Max Drawdown: {lowest_dd['maximum_drawdown']*100:.2f}%")

    # Quantum vs Classical comparison
    quantum_results = comparison_df_sorted[comparison_df_sorted['optimizer_name'].str.contains('QAOA|Annealing|Hybrid|Quantum', case=False)]
    classical_results = comparison_df_sorted[~comparison_df_sorted['optimizer_name'].str.contains('QAOA|Annealing|Hybrid|Quantum', case=False)]

    if len(quantum_results) > 0 and len(classical_results) > 0:
        print("\n🔬 QUANTUM-INSPIRED vs CLASSICAL COMPARISON")
        print("=" * 80)
        classical_sharpe = classical_results['sharpe_ratio'].mean()
        quantum_sharpe = quantum_results['sharpe_ratio'].mean()
        print(f"Classical Average Sharpe: {classical_sharpe:.4f}")
        print(f"Quantum-Inspired Average Sharpe: {quantum_sharpe:.4f}")
        # A difference, not a ratio: a ratio is meaningless when the
        # classical average is close to zero or negative
        print(f"Difference (quantum-inspired - classical): {quantum_sharpe - classical_sharpe:+.4f}")

    print("\n" + "=" * 80)
    print("✅ BACKTEST COMPLETE")
    print("=" * 80)
    print(f"\nResults saved to: {output_dir}")
    print(f"Visualizations saved to: {backtest_config['outputs']['figures_dir']}")
    print(f"Log file: backtest.log")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nBacktest interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
