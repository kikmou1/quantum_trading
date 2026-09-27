"""
Data fetching module for retrieving financial data from various sources.
Primary source: Yahoo Finance (yfinance)
Backup: Alpha Vantage, pandas-datareader
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class YahooFinanceFetcher:
    """
    Fetch historical market data using Yahoo Finance API (yfinance).
    This is the primary data source as it's completely free and unlimited.
    """

    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize the Yahoo Finance fetcher.

        Args:
            cache_dir: Directory to cache downloaded data
        """
        self.cache_dir = cache_dir or Path("data/raw")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def fetch_prices(
        self,
        tickers: List[str],
        start_date: str,
        end_date: str,
        interval: str = "1d",
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        Fetch historical price data for a list of tickers.

        Args:
            tickers: List of ticker symbols
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            interval: Data interval (1d, 1wk, 1mo)
            use_cache: Whether to use cached data if available

        Returns:
            DataFrame with adjusted close prices
        """
        cache_file = self._get_cache_path(tickers, start_date, end_date, interval)

        # Try to load from cache
        if use_cache and cache_file.exists():
            logger.info(f"Loading cached data from {cache_file}")
            try:
                return pd.read_csv(cache_file, index_col=0, parse_dates=True)
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}. Re-downloading...")

        # Download data
        logger.info(f"Downloading data for {len(tickers)} tickers from {start_date} to {end_date}")

        try:
            data = yf.download(
                tickers,
                start=start_date,
                end=end_date,
                interval=interval,
                auto_adjust=True,  # Use adjusted prices
                progress=False,
                threads=True
            )

            # Extract close prices
            if len(tickers) == 1:
                # Handle both Series and DataFrame (yfinance versions differ)
                close_data = data['Close']
                if isinstance(close_data, pd.Series):
                    prices = close_data.to_frame(name=tickers[0])
                else:
                    # Already a DataFrame
                    prices = close_data
                    if prices.columns[0] != tickers[0]:
                        prices.columns = [tickers[0]]
            else:
                prices = data['Close']

            # Remove any completely empty columns
            prices = prices.dropna(axis=1, how='all')

            # Save to cache
            if use_cache:
                prices.to_csv(cache_file)
                logger.info(f"Cached data to {cache_file}")

            return prices

        except Exception as e:
            logger.error(f"Error downloading data: {e}")
            raise

    def fetch_returns(
        self,
        tickers: List[str],
        start_date: str,
        end_date: str,
        interval: str = "1d",
        log_returns: bool = True
    ) -> pd.DataFrame:
        """
        Fetch and calculate returns.

        Args:
            tickers: List of ticker symbols
            start_date: Start date
            end_date: End date
            interval: Data interval
            log_returns: Use log returns if True, simple returns if False

        Returns:
            DataFrame of returns
        """
        prices = self.fetch_prices(tickers, start_date, end_date, interval)

        if log_returns:
            returns = np.log(prices / prices.shift(1))
        else:
            returns = prices.pct_change()

        # Drop first row (NaN)
        returns = returns.dropna(how='all')

        return returns

    def fetch_ohlcv(
        self,
        ticker: str,
        start_date: str,
        end_date: str,
        interval: str = "1d"
    ) -> pd.DataFrame:
        """
        Fetch daily bars (Open, High, Low, Close, Volume) for one ticker.

        Args:
            ticker: Ticker symbol
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            interval: Data interval (1d, 1wk, 1mo)

        Returns:
            DataFrame with Open, High, Low, Close and Volume columns
        """
        data = yf.download(
            ticker,
            start=start_date,
            end=end_date,
            interval=interval,
            auto_adjust=True,
            progress=False
        )
        return normalize_ohlcv(data, ticker)

    def fetch_ticker_info(self, ticker: str) -> Dict:
        """
        Fetch company/asset information.

        Args:
            ticker: Ticker symbol

        Returns:
            Dictionary with ticker information
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            return {
                'symbol': ticker,
                'name': info.get('longName', ticker),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'market_cap': info.get('marketCap', 0),
                'beta': info.get('beta', 1.0),
                'currency': info.get('currency', 'USD')
            }
        except Exception as e:
            logger.warning(f"Could not fetch info for {ticker}: {e}")
            return {
                'symbol': ticker,
                'name': ticker,
                'sector': 'Unknown',
                'industry': 'Unknown',
                'market_cap': 0,
                'beta': 1.0,
                'currency': 'USD'
            }

    def fetch_all_info(self, tickers: List[str]) -> pd.DataFrame:
        """
        Fetch information for all tickers.

        Args:
            tickers: List of ticker symbols

        Returns:
            DataFrame with ticker information
        """
        info_list = []
        for ticker in tickers:
            info_list.append(self.fetch_ticker_info(ticker))

        return pd.DataFrame(info_list).set_index('symbol')

    def _get_cache_path(
        self,
        tickers: List[str],
        start_date: str,
        end_date: str,
        interval: str
    ) -> Path:
        """Generate cache file path."""
        tickers_str = "_".join(sorted(tickers))
        if len(tickers_str) > 50:
            # Use hash for long ticker lists
            import hashlib
            tickers_str = hashlib.md5(tickers_str.encode()).hexdigest()[:16]

        filename = f"{tickers_str}_{start_date}_{end_date}_{interval}.csv"
        return self.cache_dir / filename


class DataFetcher:
    """
    Unified data fetcher supporting multiple data sources.
    """

    def __init__(self, primary_source: str = "yahoo", cache_dir: Optional[Path] = None):
        """
        Initialize data fetcher.

        Args:
            primary_source: Primary data source ('yahoo', 'alpha_vantage')
            cache_dir: Directory for caching data
        """
        self.primary_source = primary_source
        self.cache_dir = cache_dir or Path("data/raw")

        # Initialize fetchers
        self.yahoo = YahooFinanceFetcher(cache_dir=self.cache_dir)

    def get_prices(
        self,
        tickers: List[str],
        start_date: str,
        end_date: str,
        interval: str = "1d"
    ) -> pd.DataFrame:
        """
        Get price data using the primary source.

        Args:
            tickers: List of ticker symbols
            start_date: Start date
            end_date: End date
            interval: Data interval

        Returns:
            DataFrame of prices
        """
        if self.primary_source == "yahoo":
            return self.yahoo.fetch_prices(tickers, start_date, end_date, interval)
        else:
            raise ValueError(f"Unsupported data source: {self.primary_source}")

    def get_ohlcv(
        self,
        ticker: str,
        start_date: str,
        end_date: str,
        interval: str = "1d"
    ) -> pd.DataFrame:
        """
        Get daily bars (Open, High, Low, Close, Volume) for one ticker.
        """
        if self.primary_source == "yahoo":
            return self.yahoo.fetch_ohlcv(ticker, start_date, end_date, interval)
        else:
            raise ValueError(f"Unsupported data source: {self.primary_source}")

    def get_returns(
        self,
        tickers: List[str],
        start_date: str,
        end_date: str,
        interval: str = "1d",
        log_returns: bool = True
    ) -> pd.DataFrame:
        """
        Get returns data.

        Args:
            tickers: List of ticker symbols
            start_date: Start date
            end_date: End date
            interval: Data interval
            log_returns: Use log returns

        Returns:
            DataFrame of returns
        """
        if self.primary_source == "yahoo":
            return self.yahoo.fetch_returns(tickers, start_date, end_date, interval, log_returns)
        else:
            raise ValueError(f"Unsupported data source: {self.primary_source}")

    def get_info(self, tickers: List[str]) -> pd.DataFrame:
        """
        Get ticker information.

        Args:
            tickers: List of ticker symbols

        Returns:
            DataFrame with ticker information
        """
        if self.primary_source == "yahoo":
            return self.yahoo.fetch_all_info(tickers)
        else:
            raise ValueError(f"Unsupported data source: {self.primary_source}")


OHLCV_COLUMNS = ["Open", "High", "Low", "Close", "Volume"]


def normalize_ohlcv(data: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """
    Return a single ticker's bars with flat Open/High/Low/Close/Volume columns.

    Recent yfinance versions return (field, ticker) MultiIndex columns even for
    one ticker; older versions return flat field columns.
    """
    if isinstance(data.columns, pd.MultiIndex):
        level = 1 if ticker in data.columns.get_level_values(1) else 0
        data = data.xs(ticker, axis=1, level=level)

    missing = [c for c in OHLCV_COLUMNS if c not in data.columns]
    if missing:
        raise ValueError(f"{ticker}: missing columns {missing}")

    return data[OHLCV_COLUMNS].dropna()


def load_tickers_from_config(config_file: Path, portfolio_name: str = "small_portfolio") -> List[str]:
    """
    Load ticker list from configuration file.

    Args:
        config_file: Path to assets.yaml configuration
        portfolio_name: Name of portfolio in config

    Returns:
        List of ticker symbols
    """
    import yaml

    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)

    portfolio = config.get(portfolio_name, {})
    tickers = portfolio.get('tickers', [])

    if not tickers:
        raise ValueError(f"No tickers found for portfolio: {portfolio_name}")

    return tickers


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Initialize fetcher
    fetcher = DataFetcher(primary_source="yahoo")

    # Test with a few tickers
    tickers = ['AAPL', 'MSFT', 'GOOGL']
    start = "2020-01-01"
    end = "2024-01-01"

    # Fetch prices
    print("Fetching prices...")
    prices = fetcher.get_prices(tickers, start, end)
    print(f"\nPrices shape: {prices.shape}")
    print(prices.head())

    # Fetch returns
    print("\nFetching returns...")
    returns = fetcher.get_returns(tickers, start, end, log_returns=True)
    print(f"\nReturns shape: {returns.shape}")
    print(returns.head())

    # Fetch info
    print("\nFetching ticker info...")
    info = fetcher.get_info(tickers)
    print(info)
