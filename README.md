# Quantum Trading

A Python research toolkit for comparing **classical** and **quantum-inspired** portfolio optimization, plus a point-in-time **trading simulator** and an interactive **Streamlit dashboard**. Everything runs locally on a laptop using free market data from Yahoo Finance.

> ⚠️ **Disclaimer:** This project is for research and education only. It is not financial advice, and simulated or backtested results do not guarantee future performance.

---

## Features

- **Portfolio optimization backtester**: walk-forward backtests with periodic rebalancing and transaction costs.
- **Classical optimizers**: Equal Weight, Mean-Variance (Markowitz), Minimum Variance, Maximum Sharpe, Hierarchical Risk Parity, Risk Parity, Black-Litterman, and Target Return.
- **Quantum-inspired optimizers**: QAOA (Qiskit), simulated quantum annealing (D-Wave Ocean / `neal`), and a hybrid annealing + classical refinement approach.
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

Requires **Python 3.9+**.

```bash
git clone https://github.com/kikmou1/quantum_trading.git
cd quantum_trading

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

The full install includes Qiskit, PennyLane, D-Wave Ocean, and PyTorch, so it can take 10–15 minutes and a few GB of disk space.

The QAOA optimizer also imports `qiskit_algorithms`, which is not in `requirements.txt`. Install it separately if you want QAOA:

```bash
pip install qiskit-algorithms
```

The quantum libraries are optional. If Qiskit or D-Wave Ocean is missing, the related optimizers log a warning, and the classical optimizers still work.

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

### Using the library directly

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

## Further Documentation

- [QUICKSTART.md](QUICKSTART.md): step-by-step first run
- [README_BACKTEST.md](README_BACKTEST.md): backtesting framework details
- [BACKTESTING_PLAN.md](BACKTESTING_PLAN.md): methodology and research plan
- [TRADING_SIMULATOR_README.md](TRADING_SIMULATOR_README.md): trading simulator guide
- [DASHBOARD_GUIDE.md](DASHBOARD_GUIDE.md): dashboard walkthrough
- [quantum_how_to.md](quantum_how_to.md): background on quantum-inspired algorithms in trading

---

## Tech Stack

NumPy · pandas · SciPy · yfinance · PyPortfolioOpt · riskfolio-lib · cvxpy · Qiskit · PennyLane · D-Wave Ocean · matplotlib · seaborn · Plotly · Streamlit
