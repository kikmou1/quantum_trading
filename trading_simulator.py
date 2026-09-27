#!/usr/bin/env python3
"""
Point-in-Time Trading Simulator
Simulates day trading with realistic constraints.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
import yaml

from data_collection.fetchers import DataFetcher
from trading_simulator.signal_generator import HybridSignalGenerator, SignalType
from trading_simulator.virtual_portfolio import VirtualPortfolio

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PointInTimeTradingSimulator:
    """
    Simulates trading on a specific day using only past data.
    """

    def __init__(
        self,
        tickers: List[str],
        initial_capital: float = 100000.0,
        lookback_days: int = 60,
        max_position_pct: float = 0.1
    ):
        """
        Initialize simulator.

        Args:
            tickers: List of tickers to trade
            initial_capital: Starting capital
            lookback_days: Days of history to use for signal generation
            max_position_pct: Max % of portfolio per position
        """
        self.tickers = tickers
        self.initial_capital = initial_capital
        self.lookback_days = lookback_days
        self.max_position_pct = max_position_pct

        self.data_fetcher = DataFetcher()
        self.signal_generator = HybridSignalGenerator()
        self.portfolio = VirtualPortfolio(initial_capital, max_position_pct)

        self.historical_data: Dict[str, pd.DataFrame] = {}
        self.simulation_results = []

    def load_data(self, start_date: str, end_date: str):
        """
        Load historical data for all tickers.
        """
        logger.info(f"Loading data for {len(self.tickers)} tickers from {start_date} to {end_date}")

        for ticker in self.tickers:
            try:
                # The signal generators need full daily bars, not just closes
                bars = self.data_fetcher.get_ohlcv(ticker, start_date, end_date)

                if len(bars) > 0:
                    self.historical_data[ticker] = bars
                    logger.info(f"  ✓ {ticker}: {len(bars)} days")
                else:
                    logger.warning(f"  ✗ {ticker}: No data available")

            except Exception as e:
                logger.error(f"  ✗ {ticker}: Error loading data - {e}")

        logger.info(f"Successfully loaded data for {len(self.historical_data)} tickers")

    def simulate_trading_day(
        self,
        trading_date: pd.Timestamp,
        forecast_next_n_days: int = 5
    ) -> Dict:
        """
        Simulate trading on a specific day.

        Steps:
        1. Use data BEFORE trading_date to generate signals
        2. Open positions at the last close before trading_date
        3. Exit open positions whose stop or target is crossed by
           trading_date's close
        4. Score the predictions against the next few days (reporting only)

        Args:
            trading_date: The day to simulate trading
            forecast_next_n_days: How many days ahead to forecast

        Returns:
            Dictionary with simulation results
        """
        logger.info("\n" + "="*80)
        logger.info(f"SIMULATING TRADING DAY: {trading_date.strftime('%Y-%m-%d')}")
        logger.info("="*80)

        results = {
            'trading_date': trading_date,
            'signals_generated': [],
            'trades_executed': [],
            'positions_opened': 0,
            'positions_closed': 0,
            'daily_pnl': 0,
            'portfolio_value_start': self.portfolio.total_equity(),
            'portfolio_value_end': 0,
            'predictions': {},
            'actual_outcomes': {}
        }

        # Step 1: Get data BEFORE trading date (point-in-time correctness)
        logger.info(f"\nStep 1: Gathering historical data (using only data BEFORE {trading_date.date()})")

        for ticker in self.tickers:
            if ticker not in self.historical_data:
                continue

            # Get data BEFORE trading date
            ticker_data = self.historical_data[ticker]
            historical_data = ticker_data[ticker_data.index < trading_date]

            if len(historical_data) < self.lookback_days:
                logger.warning(f"  {ticker}: Insufficient history ({len(historical_data)} days < {self.lookback_days})")
                continue

            # Use recent lookback period
            recent_data = historical_data.tail(self.lookback_days)

            logger.info(f"  {ticker}: Using {len(recent_data)} days of history (latest: {recent_data.index[-1].date()})")

            # Step 2: Generate signals
            capital_per_trade = self.portfolio.available_capital_per_trade()
            signals = self.signal_generator.generate_all_signals(
                recent_data,
                ticker,
                trading_date,
                capital_per_trade
            )

            if signals:
                best_signal = self.signal_generator.select_best_signal(signals)
                results['signals_generated'].append(best_signal.to_dict())

                # Step 3: Execute trade (open position)
                if self.portfolio.can_open_position(best_signal):
                    success = self.portfolio.open_position(best_signal, trading_date)
                    if success:
                        results['positions_opened'] += 1
                        results['trades_executed'].append({
                            'ticker': best_signal.ticker,
                            'action': 'OPEN',
                            'signal': best_signal.to_dict()
                        })

                        # Step 4: Make predictions for next N days
                        predictions = self._make_predictions(
                            ticker,
                            recent_data,
                            best_signal,
                            forecast_next_n_days
                        )
                        results['predictions'][ticker] = predictions

        # Step 5: Mark open positions to today's close and exit any that hit
        # their stop or target. Later days are handled when the simulation
        # reaches them, so no future price ever changes the portfolio early.
        current_prices = {}
        for ticker in self.portfolio.positions.keys():
            ticker_data = self.historical_data.get(ticker)
            if ticker_data is not None and trading_date in ticker_data.index:
                current_prices[ticker] = ticker_data.loc[trading_date, 'Close']

        if current_prices:
            self.portfolio.update_positions(current_prices, trading_date)
        self.portfolio.record_equity_snapshot(trading_date)

        # Step 6: Score the predictions against the following days. This is
        # reporting only and does not affect the portfolio.
        logger.info(f"\nStep 6: Comparing predictions vs actual outcomes...")

        for ticker, predictions in results['predictions'].items():
            if ticker not in self.historical_data:
                continue

            ticker_data = self.historical_data[ticker]
            future_data = ticker_data[
                (ticker_data.index > trading_date) &
                (ticker_data.index <= trading_date + pd.Timedelta(days=forecast_next_n_days))
            ]

            if len(future_data) > 0:
                actual_prices = future_data['Close'].tolist()
                actual_high = future_data['High'].max()
                actual_low = future_data['Low'].min()
                actual_return = ((future_data['Close'].iloc[-1] - predictions['current_price']) /
                               predictions['current_price']) * 100

                results['actual_outcomes'][ticker] = {
                    'actual_prices': actual_prices,
                    'actual_high': actual_high,
                    'actual_low': actual_low,
                    'actual_return_pct': actual_return,
                    'predicted_direction': predictions['predicted_direction'],
                    'predicted_target': predictions['target_price'],
                    'hit_take_profit': actual_high >= predictions['target_price'] if predictions['predicted_direction'] == 'UP' else actual_low <= predictions['target_price'],
                    'hit_stop_loss': actual_low <= predictions['stop_loss'] if predictions['predicted_direction'] == 'UP' else actual_high >= predictions['stop_loss']
                }

                # Print comparison
                direction_correct = (
                    (predictions['predicted_direction'] == 'UP' and actual_return > 0) or
                    (predictions['predicted_direction'] == 'DOWN' and actual_return < 0)
                )

                verdict = "correct" if direction_correct else "wrong"
                logger.info(f"\n{ticker} (direction {verdict}):")
                logger.info(f"  Predicted: {predictions['predicted_direction']} to ${predictions['target_price']:.2f}")
                logger.info(f"  Actual: ${actual_prices[-1]:.2f} ({actual_return:+.2f}%)")
                logger.info(f"  High: ${actual_high:.2f}, Low: ${actual_low:.2f}")
                logger.info(f"  Take Profit Hit: {results['actual_outcomes'][ticker]['hit_take_profit']}")
                logger.info(f"  Stop Loss Hit: {results['actual_outcomes'][ticker]['hit_stop_loss']}")

        # Final summary
        results['portfolio_value_end'] = self.portfolio.total_equity()
        results['daily_pnl'] = results['portfolio_value_end'] - results['portfolio_value_start']
        results['positions_closed'] = len([t for t in self.portfolio.trades
                                          if t.exit_date == trading_date])

        logger.info("\n" + "="*80)
        logger.info("DAY SUMMARY")
        logger.info("="*80)
        logger.info(f"Signals Generated: {len(results['signals_generated'])}")
        logger.info(f"Positions Opened: {results['positions_opened']}")
        logger.info(f"Positions Closed: {results['positions_closed']}")
        logger.info(f"Portfolio Value: ${results['portfolio_value_start']:,.2f} → ${results['portfolio_value_end']:,.2f}")
        logger.info(f"Daily P&L: ${results['daily_pnl']:+,.2f}")
        logger.info("="*80)

        self.simulation_results.append(results)
        return results

    def _make_predictions(
        self,
        ticker: str,
        historical_data: pd.DataFrame,
        signal,
        forecast_days: int
    ) -> Dict:
        """
        Make predictions for the next N days based on the signal.
        """
        current_price = historical_data['Close'].iloc[-1]

        predictions = {
            'ticker': ticker,
            'current_price': current_price,
            'predicted_direction': 'UP' if signal.signal_type == SignalType.LONG else 'DOWN',
            'target_price': signal.take_profit,
            'stop_loss': signal.stop_loss,
            'confidence': signal.confidence,
            'strategy': signal.strategy_name,
            'reasoning': signal.reasoning,
            'forecast_days': forecast_days
        }

        return predictions

    def run_multi_day_simulation(
        self,
        start_date: str,
        end_date: str,
        forecast_days: int = 5
    ):
        """
        Run simulation across multiple trading days.
        """
        logger.info("\n" + "="*80)
        logger.info("MULTI-DAY TRADING SIMULATION")
        logger.info("="*80)
        logger.info(f"Period: {start_date} to {end_date}")
        logger.info(f"Tickers: {', '.join(self.tickers)}")
        logger.info(f"Initial Capital: ${self.initial_capital:,.2f}")
        logger.info(f"Forecast Horizon: {forecast_days} days")
        logger.info("="*80)

        # Load data (with buffer for lookback)
        data_start = (pd.Timestamp(start_date) - pd.Timedelta(days=self.lookback_days * 2)).strftime('%Y-%m-%d')
        # Load a few days past the end so the last predictions can be scored
        data_end = (pd.Timestamp(end_date) + pd.Timedelta(days=forecast_days * 2)).strftime('%Y-%m-%d')
        self.load_data(data_start, data_end)

        if not self.historical_data:
            logger.error("No data loaded. Exiting.")
            return

        # Get trading dates
        sample_ticker = list(self.historical_data.keys())[0]
        all_dates = self.historical_data[sample_ticker].index
        trading_dates = all_dates[
            (all_dates >= pd.Timestamp(start_date)) &
            (all_dates <= pd.Timestamp(end_date))
        ]

        logger.info(f"\nFound {len(trading_dates)} trading days")

        # Simulate each day
        for i, trading_date in enumerate(trading_dates, 1):
            logger.info(f"\n{'='*80}")
            logger.info(f"Day {i}/{len(trading_dates)}")

            self.simulate_trading_day(trading_date, forecast_days)

            # Print portfolio status
            if i % 5 == 0:  # Every 5 days
                self.portfolio.print_summary()

        # Final summary
        logger.info("\n" + "="*80)
        logger.info("SIMULATION COMPLETE")
        logger.info("="*80)

        self.portfolio.print_summary()

        # Performance metrics
        self.print_performance_analysis()

    def print_performance_analysis(self):
        """Print detailed performance analysis."""
        print("\n" + "="*80)
        print("PREDICTION ACCURACY ANALYSIS")
        print("="*80)

        total_predictions = 0
        correct_directions = 0
        tp_hits = 0
        sl_hits = 0

        for result in self.simulation_results:
            for ticker, outcome in result['actual_outcomes'].items():
                total_predictions += 1

                # Check direction accuracy
                predicted_dir = outcome['predicted_direction']
                actual_return = outcome['actual_return_pct']

                if (predicted_dir == 'UP' and actual_return > 0) or \
                   (predicted_dir == 'DOWN' and actual_return < 0):
                    correct_directions += 1

                if outcome['hit_take_profit']:
                    tp_hits += 1

                if outcome['hit_stop_loss']:
                    sl_hits += 1

        if total_predictions > 0:
            print(f"\nTotal Predictions: {total_predictions}")
            print(f"Direction Accuracy: {correct_directions}/{total_predictions} ({correct_directions/total_predictions*100:.1f}%)")
            print(f"Take Profit Hit Rate: {tp_hits}/{total_predictions} ({tp_hits/total_predictions*100:.1f}%)")
            print(f"Stop Loss Hit Rate: {sl_hits}/{total_predictions} ({sl_hits/total_predictions*100:.1f}%)")

        print("="*80)


def main():
    """Main execution."""

    # Configuration
    config = {
        'tickers': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'NFLX'],
        'initial_capital': 100000,
        'start_date': '2024-01-01',
        'end_date': '2024-03-31',
        'lookback_days': 60,
        'forecast_days': 5,
        'max_position_pct': 0.15  # Max 15% per position
    }

    # Create simulator
    simulator = PointInTimeTradingSimulator(
        tickers=config['tickers'],
        initial_capital=config['initial_capital'],
        lookback_days=config['lookback_days'],
        max_position_pct=config['max_position_pct']
    )

    # Run simulation
    simulator.run_multi_day_simulation(
        start_date=config['start_date'],
        end_date=config['end_date'],
        forecast_days=config['forecast_days']
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSimulation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
