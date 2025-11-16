"""
Trading Signal Generator - Creates specific trade signals with entry, SL, TP.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


def _to_scalar(value):
    """Convert pandas Series or other types to scalar value."""
    if isinstance(value, pd.Series):
        return float(value.values[0])
    return float(value)


class SignalType(Enum):
    """Trade signal types."""
    LONG = "LONG"
    SHORT = "SHORT"
    HOLD = "HOLD"
    EXIT = "EXIT"


@dataclass
class TradeSignal:
    """
    Represents a specific trade signal.
    """
    ticker: str
    signal_type: SignalType
    entry_price: float
    stop_loss: float
    take_profit: float
    position_size: float  # Number of shares
    confidence: float  # 0-1 confidence score
    timestamp: pd.Timestamp
    strategy_name: str
    reasoning: str  # Why this trade?

    def to_dict(self) -> Dict:
        """Convert to dictionary for logging."""
        return {
            'ticker': self.ticker,
            'signal': self.signal_type.value,
            'entry': self.entry_price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'size': self.position_size,
            'confidence': self.confidence,
            'timestamp': self.timestamp,
            'strategy': self.strategy_name,
            'reasoning': self.reasoning
        }

    def risk_reward_ratio(self) -> float:
        """Calculate risk/reward ratio."""
        if self.signal_type == SignalType.LONG:
            risk = self.entry_price - self.stop_loss
            reward = self.take_profit - self.entry_price
        else:  # SHORT
            risk = self.stop_loss - self.entry_price
            reward = self.entry_price - self.take_profit

        if risk > 0:
            return reward / risk
        return 0.0


class TechnicalSignalGenerator:
    """
    Generate signals based on technical indicators.
    """

    def __init__(self, atr_period: int = 14):
        self.atr_period = atr_period

    def calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
        """Calculate Average True Range for stop loss placement."""
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=self.atr_period).mean()
        return atr

    def rsi_signal(
        self,
        data: pd.DataFrame,
        ticker: str,
        current_date: pd.Timestamp,
        capital_per_trade: float
    ) -> Optional[TradeSignal]:
        """
        RSI-based signals.

        Long: RSI < 30 (oversold)
        Short: RSI > 70 (overbought)
        """
        # Calculate RSI
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        current_rsi = _to_scalar(rsi.iloc[-1])
        current_price = _to_scalar(data['Close'].iloc[-1])

        # Calculate ATR for stop loss
        atr = _to_scalar(self.calculate_atr(data['High'], data['Low'], data['Close']).iloc[-1])

        # Generate signal
        if current_rsi < 30:  # Oversold - Long signal
            entry_price = current_price
            stop_loss = current_price - (2 * atr)  # 2 ATR stop
            take_profit = current_price + (4 * atr)  # 4 ATR target (2:1 R/R)
            position_size = int(capital_per_trade / current_price)

            return TradeSignal(
                ticker=ticker,
                signal_type=SignalType.LONG,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                position_size=position_size,
                confidence=0.7,
                timestamp=current_date,
                strategy_name="RSI_Reversal",
                reasoning=f"RSI oversold at {current_rsi:.1f}, mean reversion expected"
            )

        elif current_rsi > 70:  # Overbought - Short signal
            entry_price = current_price
            stop_loss = current_price + (2 * atr)
            take_profit = current_price - (4 * atr)
            position_size = int(capital_per_trade / current_price)

            return TradeSignal(
                ticker=ticker,
                signal_type=SignalType.SHORT,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                position_size=position_size,
                confidence=0.7,
                timestamp=current_date,
                strategy_name="RSI_Reversal",
                reasoning=f"RSI overbought at {current_rsi:.1f}, reversal expected"
            )

        return None

    def macd_signal(
        self,
        data: pd.DataFrame,
        ticker: str,
        current_date: pd.Timestamp,
        capital_per_trade: float
    ) -> Optional[TradeSignal]:
        """
        MACD crossover signals.
        """
        # Calculate MACD
        exp1 = data['Close'].ewm(span=12, adjust=False).mean()
        exp2 = data['Close'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()

        current_price = _to_scalar(data['Close'].iloc[-1])
        atr = _to_scalar(self.calculate_atr(data['High'], data['Low'], data['Close']).iloc[-1])

        # Check for crossover
        if len(macd) < 2:
            return None

        macd_prev = _to_scalar(macd.iloc[-2])
        macd_curr = _to_scalar(macd.iloc[-1])
        signal_prev = _to_scalar(signal.iloc[-2])
        signal_curr = _to_scalar(signal.iloc[-1])

        macd_cross_above = macd_prev < signal_prev and macd_curr > signal_curr
        macd_cross_below = macd_prev > signal_prev and macd_curr < signal_curr

        if macd_cross_above:  # Bullish crossover
            entry_price = current_price
            stop_loss = current_price - (1.5 * atr)
            take_profit = current_price + (3 * atr)
            position_size = int(capital_per_trade / current_price)

            return TradeSignal(
                ticker=ticker,
                signal_type=SignalType.LONG,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                position_size=position_size,
                confidence=0.75,
                timestamp=current_date,
                strategy_name="MACD_Crossover",
                reasoning="MACD bullish crossover, upward momentum"
            )

        elif macd_cross_below:  # Bearish crossover
            entry_price = current_price
            stop_loss = current_price + (1.5 * atr)
            take_profit = current_price - (3 * atr)
            position_size = int(capital_per_trade / current_price)

            return TradeSignal(
                ticker=ticker,
                signal_type=SignalType.SHORT,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                position_size=position_size,
                confidence=0.75,
                timestamp=current_date,
                strategy_name="MACD_Crossover",
                reasoning="MACD bearish crossover, downward momentum"
            )

        return None

    def bollinger_band_signal(
        self,
        data: pd.DataFrame,
        ticker: str,
        current_date: pd.Timestamp,
        capital_per_trade: float
    ) -> Optional[TradeSignal]:
        """
        Bollinger Band mean reversion signals.
        """
        # Calculate Bollinger Bands
        sma = data['Close'].rolling(window=20).mean()
        std = data['Close'].rolling(window=20).std()
        upper_band = sma + (2 * std)
        lower_band = sma - (2 * std)

        current_price = _to_scalar(data['Close'].iloc[-1])
        current_upper = _to_scalar(upper_band.iloc[-1])
        current_lower = _to_scalar(lower_band.iloc[-1])
        current_sma = _to_scalar(sma.iloc[-1])

        atr = _to_scalar(self.calculate_atr(data['High'], data['Low'], data['Close']).iloc[-1])

        # Price touching lower band - Long signal
        if current_price <= current_lower:
            entry_price = current_price
            stop_loss = current_price - (1.5 * atr)
            take_profit = current_sma  # Target mean reversion to SMA
            position_size = int(capital_per_trade / current_price)

            return TradeSignal(
                ticker=ticker,
                signal_type=SignalType.LONG,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                position_size=position_size,
                confidence=0.8,
                timestamp=current_date,
                strategy_name="Bollinger_Reversal",
                reasoning="Price at lower Bollinger Band, mean reversion expected"
            )

        # Price touching upper band - Short signal
        elif current_price >= current_upper:
            entry_price = current_price
            stop_loss = current_price + (1.5 * atr)
            take_profit = current_sma
            position_size = int(capital_per_trade / current_price)

            return TradeSignal(
                ticker=ticker,
                signal_type=SignalType.SHORT,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                position_size=position_size,
                confidence=0.8,
                timestamp=current_date,
                strategy_name="Bollinger_Reversal",
                reasoning="Price at upper Bollinger Band, mean reversion expected"
            )

        return None


class MomentumSignalGenerator:
    """
    Generate momentum-based signals.
    """

    def momentum_breakout(
        self,
        data: pd.DataFrame,
        ticker: str,
        current_date: pd.Timestamp,
        capital_per_trade: float,
        lookback: int = 20
    ) -> Optional[TradeSignal]:
        """
        Breakout of recent high/low.
        """
        current_price = _to_scalar(data['Close'].iloc[-1])
        recent_high = _to_scalar(data['High'].iloc[-lookback:-1].max())
        recent_low = _to_scalar(data['Low'].iloc[-lookback:-1].min())

        atr = _to_scalar(TechnicalSignalGenerator().calculate_atr(
            data['High'], data['Low'], data['Close']
        ).iloc[-1])

        # Breakout above recent high
        if current_price > recent_high:
            entry_price = current_price
            stop_loss = recent_high - atr  # Stop below breakout level
            take_profit = current_price + (3 * atr)
            position_size = int(capital_per_trade / current_price)

            return TradeSignal(
                ticker=ticker,
                signal_type=SignalType.LONG,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                position_size=position_size,
                confidence=0.75,
                timestamp=current_date,
                strategy_name="Momentum_Breakout",
                reasoning=f"Breakout above {lookback}-day high at ${recent_high:.2f}"
            )

        # Breakdown below recent low
        elif current_price < recent_low:
            entry_price = current_price
            stop_loss = recent_low + atr
            take_profit = current_price - (3 * atr)
            position_size = int(capital_per_trade / current_price)

            return TradeSignal(
                ticker=ticker,
                signal_type=SignalType.SHORT,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                position_size=position_size,
                confidence=0.75,
                timestamp=current_date,
                strategy_name="Momentum_Breakout",
                reasoning=f"Breakdown below {lookback}-day low at ${recent_low:.2f}"
            )

        return None


class HybridSignalGenerator:
    """
    Combines multiple signal generators and selects best signals.
    """

    def __init__(self):
        self.technical = TechnicalSignalGenerator()
        self.momentum = MomentumSignalGenerator()

    def generate_all_signals(
        self,
        data: pd.DataFrame,
        ticker: str,
        current_date: pd.Timestamp,
        capital_per_trade: float
    ) -> List[TradeSignal]:
        """
        Generate signals from all strategies.
        """
        signals = []

        # Ensure enough data
        if len(data) < 30:
            return signals

        # Technical signals
        rsi_signal = self.technical.rsi_signal(data, ticker, current_date, capital_per_trade)
        if rsi_signal:
            signals.append(rsi_signal)

        macd_signal = self.technical.macd_signal(data, ticker, current_date, capital_per_trade)
        if macd_signal:
            signals.append(macd_signal)

        bb_signal = self.technical.bollinger_band_signal(data, ticker, current_date, capital_per_trade)
        if bb_signal:
            signals.append(bb_signal)

        # Momentum signals
        momentum_signal = self.momentum.momentum_breakout(data, ticker, current_date, capital_per_trade)
        if momentum_signal:
            signals.append(momentum_signal)

        return signals

    def select_best_signal(self, signals: List[TradeSignal]) -> Optional[TradeSignal]:
        """
        Select best signal based on confidence and risk/reward.
        """
        if not signals:
            return None

        # Score each signal
        scored_signals = []
        for signal in signals:
            rr_ratio = signal.risk_reward_ratio()
            # Score = confidence * min(risk_reward, 3.0)  # Cap R/R at 3
            score = signal.confidence * min(rr_ratio, 3.0)
            scored_signals.append((score, signal))

        # Return highest scoring signal
        scored_signals.sort(key=lambda x: x[0], reverse=True)
        best_signal = scored_signals[0][1]

        logger.info(f"Selected {best_signal.strategy_name} signal with score {scored_signals[0][0]:.2f}")

        return best_signal


if __name__ == "__main__":
    # Test signal generation
    logging.basicConfig(level=logging.INFO)

    # Create sample data
    dates = pd.date_range('2024-01-01', '2024-03-01', freq='D')
    np.random.seed(42)

    data = pd.DataFrame({
        'Open': 100 + np.cumsum(np.random.randn(len(dates)) * 2),
        'High': 100 + np.cumsum(np.random.randn(len(dates)) * 2) + 1,
        'Low': 100 + np.cumsum(np.random.randn(len(dates)) * 2) - 1,
        'Close': 100 + np.cumsum(np.random.randn(len(dates)) * 2),
        'Volume': np.random.randint(1000000, 10000000, len(dates))
    }, index=dates)

    # Generate signals
    generator = HybridSignalGenerator()
    signals = generator.generate_all_signals(
        data,
        ticker='TEST',
        current_date=dates[-1],
        capital_per_trade=10000
    )

    print(f"\nGenerated {len(signals)} signals:")
    for sig in signals:
        print(f"\n{sig.strategy_name}:")
        print(f"  Direction: {sig.signal_type.value}")
        print(f"  Entry: ${sig.entry_price:.2f}")
        print(f"  Stop Loss: ${sig.stop_loss:.2f}")
        print(f"  Take Profit: ${sig.take_profit:.2f}")
        print(f"  Position Size: {sig.position_size} shares")
        print(f"  Risk/Reward: {sig.risk_reward_ratio():.2f}")
        print(f"  Reasoning: {sig.reasoning}")

    if signals:
        best = generator.select_best_signal(signals)
        print(f"\n✅ Best Signal: {best.strategy_name} ({best.signal_type.value})")
