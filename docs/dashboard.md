# Dashboard

`trading_dashboard.py` is a Streamlit app for browsing assets, charting their
price history, and running the trading simulator's signal logic on a single
asset and date.

```bash
pip install -r requirements.txt
streamlit run trading_dashboard.py
```

Then open http://localhost:8501.

## Choosing an asset

The sidebar lists the 224 assets in `data/tradable_assets.txt`: 103 stocks,
54 ETFs, 23 commodities, 14 indices, 10 cryptocurrencies, 9 REITs, 7 currency
pairs and 4 bond funds. Filter by category, or search by symbol, name or
description (for example "gold" matches GC=F, GLD and Goldman Sachs).

To add an asset, add a line to `data/tradable_assets.txt` in the format
`Symbol|Name|Category|Exchange|Description`, using the Yahoo Finance symbol.

## Loading data

Pick a start and end date (the default is the last two years) and click
**Load Data**. The app downloads split- and dividend-adjusted daily bars from
Yahoo Finance and shows the number of days, the date range, the last price,
and a candlestick chart with volume.

## Running a simulation

Choose a trading date, a forecast horizon (1–30 calendar days) and the
starting capital, then click **Run Simulation**. The app:

1. generates signals from the 60 trading days before the chosen date, using
   the same strategies as the [trading simulator](trading-simulator.md);
2. picks the best signal and opens a position at the last close before the
   date, sized at up to 20% of capital;
3. checks the following days' closes for the stop or target and closes the
   position when one is crossed;
4. shows the signal (entry, stop, target, reasoning), the outcome, the price
   chart around the trade, and all signals the strategies produced.

If no strategy produces a signal for that date, the app says so. That is
common, because most strategies only fire in unusual conditions.

## Limitations

The same limitations as the trading simulator apply: daily closes only, no
costs, and entry at the previous close. Each run is a single trade on a
single date, so it illustrates how the rules behave but says nothing about
whether they work.
