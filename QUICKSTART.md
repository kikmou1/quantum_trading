# 🚀 Quick Start Guide

Get started with quantum-inspired portfolio backtesting in 5 minutes!

## Step 1: Install Dependencies

```bash
# Create and activate virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install all required packages
pip install -r requirements.txt
```

**Installation time:** ~10-15 minutes
**Disk space required:** ~3-5 GB

### Core Dependencies Installed:

✅ **Data**: yfinance, pandas, numpy
✅ **Classical Optimization**: PyPortfolioOpt, cvxpy, riskfolio-lib
✅ **Quantum Libraries**: qiskit, pennylane, dwave-ocean-sdk
✅ **Visualization**: matplotlib, seaborn, plotly
✅ **Backtesting**: Custom engine (no external dependencies)

## Step 2: Run Your First Backtest

```bash
# Run with default settings (20 stocks, 2018-2024)
python run_backtest.py
```

**What happens:**
1. Downloads 7 years of data for 20 S&P 500 stocks (AAPL, MSFT, GOOGL, etc.)
2. Tests 8+ optimization algorithms (classical + quantum-inspired)
3. Compares performance with monthly rebalancing
4. Generates visualizations and reports

**Expected runtime:** 5-15 minutes (depending on your hardware)

### Sample Output:

```
================================================================================
QUANTUM-INSPIRED PORTFOLIO OPTIMIZATION BACKTEST
================================================================================

Loading configurations...
Selected portfolio: S&P 500 Large Cap - 20 Assets
Number of assets: 20

Fetching market data...
Downloaded 1761 days of data

Running backtests...
  ✓ EqualWeight
  ✓ MinimumVariance
  ✓ MaximumSharpe
  ✓ HierarchicalRiskParity
  ✓ RiskParity
  ✓ QAOA_Continuous
  ✓ HybridAnnealing

================================================================================
BACKTEST RESULTS
================================================================================

📊 PERFORMANCE SUMMARY
optimizer_name              final_value  annualized_return  sharpe_ratio
MaximumSharpe               $127,543     0.1234            1.45
QAOA_Continuous             $125,891     0.1198            1.38
HybridAnnealing             $124,332     0.1156            1.32
HierarchicalRiskParity      $122,109     0.1089            1.25
...

🏆 Best Sharpe Ratio: MaximumSharpe (1.45)
💰 Highest Return: MaximumSharpe (12.34%)
🛡️  Lowest Drawdown: MinimumVariance (-15.23%)
```

## Step 3: View Results

### Performance Comparison Table
```
results/data/comparison_TIMESTAMP.csv
```

Open in Excel or any spreadsheet software to see:
- Final portfolio values
- Sharpe, Sortino, Calmar ratios
- Maximum drawdowns
- Win rates
- Turnover statistics

### Visualizations
```
results/figures/
  ├── equity_curves.png           # Portfolio value over time
  ├── drawdowns.png               # Drawdown charts
  ├── risk_return_scatter.png     # Risk vs return plot
  ├── metrics_comparison.png      # Bar charts of metrics
  ├── returns_distribution.png    # Return histograms
  └── rolling_sharpe.png          # Rolling Sharpe ratios
```

## Step 4: Customize Your Backtest

### Change the Portfolio

Edit `config/assets.yaml`:

```yaml
# Use medium portfolio (50 assets) instead of small (20)
medium_portfolio:
  tickers:
    - AAPL
    - MSFT
    # ... 48 more tickers
```

Then in `run_backtest.py` line ~50:
```python
portfolio_name = "medium_portfolio"  # Changed from "small_portfolio"
```

### Adjust Time Period

Edit `config/backtest.yaml`:

```yaml
period:
  start_date: "2020-01-01"  # Changed from 2018
  end_date: "2024-12-31"
```

### Change Rebalancing Frequency

```yaml
rebalancing:
  frequency: "quarterly"  # Options: daily, weekly, monthly, quarterly
```

### Modify Transaction Costs

```yaml
transaction_costs:
  total_cost_pct: 0.0030  # 30 bps instead of 15 bps
```

## Step 5: Advanced Usage

### Test Specific Algorithms Only

Edit `run_backtest.py` around line ~90:

```python
# Test only quantum-inspired methods
all_optimizers = quantum_optimizers  # Comment out classical_optimizers
```

### Add Custom Algorithm Parameters

Edit `config/parameters.yaml`:

```yaml
quantum_inspired:
  qaoa:
    risk_factor: 0.7  # More aggressive (default 0.5)
    max_iterations: 200  # More optimization (default 100)
```

### Run with Different Risk-Free Rate

```yaml
performance:
  risk_free_rate: 0.05  # 5% instead of 4%
```

## Common Use Cases

### 1. Test Defensive Portfolio

```yaml
# In config/assets.yaml
defensive:
  name: "Defensive Low Beta"
  tickers:
    - JNJ   # Johnson & Johnson
    - PG    # Procter & Gamble
    - KO    # Coca-Cola
    - WMT   # Walmart
    # ... more defensive stocks
```

```python
# In run_backtest.py
portfolio_name = "defensive"
```

### 2. Compare Different Time Periods

Run multiple backtests for different market conditions:

**Bull Market (2019-2021):**
```yaml
period:
  start_date: "2019-01-01"
  end_date: "2021-12-31"
```

**Bear Market (2022):**
```yaml
period:
  start_date: "2022-01-01"
  end_date: "2022-12-31"
```

### 3. Test High-Frequency Rebalancing

```yaml
rebalancing:
  frequency: "weekly"  # Rebalance every week
  lookback_window: 63  # Use 3 months of data
```

**Note:** Higher frequency = more transaction costs!

## Troubleshooting

### Issue: Import errors

```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

### Issue: Data download fails

```python
# yfinance sometimes has issues. Try:
# 1. Check internet connection
# 2. Reduce number of tickers
# 3. Try different date range
```

### Issue: Out of memory

```yaml
# Reduce portfolio size or lookback window
rebalancing:
  lookback_window: 126  # 6 months instead of 1 year
```

### Issue: Quantum libraries not found

```bash
# Install quantum libraries separately
pip install qiskit qiskit-finance
pip install pennylane
pip install dwave-ocean-sdk
```

**Note:** The framework will still work without quantum libraries, just with classical methods only.

## Next Steps

1. **Understand the Results**: Read through `BACKTESTING_PLAN.md` for detailed explanation of metrics
2. **Experiment**: Try different portfolios, time periods, and parameters
3. **Learn More**: Study `quantum_how_to.md` for quantum algorithm theory
4. **Contribute**: Add your own custom optimizers or improvements

## Performance Expectations

Based on academic research and our testing:

| Algorithm              | Expected Sharpe | Typical Range |
|------------------------|-----------------|---------------|
| Equal Weight           | 0.6-0.8         | Baseline      |
| Mean-Variance          | 0.7-1.0         | Classical     |
| HRP                    | 0.8-1.1         | Modern        |
| Max Sharpe             | 0.9-1.3         | Classical     |
| QAOA                   | 0.8-1.3         | Quantum       |
| Hybrid Annealing       | 0.9-1.4         | Quantum       |

**Factors affecting results:**
- Time period (bull vs bear market)
- Number of assets (more assets = more diversification)
- Transaction costs (higher costs reduce returns)
- Rebalancing frequency (more frequent = higher costs)
- Asset selection (tech-heavy vs diversified)

## Resources

- **Documentation**: See `README_BACKTEST.md`
- **Theory**: See `quantum_how_to.md`
- **Configuration**: See `config/*.yaml`
- **Logs**: Check `backtest.log` for detailed execution info

## Getting Help

If you encounter issues:

1. Check `backtest.log` for error details
2. Verify all configurations are valid YAML
3. Ensure data downloaded successfully
4. Review error messages carefully

## Example: Full Custom Backtest

```python
# Create custom_backtest.py

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from data_collection.fetchers import DataFetcher
from optimizers.classical.portfolio_optimizers import MaximumSharpeOptimizer
from backtesting.engine import BacktestEngine

# Fetch data
fetcher = DataFetcher()
tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
returns = fetcher.get_returns(tickers, '2020-01-01', '2024-01-01')

# Run backtest
engine = BacktestEngine(initial_capital=100000, rebalance_frequency='monthly')
optimizer = MaximumSharpeOptimizer()

result = engine.run_backtest(returns, optimizer, lookback_window=252)

print(f"Final Value: ${result['final_value']:,.2f}")
print(f"Sharpe Ratio: {result['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {result['maximum_drawdown']*100:.2f}%")
```

Run it:
```bash
python custom_backtest.py
```

---

**Happy Backtesting! 🚀**

For questions or issues, check the documentation or review the code comments.
