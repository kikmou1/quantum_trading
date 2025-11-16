# 🎯 Interactive Trading Dashboard Guide

An easy-to-use web interface for selecting any tradable asset, viewing historical data, and simulating trades!

---

## 🚀 Quick Start

### 1. Install Dependencies (if not already done)

```bash
pip install streamlit plotly
```

### 2. Launch Dashboard

```bash
streamlit run trading_dashboard.py
```

The dashboard will open in your browser at `http://localhost:8501`

---

## 📊 How to Use

### **Step 1: Select an Asset**

**Sidebar → Asset Selection**

Choose from 500+ tradable assets:

- **By Category**: Select from dropdown
  - Stock, ETF, Commodity, Crypto, Forex, Index, Bond, REIT

- **By Search**: Type keywords
  - "gold" → Gold futures, Gold ETF, Gold miners
  - "bitcoin" → BTC-USD, crypto ETFs
  - "oil" → Crude oil, Oil ETFs, energy stocks
  - "AAPL" → Apple stock

- **Popular Assets**: Default view shows most liquid assets
  - SPY, QQQ, AAPL, MSFT, Gold (GC=F), Bitcoin (BTC-USD)

**Asset Info** shows:
- Symbol (e.g., GC=F for Gold)
- Full name
- Category
- Exchange
- Description

---

### **Step 2: Load Data**

**Main Panel → Data Settings**

1. **Set Date Range**:
   - Start Date: Default 2 years ago
   - End Date: Today

2. **Click "Load Data"**:
   - Downloads from Yahoo Finance (free)
   - Shows progress bar
   - Displays confirmation

**Data Summary** shows:
- Total data points
- First available date
- Last available date
- Current price

**Interactive Price Chart**:
- Candlestick chart (if OHLC available)
- Volume bars below
- Zoom and pan enabled
- Hover for details

---

### **Step 3: Run Simulation**

**Trading Simulation Section**

1. **Select Trading Date**:
   - Choose any historical date
   - Must have 60+ days history before
   - Must have 5+ days data after
   - Dropdown shows available dates

2. **Set Forecast Days** (1-30):
   - How many days to predict ahead
   - Default: 5 days
   - Longer = more uncertainty

3. **Set Initial Capital** ($1,000 - $1,000,000):
   - Virtual trading capital
   - Default: $100,000
   - Affects position size

4. **Click "Run Simulation"**:
   - Generates trade signals using only past data
   - Selects best strategy
   - Executes virtual trade
   - Monitors over forecast period
   - Compares prediction vs reality

---

### **Step 4: Analyze Results**

**Top Metrics Row**:
- **Entry Price**: Where you bought/sold
- **Stop Loss**: Auto-exit if wrong (with %)
- **Take Profit**: Auto-exit if right (with %)
- **P&L**: Profit/loss from trade

**Trade Signal Details**:
- Direction (LONG or SHORT)
- Strategy used (RSI, MACD, Bollinger, Breakout)
- Confidence score (0-100%)
- Position size (number of shares)
- Risk/Reward ratio
- Reasoning (why this trade)

**Prediction vs Reality**:
- **Predicted Direction**: UP or DOWN
- **Actual Movement**: % change (✅ or ❌)
- **Outcome**:
  - 🎯 Take Profit Hit (you won!)
  - 🛑 Stop Loss Hit (saved you from bigger loss)
  - ⏳ Still Open (neither triggered)

**Interactive Chart**:
- Full price history
- Green line: Entry price
- Red line: Stop loss
- Green line: Take profit target
- Purple line: Trading date marker
- Shows if target or stop was hit

**Trade History Table**:
- All closed trades
- Entry/exit dates and prices
- P&L in $ and %
- Reason for exit
- Holding period

**All Generated Signals** (expandable):
- See all 4 strategies' recommendations
- Compare RSI vs MACD vs Bollinger vs Breakout
- Confidence and risk/reward for each
- Learn which strategies work when

---

## 💡 Example Workflows

### **Test Gold Trading**

1. **Select Asset**:
   - Search: "gold"
   - Choose: `GC=F - Gold Futures`

2. **Load Data**:
   - Start: 2022-01-01
   - End: Today
   - Click "Load Data"

3. **Pick a Date**:
   - Choose: 2023-03-15 (after SVB bank crisis)
   - Forecast: 5 days
   - Capital: $50,000

4. **Run & Analyze**:
   - See if signals predicted gold rally
   - Check if take profit was hit
   - Learn which strategy worked best

---

### **Test Bitcoin in Bull Market**

1. **Select**: `BTC-USD - Bitcoin`
2. **Load**: 2023-01-01 to Today
3. **Pick Date**: Early 2024 (bull run start)
4. **Analyze**: Did momentum strategies work?

---

### **Test S&P 500 on Crash Days**

1. **Select**: `^GSPC - S&P 500`
2. **Load**: 2020-01-01 to 2020-06-30
3. **Pick**: 2020-03-16 (COVID crash)
4. **Analyze**: Did stop losses protect you?

---

### **Test Oil During Ukraine War**

1. **Select**: `CL=F - Crude Oil WTI`
2. **Load**: 2022-01-01 to 2022-06-30
3. **Pick**: 2022-02-24 (invasion day)
4. **Analyze**: How did signals react?

---

## 📊 Available Assets (500+)

### **Major Indices**
- ^GSPC - S&P 500
- ^DJI - Dow Jones
- ^IXIC - NASDAQ
- ^VIX - Volatility Index

### **Precious Metals**
- GC=F - Gold Futures
- SI=F - Silver Futures
- GLD - Gold ETF
- SLV - Silver ETF

### **Energy**
- CL=F - Crude Oil WTI
- NG=F - Natural Gas
- USO - Oil ETF
- XLE - Energy Sector ETF

### **Cryptocurrencies**
- BTC-USD - Bitcoin
- ETH-USD - Ethereum
- SOL-USD - Solana
- DOGE-USD - Dogecoin

### **Mega Cap Tech**
- AAPL - Apple
- MSFT - Microsoft
- GOOGL - Google
- NVDA - NVIDIA
- TSLA - Tesla

### **Forex**
- EURUSD=X - Euro/Dollar
- GBPUSD=X - Pound/Dollar
- USDJPY=X - Dollar/Yen

### **Agriculture**
- ZC=F - Corn
- ZW=F - Wheat
- KC=F - Coffee
- CT=F - Cotton

See `data/tradable_assets.txt` for complete list!

---

## 🎓 Understanding the Results

### **Good Trade Signals**

✅ High confidence (>70%)
✅ Good risk/reward (>2:1)
✅ Clear reasoning
✅ Hit take profit
✅ Direction correct

### **Bad Trade Signals**

❌ Low confidence (<50%)
❌ Poor risk/reward (<1:1)
❌ Hit stop loss quickly
❌ Direction wrong

### **What to Learn**

1. **Which strategies work when**:
   - RSI good for mean reversion
   - MACD good for trending markets
   - Bollinger good for range-bound
   - Breakout good for strong trends

2. **Risk management**:
   - Stop losses prevent big losses
   - Take profits lock in gains
   - Position sizing matters

3. **Market conditions**:
   - Strategies perform differently in bull/bear
   - Volatility affects stop placement
   - Some assets easier to trade than others

---

## ⚙️ Advanced Features

### **Multiple Asset Comparison**

Run simulations on different assets for same date:
- Gold vs Bitcoin vs S&P 500
- Which had better signals?
- Which strategy worked best for each?

### **Time Period Analysis**

Test same asset across different periods:
- Bull market (2023)
- Bear market (2022)
- Crash (2020)
- Recovery (2021)

### **Strategy Performance**

Track which strategy wins:
- RSI vs MACD vs Bollinger vs Breakout
- Keep notes on when each excels
- Build your own playbook

---

## 🐛 Troubleshooting

### **"No data available"**

- Asset may not have data for selected period
- Try different date range
- Some assets have limited history
- Futures contracts may expire

### **"Insufficient history"**

- Need 60+ days before trading date
- Choose later date
- Load more historical data

### **"No trading signals"**

- No clear opportunity on that date
- Strategies didn't trigger
- Try different date
- Normal - not every day has signals

### **Dashboard won't load**

```bash
# Reinstall Streamlit
pip install --upgrade streamlit

# Check Python version (need 3.8+)
python --version

# Run with verbose
streamlit run trading_dashboard.py --logger.level=debug
```

---

## 💾 Data Sources

All data from **Yahoo Finance** (free):
- No API key needed
- Historical data up to 20+ years
- Real-time data up to today
- OHLCV (Open, High, Low, Close, Volume)

**Supported via Yahoo**:
- ✅ US Stocks (NASDAQ, NYSE)
- ✅ International Stocks
- ✅ ETFs
- ✅ Indices
- ✅ Futures (Commodities)
- ✅ Cryptocurrencies
- ✅ Forex
- ✅ Bonds (via yield symbols)

---

## 📚 Tips & Tricks

1. **Start Simple**:
   - Test SPY (S&P 500 ETF) first
   - Liquid and consistent data
   - See how strategies work

2. **Test Major Events**:
   - COVID crash (March 2020)
   - Tech bubble (2022)
   - Bank crisis (March 2023)
   - Learn from history

3. **Compare Assets**:
   - Gold vs Bitcoin in uncertainty
   - Oil vs Stocks in inflation
   - Bonds vs Stocks in recession

4. **Learn Patterns**:
   - Which signals work for which assets?
   - When do stop losses save you?
   - What's realistic risk/reward?

5. **Build Confidence**:
   - Run many simulations
   - See what could have happened
   - Understand before risking real money

---

## 🎯 Next Steps

After mastering the dashboard:

1. **Run command-line simulator**: `python trading_simulator.py`
   - Test multiple assets at once
   - Longer time periods
   - Batch testing

2. **Customize strategies**: Edit `src/trading_simulator/signal_generator.py`
   - Add your own indicators
   - Tune parameters
   - Create hybrid strategies

3. **Add ML predictions**: Enhance signals with machine learning
   - Feature engineering
   - LSTM forecasting
   - Sentiment analysis

4. **Paper trading**: Test with live data
   - Alpaca API integration
   - Real-time signals
   - Track live performance

---

## 📞 Support

**Issues?**
- Check `data/tradable_assets.txt` for valid symbols
- Verify internet connection for data download
- See logs in terminal window
- Try different asset or date range

**Want to add assets?**
Edit `data/tradable_assets.txt`:
```
SYMBOL|Name|Category|Exchange|Description
```

---

**Happy Trading! 📈💰**

*Remember: This is for educational and backtesting purposes only. Past performance does not guarantee future results.*
