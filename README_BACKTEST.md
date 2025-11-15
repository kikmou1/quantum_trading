# Quantum-Inspired Portfolio Optimization Backtesting Framework

A comprehensive backtesting system comparing classical and quantum-inspired portfolio optimization algorithms using entirely free data sources and libraries.

## 🎯 Overview

This framework implements and compares 10+ portfolio optimization algorithms across classical and quantum-inspired approaches:

**Classical Methods:**
- Equal Weight (Baseline)
- Mean-Variance Optimization (Markowitz)
- Minimum Variance
- Maximum Sharpe Ratio
- Hierarchical Risk Parity (HRP)
- Risk Parity
- Black-Litterman

**Quantum-Inspired Methods:**
- QAOA (Quantum Approximate Optimization Algorithm)
- VQE (Variational Quantum Eigensolver)
- Simulated Quantum Annealing
- Hybrid Quantum-Classical

## 📊 Key Features

- **100% Free**: Uses yfinance, no paid APIs required
- **Comprehensive Metrics**: Sharpe, Sortino, Calmar ratios, VaR, CVaR, drawdowns
- **Walk-Forward Analysis**: Rolling window backtesting with realistic constraints
- **Transaction Costs**: Models realistic trading costs (15 bps default)
- **Rich Visualizations**: Equity curves, drawdowns, risk-return scatter plots
- **Flexible Configuration**: YAML-based configuration for easy customization

## 🚀 Quick Start

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

```bash
# Run backtest with default settings
python run_backtest.py
```

This will:
1. Download data for 20 S&P 500 stocks (2018-2024)
2. Run backtests for all available optimizers
3. Generate performance comparison
4. Create visualizations in `results/figures/`
5. Save detailed results to `results/data/`

## 📁 Project Structure

```
quantum_trading/
├── config/                     # Configuration files
│   ├── assets.yaml            # Portfolio definitions
│   ├── parameters.yaml        # Algorithm parameters
│   └── backtest.yaml          # Backtesting settings
│
├── src/
│   ├── data_collection/       # Data fetching & preprocessing
│   │   ├── fetchers.py        # Yahoo Finance integration
│   │   └── preprocessors.py  # Data cleaning
│   │
│   ├── optimizers/
│   │   ├── classical/         # Classical optimizers
│   │   │   └── portfolio_optimizers.py
│   │   └── quantum_inspired/  # Quantum-inspired optimizers
│   │       ├── qaoa_optimizer.py
│   │       └── quantum_annealing.py
│   │
│   ├── backtesting/
│   │   └── engine.py          # Backtesting engine
│   │
│   ├── metrics/               # Performance & risk metrics
│   │   ├── performance.py
│   │   └── risk.py
│   │
│   └── visualization/
│       └── plots.py           # Visualization module
│
├── data/                      # Cached data
├── results/                   # Results & visualizations
├── run_backtest.py           # Main execution script
└── requirements.txt          # Dependencies
```

## ⚙️ Configuration

### Assets Configuration (`config/assets.yaml`)

Define your portfolio universe:

```yaml
small_portfolio:
  name: "S&P 500 Large Cap - 20 Assets"
  tickers:
    - AAPL
    - MSFT
    - GOOGL
    # ... more tickers
```

### Backtest Configuration (`config/backtest.yaml`)

Customize backtest parameters:

```yaml
period:
  start_date: "2018-01-01"
  end_date: "2024-12-31"

rebalancing:
  frequency: "monthly"  # daily, weekly, monthly, quarterly
  lookback_window: 252  # Days for optimization

transaction_costs:
  total_cost_pct: 0.0015  # 15 basis points

capital:
  initial: 100000.0  # Starting capital
```

### Algorithm Parameters (`config/parameters.yaml`)

Fine-tune optimizer settings:

```yaml
classical:
  maximum_sharpe:
    risk_free_rate: 0.04
    allow_short: false

quantum_inspired:
  qaoa:
    p_layers: 3
    risk_factor: 0.5  # Balance risk vs return
```

## 📈 Understanding Results

### Performance Metrics

- **Sharpe Ratio**: Risk-adjusted returns (higher is better, >1.0 is good)
- **Sortino Ratio**: Like Sharpe but only penalizes downside volatility
- **Calmar Ratio**: Return / Max Drawdown
- **Maximum Drawdown**: Largest peak-to-trough decline (lower is better)
- **Win Rate**: Percentage of profitable periods

### Risk Metrics

- **VaR (Value at Risk)**: Maximum expected loss at 95% confidence
- **CVaR (Conditional VaR)**: Average loss beyond VaR threshold
- **Downside Deviation**: Volatility of negative returns only

### Output Files

**results/data/**
- `comparison_TIMESTAMP.csv`: Summary comparison of all optimizers
- `[optimizer]_values_TIMESTAMP.csv`: Portfolio value time series
- `[optimizer]_returns_TIMESTAMP.csv`: Daily returns

**results/figures/**
- `equity_curves.png`: Portfolio value over time
- `drawdowns.png`: Drawdown charts
- `risk_return_scatter.png`: Risk vs return visualization
- `metrics_comparison.png`: Bar charts of key metrics
- `returns_distribution.png`: Return distributions
- `rolling_sharpe.png`: Rolling Sharpe ratio

## 🔬 Expected Results

Based on academic research and industry results:

**Classical Methods:**
- Equal Weight: ~0.5-0.8 Sharpe ratio (baseline)
- Mean-Variance: ~0.6-1.0 Sharpe ratio
- HRP: ~0.7-1.0 Sharpe ratio (robust to estimation errors)
- Max Sharpe: ~0.8-1.2 Sharpe ratio

**Quantum-Inspired Methods:**
- QAOA: ~0.7-1.2 Sharpe ratio (5-10% improvement potential)
- Quantum Annealing: ~0.7-1.3 Sharpe ratio
- Hybrid: ~0.8-1.3 Sharpe ratio (10-20% improvement potential)

*Note: Results depend heavily on time period, asset selection, and market conditions*

## 🧪 Advanced Usage

### Custom Portfolio

Edit `config/assets.yaml` to test different asset universes:

```yaml
my_portfolio:
  name: "Tech Stocks"
  tickers:
    - AAPL
    - MSFT
    - GOOGL
    - NVDA
    - AMD
```

Then modify `run_backtest.py`:

```python
portfolio_name = "my_portfolio"  # Change this line
```

### Walk-Forward Analysis

Enable walk-forward testing in `config/backtest.yaml`:

```yaml
walk_forward:
  enabled: true
  train_period: 252   # 1 year training
  test_period: 63     # 1 quarter testing
  step_size: 21       # Monthly steps
```

### Add Custom Optimizer

Create a new optimizer class:

```python
from src.optimizers.base import BaseOptimizer

class MyCustomOptimizer(BaseOptimizer):
    def __init__(self):
        super().__init__(name="MyCustom")

    def optimize(self, returns, **kwargs):
        # Your optimization logic here
        weights = # ... calculate weights
        return weights
```

Add to `run_backtest.py`:

```python
from my_module import MyCustomOptimizer

all_optimizers.append(MyCustomOptimizer())
```

## 📊 Benchmark Comparison

The framework automatically compares against S&P 500 (SPY):

- **Alpha**: Excess return vs benchmark
- **Beta**: Correlation with benchmark
- **Information Ratio**: Risk-adjusted excess return
- **Tracking Error**: Volatility of excess returns

## 🐛 Troubleshooting

### Data Download Issues

```python
# If yfinance fails, increase retry attempts in fetchers.py
# Or manually download and place in data/raw/
```

### Memory Issues (Large Portfolios)

```yaml
# Reduce lookback window in config/backtest.yaml
rebalancing:
  lookback_window: 126  # 6 months instead of 1 year
```

### Quantum Libraries Not Available

The framework gracefully handles missing quantum libraries:

```
✗ QAOA optimizer not available: No module named 'qiskit'
```

Install optional dependencies:

```bash
pip install qiskit qiskit-finance pennylane dwave-ocean-sdk
```

## 📚 References

This implementation is based on:

1. **HSBC-IBM Study (2025)**: 34% improvement in bond trading using quantum
2. **Multiverse Computing**: Portfolio optimization with D-Wave quantum annealers
3. **Academic Research**: QAOA and VQE for portfolio optimization

See `quantum_how_to.md` for detailed background on quantum-inspired algorithms.

## 🤝 Contributing

Contributions welcome! Areas for improvement:

- Additional optimizers (CVaR optimization, robust optimization)
- Machine learning integration
- Real-time data feeds
- Multi-asset class portfolios (stocks + bonds + commodities)
- Options and derivatives support

## 📄 License

This project uses open-source libraries:
- Qiskit (Apache 2.0)
- PyPortfolioOpt (Apache 2.0)
- D-Wave Ocean SDK (Apache 2.0)
- yfinance (Apache 2.0)

## 🎓 Learning Resources

- **Quantum Computing**: Start with `quantum_how_to.md`
- **Portfolio Theory**: Markowitz (1952), Sharpe (1964)
- **Modern Methods**: HRP (Lopez de Prado, 2016)
- **Quantum Finance**: qiskit-finance documentation

## ⚡ Performance Tips

1. **Start Small**: Test with 10-20 assets before scaling to 100+
2. **Use Caching**: Data is automatically cached in `data/raw/`
3. **Parallel Processing**: Enable in `config/backtest.yaml`
4. **GPU Acceleration**: Install qiskit-aer-gpu for quantum simulations

## 📞 Support

For issues or questions:
1. Check `backtest.log` for detailed error messages
2. Review configuration files for typos
3. Ensure all dependencies are installed
4. Verify data download completed successfully

---

**Happy Backtesting! 🚀📈**
