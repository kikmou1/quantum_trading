import pandas as pd
import pytest

from trading_simulator.signal_generator import SignalType, TradeSignal
from trading_simulator.virtual_portfolio import VirtualPortfolio

DAY0 = pd.Timestamp("2024-01-02")
DAY1 = pd.Timestamp("2024-01-10")


def make_signal(side, entry=100.0, stop=95.0, target=110.0, size=50):
    return TradeSignal(
        ticker="XYZ",
        signal_type=side,
        entry_price=entry,
        stop_loss=stop,
        take_profit=target,
        position_size=size,
        confidence=0.7,
        timestamp=DAY0,
        strategy_name="test",
        reasoning="test",
    )


def test_long_take_profit_realizes_gain():
    pf = VirtualPortfolio(initial_capital=100_000, max_position_pct=0.1)
    assert pf.open_position(make_signal(SignalType.LONG), DAY0)
    assert pf.cash == pytest.approx(95_000)

    pf.update_positions({"XYZ": 111.0}, DAY1)
    assert not pf.positions
    assert pf.trades[0].exit_reason == "TAKE_PROFIT"
    assert pf.trades[0].pnl == pytest.approx(550)
    assert pf.total_equity() == pytest.approx(100_550)


def test_long_stop_loss_realizes_loss():
    pf = VirtualPortfolio(initial_capital=100_000)
    pf.open_position(make_signal(SignalType.LONG), DAY0)
    pf.update_positions({"XYZ": 94.0}, DAY1)
    assert pf.trades[0].exit_reason == "STOP_LOSS"
    assert pf.total_equity() == pytest.approx(100_000 - 300)


def test_profitable_short_increases_equity():
    pf = VirtualPortfolio(initial_capital=100_000)
    pf.open_position(make_signal(SignalType.SHORT, entry=100, stop=105, target=90), DAY0)

    pf.update_positions({"XYZ": 95.0}, DAY1)
    assert pf.positions["XYZ"].unrealized_pnl() == pytest.approx(250)
    assert pf.total_equity() == pytest.approx(100_250)

    pf.update_positions({"XYZ": 89.0}, DAY1)
    assert pf.trades[0].exit_reason == "TAKE_PROFIT"
    assert pf.trades[0].pnl == pytest.approx(550)
    assert pf.cash == pytest.approx(100_550)


def test_losing_short_decreases_equity():
    pf = VirtualPortfolio(initial_capital=100_000)
    pf.open_position(make_signal(SignalType.SHORT, entry=100, stop=105, target=90), DAY0)
    pf.update_positions({"XYZ": 106.0}, DAY1)
    assert pf.trades[0].exit_reason == "STOP_LOSS"
    assert pf.cash == pytest.approx(100_000 - 300)


def test_position_size_limit_is_enforced():
    pf = VirtualPortfolio(initial_capital=10_000, max_position_pct=0.1)
    assert not pf.open_position(make_signal(SignalType.LONG, size=50), DAY0)
    assert pf.cash == 10_000


def test_duplicate_position_rejected():
    pf = VirtualPortfolio(initial_capital=100_000)
    assert pf.open_position(make_signal(SignalType.LONG), DAY0)
    assert not pf.open_position(make_signal(SignalType.LONG), DAY0)
