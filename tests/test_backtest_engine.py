import numpy as np
import pandas as pd
import pytest

from backtesting.engine import BacktestEngine
from optimizers.classical.portfolio_optimizers import EqualWeightOptimizer


class RecordingOptimizer(EqualWeightOptimizer):
    """Equal weight optimizer that records the data it was given."""

    def __init__(self):
        super().__init__()
        self.calls = []

    def optimize(self, returns, **kwargs):
        self.calls.append(returns.index.copy())
        return super().optimize(returns, **kwargs)


def test_no_look_ahead(returns):
    engine = BacktestEngine(rebalance_frequency="monthly")
    optimizer = RecordingOptimizer()
    result = engine.run_backtest(returns, optimizer, lookback_window=60)

    rebalance_dates = [w["date"] for w in result["weights_over_time"]]
    assert len(optimizer.calls) == len(rebalance_dates) > 0
    for train_index, date in zip(optimizer.calls, rebalance_dates):
        assert train_index.max() < date
        assert len(train_index) == 60


def test_constant_returns_without_costs_compound_exactly():
    dates = pd.bdate_range("2021-01-01", periods=100)
    returns = pd.DataFrame(0.001, index=dates, columns=["X", "Y"])
    engine = BacktestEngine(initial_capital=1000, transaction_cost_pct=0.0)
    result = engine.run_backtest(returns, EqualWeightOptimizer(), lookback_window=10)

    first_trade = next(i for i, d in enumerate(dates) if i >= 10 and d.month != dates[i - 1].month)
    n_invested_days = len(dates) - first_trade
    assert result["final_value"] == pytest.approx(1000 * 1.001 ** n_invested_days)


def test_transaction_costs_reduce_final_value(returns):
    class Alternating(EqualWeightOptimizer):
        flip = False

        def optimize(self, r, **kwargs):
            self.flip = not self.flip
            w = pd.Series(0.0, index=r.columns)
            w.iloc[0 if self.flip else 1] = 1.0
            return w

    free = BacktestEngine(transaction_cost_pct=0.0).run_backtest(returns, Alternating(), lookback_window=60)
    costly = BacktestEngine(transaction_cost_pct=0.01).run_backtest(returns, Alternating(), lookback_window=60)
    assert costly["final_value"] < free["final_value"]
    assert costly["avg_turnover"] > 0


@pytest.mark.parametrize("frequency,expected", [("monthly", 3), ("quarterly", 1)])
def test_rebalance_dates(frequency, expected):
    dates = pd.bdate_range("2021-01-01", "2021-03-31")
    engine = BacktestEngine(rebalance_frequency=frequency)
    assert len(engine._get_rebalance_dates(dates)) == expected


def test_turnover_is_one_way():
    engine = BacktestEngine()
    old = pd.Series({"A": 1.0, "B": 0.0})
    new = pd.Series({"A": 0.0, "B": 1.0})
    assert engine._calculate_turnover(old, new) == pytest.approx(1.0)


def test_unknown_frequency_raises():
    with pytest.raises(ValueError):
        BacktestEngine(rebalance_frequency="hourly")._get_rebalance_dates(pd.bdate_range("2021-01-01", periods=5))
