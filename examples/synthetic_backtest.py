#!/usr/bin/env python3
"""
Offline example: backtest every optimizer on synthetic data.

Needs no internet connection and no quantum libraries, and uses a fixed random
seed, so the output is reproducible. Run from the repository root:

    python examples/synthetic_backtest.py

The market is simulated with a one-factor model (a common market factor plus
asset-specific noise). The results only show that the pipeline works; they say
nothing about how any method would perform on real markets.
"""

import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from backtesting.engine import BacktestEngine  # noqa: E402
from optimizers.classical.portfolio_optimizers import (  # noqa: E402
    BlackLittermanOptimizer,
    EqualWeightOptimizer,
    HierarchicalRiskParityOptimizer,
    MaximumSharpeOptimizer,
    MinimumVarianceOptimizer,
    RiskParityOptimizer,
)
from optimizers.quantum_inspired.qaoa_optimizer import QAOAContinuousOptimizer  # noqa: E402
from optimizers.quantum_inspired.quantum_annealing import HybridAnnealingOptimizer  # noqa: E402


def simulate_returns(n_days: int = 1260, seed: int = 4) -> pd.DataFrame:
    """Daily simple returns for 8 assets driven by one market factor."""
    rng = np.random.default_rng(seed)
    tickers = ["AAA", "BBB", "CCC", "DDD", "EEE", "FFF", "GGG", "HHH"]
    betas = np.array([0.6, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.5])
    idio_vol = np.array([0.006, 0.008, 0.010, 0.012, 0.014, 0.016, 0.018, 0.022])
    alpha = np.array([0.0002, 0.0001, 0.0003, 0.0000, 0.0002, 0.0001, 0.0000, -0.0001])

    market = rng.normal(0.0004, 0.01, n_days)
    noise = rng.normal(0.0, 1.0, (n_days, len(tickers))) * idio_vol
    data = alpha + np.outer(market, betas) + noise

    dates = pd.bdate_range("2019-01-01", periods=n_days)
    return pd.DataFrame(data, index=dates, columns=tickers)


def main():
    logging.basicConfig(level=logging.ERROR)
    returns = simulate_returns()

    optimizers = [
        EqualWeightOptimizer(),
        MinimumVarianceOptimizer(),
        MaximumSharpeOptimizer(),
        HierarchicalRiskParityOptimizer(),
        RiskParityOptimizer(),
        BlackLittermanOptimizer(),
        QAOAContinuousOptimizer(),
        HybridAnnealingOptimizer(),
    ]

    engine = BacktestEngine(
        initial_capital=100_000,
        transaction_cost_pct=0.0015,
        risk_free_rate=0.04,
        rebalance_frequency="monthly",
    )
    comparison, _ = engine.run_multiple_backtests(returns, optimizers, lookback_window=252)

    columns = [
        "optimizer_name",
        "annualized_return",
        "annualized_volatility",
        "sharpe_ratio",
        "maximum_drawdown",
        "avg_turnover",
    ]
    table = comparison[columns].sort_values("sharpe_ratio", ascending=False)

    print(f"Synthetic market: {returns.shape[1]} assets, {len(returns)} trading days")
    print("Monthly rebalancing, 252-day lookback, 15 bps transaction costs\n")
    with pd.option_context("display.float_format", "{:.4f}".format, "display.width", 120):
        print(table.to_string(index=False))


if __name__ == "__main__":
    main()
