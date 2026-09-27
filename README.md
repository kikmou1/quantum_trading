# Quantum Trading

[![CI](https://github.com/kikmou1/quantum_trading/actions/workflows/ci.yml/badge.svg)](https://github.com/kikmou1/quantum_trading/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)

A Python research toolkit for comparing **classical** and **quantum-inspired** portfolio optimization, plus a point-in-time **trading simulator** and an interactive **Streamlit dashboard**. Everything runs locally on a laptop using free market data from Yahoo Finance.

> ⚠️ **Disclaimer:** This project is for research and education only. It is not financial advice, and simulated or backtested results do not guarantee future performance.

---

## Features

- **Portfolio optimization backtester**: walk-forward backtests with periodic rebalancing and transaction costs.
- **Classical optimizers**: Equal Weight, Mean-Variance (Markowitz), Minimum Variance, Maximum Sharpe, Hierarchical Risk Parity, Risk Parity, Black-Litterman, and Target Return.
- **Quantum-inspired optimizers**: a QAOA-style QUBO asset selector, simulated annealing (D-Wave Ocean / `neal`), and a hybrid annealing + classical refinement approach. All of them run on classical hardware; see [Limitations](#limitations).
- **Metrics**: Sharpe, Sortino, Calmar, Omega, information ratio, alpha/beta, max drawdown, VaR, CVaR, tail ratio, skewness, and kurtosis.
- **Point-in-time trading simulator**: produces trade signals (RSI, MACD, Bollinger Bands, momentum breakout) with entry, stop-loss, and take-profit levels. It uses only data available before each trading day, so there is no look-ahead bias.
- **Virtual portfolio**: tracks positions, P&L, and an equity curve, and compares predicted outcomes with what actually happened.
- **Interactive dashboard**: browse more than 200 tradable assets (stocks, ETFs, indices, commodities, crypto, forex, bonds, REITs), view charts, and simulate trades.
- **YAML configuration**: set the asset universe, backtest period, costs, and algorithm parameters without editing code.

---

## Project Structure

```
quantum_trading/
├── run_backtest.py              # Entry point: portfolio optimization backtest
├── trading_simulator.py         # Entry point: point-in-time trading simulator
├── trading_dashboard.py         # Entry point: Streamlit web dashboard
├── config/
│   ├── assets.yaml              # Asset universes (small / medium / sector portfolios)
│   ├── backtest.yaml            # Period, rebalancing, costs, capital, walk-forward
│   └── parameters.yaml          # Optimizer hyperparameters
├── data/
│   └── tradable_assets.txt      # Asset database used by the dashboard
├── src/
│   ├── backtesting/engine.py    # BacktestEngine (rebalancing + costs)
│   ├── data_collection/         # Yahoo Finance fetchers and preprocessing
│   ├── optimizers/
│   │   ├── base.py              # BaseOptimizer interface
│   │   ├── classical/           # Classical portfolio optimizers
│   │   └── quantum_inspired/    # QAOA and quantum annealing optimizers
│   ├── metrics/                 # Performance and risk metrics
│   ├── trading_simulator/       # Signal generators and virtual portfolio
│   ├── visualization/plots.py   # Equity curves, drawdowns, risk/return charts
│   └── utils/asset_manager.py   # Asset search and categorization
└── results/                     # Generated data, figures, and reports
```

---

## Installation

Requires **Python 3.10+**. The code runs from a clone; it is not published on PyPI.

```bash
git clone https://github.com/kikmou1/quantum_trading.git
cd quantum_trading

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

Then choose one of two installs:

| Install | Command | What you get |
|---------|---------|--------------|
| Core (about 1 minute) | `pip install -r requirements-core.txt` | Data download, classical optimizers, `QAOA_Continuous`, `HybridAnnealing` (classical fallback), backtest engine, metrics, plots, tests |
| Full (10–15 minutes, a few GB) | `pip install -r requirements.txt` | Everything above plus Qiskit, D-Wave Ocean, PennyLane, PyTorch, the trading simulator and the Streamlit dashboard |

The quantum libraries are optional. If Qiskit or D-Wave Ocean is missing, `run_backtest.py` logs a warning and skips the optimizers that need them.

---

## Quick Start (offline)

This runs every optimizer on a simulated 8-asset market. It needs no internet connection and uses a fixed random seed, so you should get the same numbers:

```bash
python examples/synthetic_backtest.py
```

Output with the full install:

```
Synthetic market: 8 assets, 1260 trading days
Monthly rebalancing, 252-day lookback, 15 bps transaction costs

        optimizer_name  annualized_return  annualized_volatility  sharpe_ratio  maximum_drawdown  avg_turnover
       MinimumVariance             0.1040                 0.1166        0.5490           -0.1443        0.0278
HierarchicalRiskParity             0.0810                 0.1375        0.2980           -0.1867        0.0232
       QAOA_Continuous             0.0876                 0.2124        0.2242           -0.3033        0.3006
            RiskParity             0.0686                 0.1526        0.1875           -0.2129        0.0087
         MaximumSharpe             0.0639                 0.1709        0.1398           -0.1922        0.2664
           EqualWeight             0.0609                 0.1688        0.1239           -0.2352        0.0000
        BlackLitterman             0.0609                 0.1688        0.1239           -0.2352        0.0000
       HybridAnnealing             0.0394                 0.1736       -0.0032           -0.3530        0.2649
```

With the core install, the `HybridAnnealing` row differs because it uses its classical fallback instead of D-Wave's sampler.

These numbers only show that the pipeline works. The ranking changes with the random seed, so they say nothing about which method is better. Black-Litterman matches Equal Weight here because, with no views and no market caps, its equilibrium portfolio is the equal-weight portfolio.

---

## Usage

### 1. Portfolio optimization backtest

```bash
python run_backtest.py
```

This downloads prices for the `small_portfolio` universe (20 large-cap US stocks). It then backtests the classical and quantum-inspired optimizers with monthly rebalancing and prints a ranked comparison. It saves:

- `results/data/comparison_<timestamp>.csv`: metrics for each optimizer
- `results/data/<Optimizer>_values_<timestamp>.csv` and `..._returns_<timestamp>.csv`
- Charts in `results/figures/`
- A log in `backtest.log`

### 2. Trading simulator

```bash
python trading_simulator.py
```

By default, the simulator trades 8 tech stocks from Jan 1 to Mar 31, 2024 with $100,000 of virtual capital. It generates hybrid technical signals, opens and closes positions using stop-loss and take-profit rules, and reports predicted vs. actual outcomes. To change the tickers, dates, or capital, edit the `config` dict in `main()`.

### 3. Interactive dashboard

```bash
streamlit run trading_dashboard.py
```

Open http://localhost:8501 in your browser. From there you can search or filter assets, view historical price charts, and run trade simulations.

### Using the code directly

```python
import sys; sys.path.insert(0, "src")
from data_collection.fetchers import DataFetcher
from optimizers.classical.portfolio_optimizers import HierarchicalRiskParityOptimizer

returns = DataFetcher().get_returns(["AAPL", "MSFT", "GOOGL", "JPM"], "2020-01-01", "2024-12-31")
weights = HierarchicalRiskParityOptimizer().optimize(returns)
print(weights)
```

Check the signatures in `src/data_collection/fetchers.py` for the exact arguments.

---

## Configuration

| File | What it controls |
|------|------------------|
| `config/assets.yaml` | Named asset universes: `small_portfolio` (20), `medium_portfolio` (50), `tech_heavy`, `defensive`, and more |
| `config/backtest.yaml` | Date range (default 2018–2024), rebalancing frequency and lookback, transaction costs (15 bps total by default), initial capital, benchmark (`SPY`), risk-free rate, walk-forward windows |
| `config/parameters.yaml` | Hyperparameters for each classical and quantum-inspired optimizer |

To backtest a different universe, change `portfolio_name` in `run_backtest.py`.

---

## Adding a New Optimizer

Subclass `BaseOptimizer` and implement `optimize`. It should return a `pd.Series` of weights indexed by ticker:

```python
from optimizers.base import BaseOptimizer
import pandas as pd

class MyOptimizer(BaseOptimizer):
    def optimize(self, returns: pd.DataFrame, **kwargs) -> pd.Series:
        weights = ...  # your logic
        return self.normalize_weights(pd.Series(weights, index=returns.columns))
```

Then add an instance to the optimizer list in `run_backtest.py`.

---

## Testing

```bash
pip install ruff
ruff check .
pytest
```

The tests use synthetic data and need no network access. They check the metrics against hand-computed values; check that every optimizer returns long-only weights summing to 1; and test specific properties, such as Risk Parity giving equal risk contributions and Black-Litterman without views returning the market portfolio. They also verify that the backtest engine never gives an optimizer data from the rebalance date or later, and that transaction costs are applied; test the virtual portfolio's P&L for long and short trades; and cover data preprocessing. The Qiskit and D-Wave tests are skipped when those libraries are not installed. CI runs everything on Python 3.10–3.12.

---

## Limitations

Read these before drawing conclusions from any result.

**About the "quantum" methods**

- Nothing here runs on quantum hardware or simulates a quantum circuit.
- `QAOAPortfolioOptimizer` writes asset selection as a QUBO (the problem QAOA would solve) and solves it with classical simulated annealing. Qiskit is only checked at import time. It picks roughly a third of the assets and weights them equally.
- `QAOAContinuousOptimizer` is a classical mean/volatility trade-off solved with SciPy's SLSQP.
- `QuantumAnnealingOptimizer` uses D-Wave's classical simulated annealing sampler (`neal`), not a D-Wave quantum computer.
- `HybridAnnealingOptimizer` selects assets with that sampler, then sets weights with SLSQP. Without D-Wave Ocean it skips the selection step.
- So a comparison in this project is between classical heuristics inspired by quantum algorithms and standard classical optimizers. It is not evidence for or against quantum advantage.

**About the backtests**

- **Survivorship bias:** the default universes are today's large-cap stocks. Companies that were delisted or fell out of the index are missing, which flatters historical returns.
- **Data quality:** prices come from Yahoo Finance through `yfinance`, which can have gaps and errors and changes over time. Gaps are forward-filled; missing values at the start of a series are back-filled, which produces zero returns before an asset's first real price.
- **Weights are held constant between rebalances.** The engine applies the target weights to every day's returns, which is equivalent to rebalancing daily without paying for it. Real portfolios drift between rebalances.
- **Simple cost model:** a flat 15 bps is charged on one-way turnover at each rebalance. The first allocation is free, and there is no slippage, bid-ask spread, market impact, borrowing cost, or tax.
- **Estimation error:** expected returns come from the mean of the lookback window, which is very noisy. Mean-based methods (Maximum Sharpe, Mean-Variance, Target Return) are sensitive to it.
- **Maximum Sharpe fallback:** when no asset's expected return beats the risk-free rate, Maximum Sharpe uses Minimum Variance for that rebalance.
- **No out-of-sample protocol by default:** `run_backtest.py` backtests one period with default parameters. If you tune parameters on the same period, the results will overfit it.

**About the trading simulator**

- Signals come from simple technical rules (RSI, MACD, Bollinger Bands, breakouts). Stops and targets are checked against daily closes only, so intraday moves through a stop are not modeled, and there are no costs or short-borrow fees.

---

## Further Documentation

- [QUICKSTART.md](QUICKSTART.md): step-by-step first run
- [README_BACKTEST.md](README_BACKTEST.md): backtesting framework details
- [BACKTESTING_PLAN.md](BACKTESTING_PLAN.md): methodology and research plan
- [TRADING_SIMULATOR_README.md](TRADING_SIMULATOR_README.md): trading simulator guide
- [DASHBOARD_GUIDE.md](DASHBOARD_GUIDE.md): dashboard walkthrough
- [quantum_how_to.md](quantum_how_to.md): background on quantum-inspired algorithms in trading

---

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for setup and guidelines, and [CHANGELOG.md](CHANGELOG.md) for recent changes. Please report bugs through [GitHub Issues](https://github.com/kikmou1/quantum_trading/issues).

---

## License

[MIT](LICENSE)

---

## Tech Stack

NumPy · pandas · SciPy · yfinance · PyPortfolioOpt · riskfolio-lib · cvxpy · Qiskit · PennyLane · D-Wave Ocean · matplotlib · seaborn · Plotly · Streamlit
