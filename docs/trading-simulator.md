# Trading Simulator

`trading_simulator.py` replays a period day by day. On each day it generates
trade signals from past data only, opens positions in a virtual portfolio,
exits them when a stop or target is crossed, and scores each signal's
prediction against what happened next.

```bash
python trading_simulator.py
```

The default run trades AAPL, MSFT, GOOGL, AMZN, NVDA, TSLA, META and NFLX from
2024-01-01 to 2024-03-31 with $100,000 and at most 15% of equity per position.
To change this, edit the `config` dict in `main()`.

## How a simulated day works

For each trading day `D`:

1. **Signals.** For every ticker, the last `lookback_days` (default 60) of
   daily bars *before* `D` go to the signal generators. Each strategy may
   produce one signal; the one with the highest
   `confidence × min(reward/risk, 3)` is kept.
2. **Entry.** If there is enough cash, no position in that ticker yet, and
   the position is within the size limit, a position is opened at the last
   close before `D`. The share count is `floor(capital_per_trade / price)`.
3. **Exits.** Every open position is checked against `D`'s close. A long is
   closed if the close is at or below its stop, or at or above its target;
   shorts are the mirror image. The stop is checked first. The exit price is
   that close, so a gap through a level exits beyond it.
4. **Scoring.** Separately, the day's prediction (direction, target, stop) is
   compared with the next `forecast_days` calendar days of prices. This only
   feeds the "Prediction accuracy" report; it never changes the portfolio.

## Strategies

All stops and targets use a 14-day Average True Range (ATR).

| Strategy | Long when | Short when | Stop | Target | Confidence |
|----------|-----------|------------|------|--------|------------|
| RSI reversal | RSI(14) < 30 | RSI(14) > 70 | 2 ATR | 4 ATR | 0.70 |
| MACD crossover | MACD crosses above signal | MACD crosses below signal | 1.5 ATR | 3 ATR | 0.75 |
| Bollinger reversal | Close ≤ lower band (20, 2σ) | Close ≥ upper band | 1.5 ATR | 20-day SMA | 0.80 |
| Momentum breakout | Close > prior 20-day high | Close < prior 20-day low | 1 ATR beyond the broken level | 3 ATR | 0.75 |

The confidence values are fixed constants, not estimated probabilities.

## Output

Every five days, and at the end, the simulator prints a portfolio summary:
equity, cash, open positions with unrealized P&L, and closed-trade statistics
(win rate, average and largest win and loss, number of stops and targets hit).
It ends with the prediction accuracy: how often the direction was right and
how often the target or stop was reached within the forecast window.

## Using it from Python

```python
import sys
sys.path.insert(0, "src")
sys.path.insert(0, ".")

from trading_simulator import PointInTimeTradingSimulator

sim = PointInTimeTradingSimulator(
    tickers=["AAPL", "TSLA"],
    initial_capital=50_000,
    lookback_days=60,
    max_position_pct=0.15,
)
sim.run_multi_day_simulation("2023-01-01", "2023-06-30", forecast_days=5)
```

`run_multi_day_simulation` downloads the data it needs. A simulator keeps its
portfolio and results between calls, so create a new one for each period you
want to compare.

## Limitations

- Daily bars only. Stops and targets are checked on closes, so intraday
  touches are missed and exits happen at the close.
- No commissions, slippage, spread, or short borrowing costs.
- Entries use the previous close, which you could not actually trade at on
  day `D`.
- One position per ticker at a time and no position scaling.
- The rules and parameters are textbook defaults and were not tuned or
  validated. Results over a single quarter are dominated by noise.
