"""
Virtual Portfolio - Tracks trades, positions, and P&L.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging

from .signal_generator import TradeSignal, SignalType

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """Represents an open position."""
    ticker: str
    entry_price: float
    current_price: float
    quantity: int
    side: str  # 'LONG' or 'SHORT'
    entry_date: pd.Timestamp
    stop_loss: float
    take_profit: float
    strategy_name: str

    def unrealized_pnl(self) -> float:
        """Calculate unrealized P&L."""
        if self.side == 'LONG':
            return (self.current_price - self.entry_price) * self.quantity
        else:  # SHORT
            return (self.entry_price - self.current_price) * self.quantity

    def unrealized_pnl_pct(self) -> float:
        """Calculate unrealized P&L percentage."""
        if self.side == 'LONG':
            return ((self.current_price - self.entry_price) / self.entry_price) * 100
        else:
            return ((self.entry_price - self.current_price) / self.entry_price) * 100

    def position_value(self) -> float:
        """Current market value of position."""
        return self.current_price * self.quantity


@dataclass
class Trade:
    """Represents a completed trade."""
    ticker: str
    side: str
    entry_price: float
    exit_price: float
    quantity: int
    entry_date: pd.Timestamp
    exit_date: pd.Timestamp
    pnl: float
    pnl_pct: float
    exit_reason: str  # 'STOP_LOSS', 'TAKE_PROFIT', 'MANUAL'
    strategy_name: str
    holding_period_days: int


class VirtualPortfolio:
    """
    Manages virtual trading portfolio.
    """

    def __init__(self, initial_capital: float = 100000.0, max_position_pct: float = 0.1):
        """
        Initialize portfolio.

        Args:
            initial_capital: Starting cash
            max_position_pct: Maximum % of portfolio per position (default 10%)
        """
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.max_position_pct = max_position_pct

        self.positions: Dict[str, Position] = {}  # ticker -> Position
        self.trades: List[Trade] = []
        self.equity_curve: List[Dict] = []

    def total_equity(self) -> float:
        """Total portfolio value (cash + positions)."""
        positions_value = sum(pos.position_value() for pos in self.positions.values())
        return self.cash + positions_value

    def available_capital_per_trade(self) -> float:
        """Available capital for next trade based on risk limits."""
        total_equity = self.total_equity()
        return total_equity * self.max_position_pct

    def can_open_position(self, signal: TradeSignal) -> bool:
        """Check if we can open this position."""
        # Check if already have position in this ticker
        if signal.ticker in self.positions:
            logger.warning(f"Already have position in {signal.ticker}")
            return False

        # Check if we have enough cash
        required_capital = signal.entry_price * signal.position_size
        if required_capital > self.cash:
            logger.warning(f"Insufficient cash: need ${required_capital:.2f}, have ${self.cash:.2f}")
            return False

        # Check position size limit
        max_position_value = self.total_equity() * self.max_position_pct
        if required_capital > max_position_value:
            logger.warning(f"Position too large: ${required_capital:.2f} > ${max_position_value:.2f}")
            return False

        return True

    def open_position(self, signal: TradeSignal, current_date: pd.Timestamp) -> bool:
        """
        Open a new position based on signal.
        """
        if not self.can_open_position(signal):
            return False

        # Create position
        position = Position(
            ticker=signal.ticker,
            entry_price=signal.entry_price,
            current_price=signal.entry_price,
            quantity=signal.position_size,
            side=signal.signal_type.value,
            entry_date=current_date,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit,
            strategy_name=signal.strategy_name
        )

        # Deduct cash
        cost = signal.entry_price * signal.position_size
        self.cash -= cost

        # Add to positions
        self.positions[signal.ticker] = position

        logger.info(f"📈 OPENED {signal.signal_type.value} position in {signal.ticker}")
        logger.info(f"   Entry: ${signal.entry_price:.2f} x {signal.position_size} shares = ${cost:.2f}")
        logger.info(f"   Stop Loss: ${signal.stop_loss:.2f}, Take Profit: ${signal.take_profit:.2f}")
        logger.info(f"   Cash remaining: ${self.cash:.2f}")

        return True

    def update_positions(self, current_prices: Dict[str, float], current_date: pd.Timestamp):
        """
        Update all positions with current prices and check for exits.
        """
        positions_to_close = []

        for ticker, position in self.positions.items():
            if ticker not in current_prices:
                continue

            current_price = current_prices[ticker]
            position.current_price = current_price

            # Check stop loss
            if position.side == 'LONG' and current_price <= position.stop_loss:
                positions_to_close.append((ticker, 'STOP_LOSS', current_price))

            elif position.side == 'SHORT' and current_price >= position.stop_loss:
                positions_to_close.append((ticker, 'STOP_LOSS', current_price))

            # Check take profit
            elif position.side == 'LONG' and current_price >= position.take_profit:
                positions_to_close.append((ticker, 'TAKE_PROFIT', current_price))

            elif position.side == 'SHORT' and current_price <= position.take_profit:
                positions_to_close.append((ticker, 'TAKE_PROFIT', current_price))

        # Close positions that hit stops or targets
        for ticker, reason, exit_price in positions_to_close:
            self.close_position(ticker, exit_price, current_date, reason)

    def close_position(
        self,
        ticker: str,
        exit_price: float,
        exit_date: pd.Timestamp,
        reason: str = 'MANUAL'
    ) -> Optional[Trade]:
        """
        Close a position and record trade.
        """
        if ticker not in self.positions:
            logger.warning(f"No position to close in {ticker}")
            return None

        position = self.positions[ticker]

        # Calculate P&L
        if position.side == 'LONG':
            pnl = (exit_price - position.entry_price) * position.quantity
            pnl_pct = ((exit_price - position.entry_price) / position.entry_price) * 100
        else:  # SHORT
            pnl = (position.entry_price - exit_price) * position.quantity
            pnl_pct = ((position.entry_price - exit_price) / position.entry_price) * 100

        # Add cash back
        proceeds = exit_price * position.quantity
        self.cash += proceeds

        # Create trade record
        holding_days = (exit_date - position.entry_date).days
        trade = Trade(
            ticker=ticker,
            side=position.side,
            entry_price=position.entry_price,
            exit_price=exit_price,
            quantity=position.quantity,
            entry_date=position.entry_date,
            exit_date=exit_date,
            pnl=pnl,
            pnl_pct=pnl_pct,
            exit_reason=reason,
            strategy_name=position.strategy_name,
            holding_period_days=holding_days
        )

        self.trades.append(trade)

        # Log the trade
        emoji = "✅" if pnl > 0 else "❌"
        logger.info(f"{emoji} CLOSED {position.side} position in {ticker} - {reason}")
        logger.info(f"   Entry: ${position.entry_price:.2f}, Exit: ${exit_price:.2f}")
        logger.info(f"   P&L: ${pnl:+.2f} ({pnl_pct:+.2f}%), Holding: {holding_days} days")

        # Remove from positions
        del self.positions[ticker]

        return trade

    def record_equity_snapshot(self, date: pd.Timestamp):
        """Record current portfolio state."""
        snapshot = {
            'date': date,
            'cash': self.cash,
            'positions_value': sum(pos.position_value() for pos in self.positions.values()),
            'total_equity': self.total_equity(),
            'num_positions': len(self.positions),
            'return_pct': ((self.total_equity() - self.initial_capital) / self.initial_capital) * 100
        }
        self.equity_curve.append(snapshot)

    def get_performance_summary(self) -> Dict:
        """Calculate performance metrics."""
        if not self.trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'total_pnl': 0,
                'total_return_pct': 0
            }

        trades_df = pd.DataFrame([{
            'pnl': t.pnl,
            'pnl_pct': t.pnl_pct,
            'exit_reason': t.exit_reason
        } for t in self.trades])

        winning_trades = trades_df[trades_df['pnl'] > 0]
        losing_trades = trades_df[trades_df['pnl'] < 0]

        return {
            'total_trades': len(self.trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': len(winning_trades) / len(self.trades) * 100 if len(self.trades) > 0 else 0,
            'avg_win': winning_trades['pnl'].mean() if len(winning_trades) > 0 else 0,
            'avg_loss': losing_trades['pnl'].mean() if len(losing_trades) > 0 else 0,
            'largest_win': winning_trades['pnl'].max() if len(winning_trades) > 0 else 0,
            'largest_loss': losing_trades['pnl'].min() if len(losing_trades) > 0 else 0,
            'total_pnl': trades_df['pnl'].sum(),
            'total_return_pct': ((self.total_equity() - self.initial_capital) / self.initial_capital) * 100,
            'stop_losses_hit': len(trades_df[trades_df['exit_reason'] == 'STOP_LOSS']),
            'take_profits_hit': len(trades_df[trades_df['exit_reason'] == 'TAKE_PROFIT'])
        }

    def print_summary(self):
        """Print portfolio summary."""
        print("\n" + "="*70)
        print("📊 PORTFOLIO SUMMARY")
        print("="*70)

        print(f"\n💰 Capital:")
        print(f"   Initial: ${self.initial_capital:,.2f}")
        print(f"   Current Equity: ${self.total_equity():,.2f}")
        print(f"   Cash: ${self.cash:,.2f}")
        print(f"   Positions Value: ${sum(pos.position_value() for pos in self.positions.values()):,.2f}")
        print(f"   Return: {((self.total_equity() - self.initial_capital) / self.initial_capital) * 100:+.2f}%")

        if self.positions:
            print(f"\n📈 Open Positions ({len(self.positions)}):")
            for ticker, pos in self.positions.items():
                pnl_emoji = "🟢" if pos.unrealized_pnl() > 0 else "🔴"
                print(f"   {pnl_emoji} {ticker}: {pos.side} {pos.quantity} @ ${pos.entry_price:.2f}")
                print(f"      Current: ${pos.current_price:.2f}, P&L: ${pos.unrealized_pnl():+.2f} ({pos.unrealized_pnl_pct():+.2f}%)")

        if self.trades:
            perf = self.get_performance_summary()
            print(f"\n📉 Trading Performance:")
            print(f"   Total Trades: {perf['total_trades']}")
            print(f"   Win Rate: {perf['win_rate']:.1f}% ({perf['winning_trades']}W / {perf['losing_trades']}L)")
            print(f"   Avg Win: ${perf['avg_win']:,.2f}")
            print(f"   Avg Loss: ${perf['avg_loss']:,.2f}")
            print(f"   Largest Win: ${perf['largest_win']:,.2f}")
            print(f"   Largest Loss: ${perf['largest_loss']:,.2f}")
            print(f"   Stop Losses Hit: {perf['stop_losses_hit']}")
            print(f"   Take Profits Hit: {perf['take_profits_hit']}")

        print("="*70)


if __name__ == "__main__":
    # Test portfolio
    logging.basicConfig(level=logging.INFO)

    from .signal_generator import TradeSignal, SignalType

    portfolio = VirtualPortfolio(initial_capital=100000)

    # Create test signal
    signal = TradeSignal(
        ticker='AAPL',
        signal_type=SignalType.LONG,
        entry_price=150.0,
        stop_loss=145.0,
        take_profit=160.0,
        position_size=100,
        confidence=0.8,
        timestamp=pd.Timestamp('2024-01-01'),
        strategy_name='Test',
        reasoning='Test trade'
    )

    # Open position
    portfolio.open_position(signal, pd.Timestamp('2024-01-01'))

    # Simulate price movement
    portfolio.update_positions({'AAPL': 155.0}, pd.Timestamp('2024-01-02'))
    portfolio.record_equity_snapshot(pd.Timestamp('2024-01-02'))

    # Hit take profit
    portfolio.update_positions({'AAPL': 160.0}, pd.Timestamp('2024-01-03'))
    portfolio.record_equity_snapshot(pd.Timestamp('2024-01-03'))

    portfolio.print_summary()
