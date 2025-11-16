#!/usr/bin/env python3
"""
Interactive Trading Simulator Dashboard
Streamlit-based UI for asset selection and trading simulation.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from data_collection.fetchers import DataFetcher
from data_collection.preprocessors import DataPreprocessor
from utils.asset_manager import AssetManager
from trading_simulator.signal_generator import HybridSignalGenerator, SignalType
from trading_simulator.virtual_portfolio import VirtualPortfolio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="Trading Simulator Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'asset_manager' not in st.session_state:
    st.session_state.asset_manager = AssetManager()

if 'selected_asset' not in st.session_state:
    st.session_state.selected_asset = None

if 'asset_data' not in st.session_state:
    st.session_state.asset_data = None

if 'simulation_results' not in st.session_state:
    st.session_state.simulation_results = None


def load_asset_data(symbol: str, start_date: str, end_date: str):
    """Load and cache asset data."""
    with st.spinner(f"Loading data for {symbol}..."):
        try:
            fetcher = DataFetcher()
            preprocessor = DataPreprocessor()

            prices = fetcher.get_prices([symbol], start_date, end_date)
            clean_prices = preprocessor.clean_prices(prices)

            if len(clean_prices) == 0:
                st.error(f"No data available for {symbol}")
                return None

            st.success(f"✅ Loaded {len(clean_prices)} days of data")
            return clean_prices

        except Exception as e:
            st.error(f"Error loading data: {e}")
            logger.error(f"Error loading {symbol}: {e}")
            return None


def plot_price_chart(data: pd.DataFrame, symbol: str, selected_date=None):
    """Plot interactive price chart."""
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.7, 0.3],
        subplot_titles=(f'{symbol} Price Chart', 'Volume')
    )

    # Candlestick chart
    if all(col in data.columns for col in ['Open', 'High', 'Low', 'Close']):
        fig.add_trace(
            go.Candlestick(
                x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                name='Price'
            ),
            row=1, col=1
        )
    else:
        # Fallback to line chart if OHLC not available
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data['Close'],
                mode='lines',
                name='Price',
                line=dict(color='blue')
            ),
            row=1, col=1
        )

    # Volume
    if 'Volume' in data.columns:
        fig.add_trace(
            go.Bar(
                x=data.index,
                y=data['Volume'],
                name='Volume',
                marker_color='lightblue'
            ),
            row=2, col=1
        )

    # Mark selected date
    if selected_date:
        fig.add_vline(
            x=selected_date,
            line_dash="dash",
            line_color="red",
            annotation_text="Trading Date",
            row=1, col=1
        )

    fig.update_layout(
        height=600,
        xaxis_rangeslider_visible=False,
        showlegend=True,
        hovermode='x unified'
    )

    fig.update_xaxes(title_text="Date", row=2, col=1)
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)

    return fig


def run_simulation(symbol: str, data: pd.DataFrame, trading_date: pd.Timestamp,
                   forecast_days: int, initial_capital: float):
    """Run trading simulation for selected date."""

    with st.spinner("Running simulation..."):
        try:
            # Get historical data before trading date
            historical_data = data[data.index < trading_date]

            if len(historical_data) < 60:
                st.error(f"Insufficient history. Need at least 60 days before {trading_date.date()}")
                return None

            # Get data for forecast period
            future_data = data[
                (data.index > trading_date) &
                (data.index <= trading_date + pd.Timedelta(days=forecast_days))
            ]

            if len(future_data) == 0:
                st.error(f"No data available after {trading_date.date()}")
                return None

            # Generate signals
            signal_generator = HybridSignalGenerator()
            portfolio = VirtualPortfolio(initial_capital=initial_capital, max_position_pct=0.20)

            recent_data = historical_data.tail(60)
            capital_per_trade = portfolio.available_capital_per_trade()

            signals = signal_generator.generate_all_signals(
                recent_data,
                symbol,
                trading_date,
                capital_per_trade
            )

            if not signals:
                st.warning(f"No trading signals generated for {symbol} on {trading_date.date()}")
                return None

            best_signal = signal_generator.select_best_signal(signals)

            # Execute trade
            if portfolio.can_open_position(best_signal):
                portfolio.open_position(best_signal, trading_date)

                # Monitor position over forecast period
                for check_date in future_data.index:
                    current_price = future_data.loc[check_date, 'Close']
                    portfolio.update_positions({symbol: current_price}, check_date)
                    portfolio.record_equity_snapshot(check_date)

                # Get actual outcome
                actual_high = future_data['High'].max()
                actual_low = future_data['Low'].min()
                actual_final = future_data['Close'].iloc[-1]

                results = {
                    'signal': best_signal,
                    'portfolio': portfolio,
                    'historical_data': historical_data,
                    'future_data': future_data,
                    'actual_high': actual_high,
                    'actual_low': actual_low,
                    'actual_final': actual_final,
                    'all_signals': signals
                }

                return results

            else:
                st.error("Unable to open position (insufficient capital or other constraints)")
                return None

        except Exception as e:
            st.error(f"Simulation error: {e}")
            logger.error(f"Simulation error: {e}", exc_info=True)
            return None


def display_simulation_results(results: dict, symbol: str):
    """Display simulation results."""
    signal = results['signal']
    portfolio = results['portfolio']
    future_data = results['future_data']

    st.success("✅ Simulation Complete!")

    # Metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Entry Price",
            f"${signal.entry_price:.2f}",
            None
        )

    with col2:
        st.metric(
            "Stop Loss",
            f"${signal.stop_loss:.2f}",
            f"{((signal.stop_loss - signal.entry_price) / signal.entry_price * 100):.2f}%"
        )

    with col3:
        st.metric(
            "Take Profit",
            f"${signal.take_profit:.2f}",
            f"{((signal.take_profit - signal.entry_price) / signal.entry_price * 100):.2f}%"
        )

    with col4:
        final_equity = portfolio.total_equity()
        pnl = final_equity - portfolio.initial_capital
        st.metric(
            "P&L",
            f"${pnl:+,.2f}",
            f"{(pnl / portfolio.initial_capital * 100):+.2f}%"
        )

    # Signal details
    st.subheader("📊 Trade Signal Details")

    col1, col2 = st.columns(2)

    with col1:
        st.write(f"**Direction:** {signal.signal_type.value}")
        st.write(f"**Strategy:** {signal.strategy_name}")
        st.write(f"**Confidence:** {signal.confidence:.0%}")
        st.write(f"**Position Size:** {signal.position_size} shares")
        st.write(f"**Risk/Reward:** {signal.risk_reward_ratio():.2f}")

    with col2:
        st.write(f"**Reasoning:** {signal.reasoning}")
        st.write(f"**Capital Allocated:** ${signal.entry_price * signal.position_size:,.2f}")

    # Outcome comparison
    st.subheader("🎯 Prediction vs Reality")

    hit_tp = results['actual_high'] >= signal.take_profit if signal.signal_type == SignalType.LONG else results['actual_low'] <= signal.take_profit
    hit_sl = results['actual_low'] <= signal.stop_loss if signal.signal_type == SignalType.LONG else results['actual_high'] >= signal.stop_loss

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Predicted Direction",
            "UP" if signal.signal_type == SignalType.LONG else "DOWN",
            None
        )

    with col2:
        actual_return = ((results['actual_final'] - signal.entry_price) / signal.entry_price) * 100
        direction_correct = (signal.signal_type == SignalType.LONG and actual_return > 0) or \
                           (signal.signal_type == SignalType.SHORT and actual_return < 0)

        st.metric(
            "Actual Movement",
            f"{actual_return:+.2f}%",
            "✅ Correct" if direction_correct else "❌ Wrong"
        )

    with col3:
        if hit_tp:
            outcome = "🎯 Take Profit Hit"
        elif hit_sl:
            outcome = "🛑 Stop Loss Hit"
        else:
            outcome = "⏳ Still Open"

        st.write(f"**Outcome:** {outcome}")

    # Price chart with trade markers
    st.subheader("📈 Price Chart with Trade Levels")

    fig = go.Figure()

    # Price line
    all_data = pd.concat([results['historical_data'], future_data])
    fig.add_trace(go.Scatter(
        x=all_data.index,
        y=all_data['Close'],
        mode='lines',
        name='Price',
        line=dict(color='blue')
    ))

    # Entry point
    fig.add_hline(
        y=signal.entry_price,
        line_dash="dash",
        line_color="green",
        annotation_text=f"Entry: ${signal.entry_price:.2f}"
    )

    # Stop loss
    fig.add_hline(
        y=signal.stop_loss,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Stop: ${signal.stop_loss:.2f}"
    )

    # Take profit
    fig.add_hline(
        y=signal.take_profit,
        line_dash="dash",
        line_color="green",
        annotation_text=f"Target: ${signal.take_profit:.2f}"
    )

    # Trading date marker
    fig.add_vline(
        x=signal.timestamp,
        line_dash="solid",
        line_color="purple",
        annotation_text="Trade Date"
    )

    fig.update_layout(
        height=500,
        xaxis_title="Date",
        yaxis_title="Price",
        hovermode='x unified'
    )

    st.plotly_chart(fig, use_container_width=True)

    # Trade history
    if portfolio.trades:
        st.subheader("📋 Trade History")

        trades_data = []
        for trade in portfolio.trades:
            trades_data.append({
                'Entry Date': trade.entry_date.strftime('%Y-%m-%d'),
                'Exit Date': trade.exit_date.strftime('%Y-%m-%d'),
                'Side': trade.side,
                'Entry': f"${trade.entry_price:.2f}",
                'Exit': f"${trade.exit_price:.2f}",
                'Shares': trade.quantity,
                'P&L': f"${trade.pnl:+,.2f}",
                'P&L %': f"{trade.pnl_pct:+.2f}%",
                'Exit Reason': trade.exit_reason,
                'Days': trade.holding_period_days
            })

        st.dataframe(pd.DataFrame(trades_data), use_container_width=True)

    # All generated signals
    with st.expander("🔍 All Generated Signals"):
        st.write(f"Generated {len(results['all_signals'])} signals from different strategies")

        for sig in results['all_signals']:
            st.write(f"**{sig.strategy_name}** ({sig.signal_type.value})")
            st.write(f"  Confidence: {sig.confidence:.0%}, R/R: {sig.risk_reward_ratio():.2f}")
            st.write(f"  {sig.reasoning}")
            st.write("---")


def main():
    """Main dashboard application."""

    st.title("📈 Interactive Trading Simulator")
    st.markdown("**Select an asset, choose a date, and simulate trading with predictions vs reality**")

    # Sidebar - Asset Selection
    with st.sidebar:
        st.header("🔍 Asset Selection")

        # Asset database summary
        summary = st.session_state.asset_manager.get_asset_summary()
        st.info(f"💾 Database: {summary['total_assets']} assets")

        # Category filter
        category = st.selectbox(
            "Filter by Category",
            ["All"] + summary['categories']
        )

        # Search box
        search_query = st.text_input("Search assets", placeholder="e.g., gold, bitcoin, AAPL")

        # Get assets to display
        if search_query:
            assets_df = st.session_state.asset_manager.search_assets(search_query)
        elif category != "All":
            assets_df = st.session_state.asset_manager.get_by_category(category)
        else:
            assets_df = st.session_state.asset_manager.get_popular_assets(50)

        # Display results
        if len(assets_df) > 0:
            st.write(f"Found {len(assets_df)} assets")

            # Create display format
            asset_options = {}
            for _, row in assets_df.iterrows():
                display = f"{row['symbol']} - {row['name']}"
                asset_options[display] = row['symbol']

            selected_display = st.selectbox(
                "Select Asset",
                list(asset_options.keys())
            )

            selected_symbol = asset_options[selected_display]
            st.session_state.selected_asset = st.session_state.asset_manager.get_asset_info(selected_symbol)

            # Display asset info
            if st.session_state.selected_asset:
                with st.expander("ℹ️ Asset Info"):
                    st.write(f"**Symbol:** {st.session_state.selected_asset['symbol']}")
                    st.write(f"**Name:** {st.session_state.selected_asset['name']}")
                    st.write(f"**Category:** {st.session_state.selected_asset['category']}")
                    st.write(f"**Exchange:** {st.session_state.selected_asset['exchange']}")
                    st.write(f"**Description:** {st.session_state.selected_asset['description']}")
        else:
            st.warning("No assets found")

    # Main content
    if st.session_state.selected_asset:
        symbol = st.session_state.selected_asset['symbol']
        name = st.session_state.selected_asset['name']

        st.header(f"{symbol} - {name}")

        # Data loading section
        with st.expander("📊 Data Settings", expanded=True):
            col1, col2 = st.columns(2)

            with col1:
                # Calculate default date range
                end_date = datetime.now()
                start_date = end_date - timedelta(days=730)  # 2 years

                data_start = st.date_input(
                    "Start Date",
                    value=start_date,
                    max_value=datetime.now()
                )

            with col2:
                data_end = st.date_input(
                    "End Date (Today)",
                    value=end_date,
                    max_value=datetime.now()
                )

            if st.button("📥 Load Data", type="primary"):
                st.session_state.asset_data = load_asset_data(
                    symbol,
                    data_start.strftime('%Y-%m-%d'),
                    data_end.strftime('%Y-%m-%d')
                )

        # Display loaded data
        if st.session_state.asset_data is not None:
            data = st.session_state.asset_data

            # Data summary
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Data Points", len(data))

            with col2:
                st.metric("First Date", data.index[0].strftime('%Y-%m-%d'))

            with col3:
                st.metric("Last Date", data.index[-1].strftime('%Y-%m-%d'))

            with col4:
                current_price = data['Close'].iloc[-1]
                st.metric("Last Price", f"${current_price:.2f}")

            # Price chart
            st.plotly_chart(
                plot_price_chart(data, symbol),
                use_container_width=True
            )

            # Trading simulation section
            st.header("🎯 Trading Simulation")

            col1, col2, col3 = st.columns(3)

            with col1:
                # Trading date selector
                available_dates = data.index[60:-5]  # Need 60 days history and 5 days future
                if len(available_dates) > 0:
                    trading_date = st.selectbox(
                        "Select Trading Date",
                        available_dates,
                        index=len(available_dates)//2,  # Default to middle
                        format_func=lambda x: x.strftime('%Y-%m-%d')
                    )
                else:
                    st.error("Insufficient data for simulation")
                    trading_date = None

            with col2:
                forecast_days = st.number_input(
                    "Forecast Days",
                    min_value=1,
                    max_value=30,
                    value=5
                )

            with col3:
                initial_capital = st.number_input(
                    "Initial Capital ($)",
                    min_value=1000,
                    max_value=1000000,
                    value=100000,
                    step=10000
                )

            if trading_date and st.button("▶️ Run Simulation", type="primary"):
                results = run_simulation(
                    symbol,
                    data,
                    trading_date,
                    forecast_days,
                    initial_capital
                )

                if results:
                    st.session_state.simulation_results = results

            # Display results
            if st.session_state.simulation_results:
                st.markdown("---")
                display_simulation_results(st.session_state.simulation_results, symbol)

    else:
        # Welcome screen
        st.info("👈 Select an asset from the sidebar to begin")

        st.markdown("""
        ### 🚀 Quick Start Guide

        1. **Select an Asset**
           - Browse by category or search
           - Popular options: Gold (GC=F), Bitcoin (BTC-USD), S&P 500 (^GSPC), etc.

        2. **Load Data**
           - Choose date range (default: last 2 years)
           - Click "Load Data" to download from Yahoo Finance

        3. **Run Simulation**
           - Pick a trading date from history
           - Set forecast horizon (how many days to predict)
           - Set virtual capital
           - Click "Run Simulation"

        4. **Analyze Results**
           - See entry, stop loss, and take profit levels
           - Compare predictions vs actual outcomes
           - View trade P&L and statistics

        ### 📊 Available Assets

        - **Stocks**: 200+ US and international stocks
        - **ETFs**: 60+ sector, thematic, and leveraged ETFs
        - **Commodities**: Gold, Silver, Oil, Natural Gas, Agriculture
        - **Cryptocurrencies**: Bitcoin, Ethereum, and more
        - **Forex**: Major currency pairs
        - **Indices**: S&P 500, NASDAQ, Dow Jones, etc.

        ### 💡 Tips

        - Start with liquid assets (SPY, AAPL, GC=F, BTC-USD)
        - Test different market conditions (bull, bear, sideways)
        - Compare multiple trading dates to see strategy consistency
        - Use forecast days 3-10 for realistic predictions
        """)


if __name__ == "__main__":
    main()
