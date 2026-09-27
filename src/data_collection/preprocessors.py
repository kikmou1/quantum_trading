"""
Data preprocessing and cleaning module.
Handles missing data, outliers, and data quality issues.
"""

import pandas as pd
import numpy as np
from typing import Optional, Tuple, List
import logging
from scipy import stats

logger = logging.getLogger(__name__)


class DataPreprocessor:
    """
    Clean and preprocess financial data.
    """

    def __init__(self, min_history: int = 126):
        """
        Initialize preprocessor.

        Args:
            min_history: Minimum number of observations required per asset
        """
        self.min_history = min_history

    def clean_prices(
        self,
        prices: pd.DataFrame,
        handle_missing: str = "forward_fill",
        remove_zero: bool = True,
        min_price: float = 0.01
    ) -> pd.DataFrame:
        """
        Clean price data.

        Args:
            prices: DataFrame of prices
            handle_missing: Method to handle missing values
                           ('forward_fill', 'drop', 'interpolate')
            remove_zero: Remove zero or near-zero prices
            min_price: Minimum valid price

        Returns:
            Cleaned price DataFrame
        """
        prices_clean = prices.copy()

        # Remove zero or near-zero prices
        if remove_zero:
            prices_clean = prices_clean.replace(0, np.nan)
            prices_clean = prices_clean[prices_clean > min_price]

        # Count real observations before filling, otherwise every asset
        # would look like it has full history
        valid_assets = (prices_clean.count() >= self.min_history)

        # Handle missing values
        if handle_missing == "forward_fill":
            prices_clean = prices_clean.ffill()
            prices_clean = prices_clean.bfill()
        elif handle_missing == "interpolate":
            prices_clean = prices_clean.interpolate(method='linear')
        elif handle_missing == "drop":
            prices_clean = prices_clean.dropna()

        # Remove assets with insufficient history
        prices_clean = prices_clean.loc[:, valid_assets]

        removed = set(prices.columns) - set(prices_clean.columns)
        if removed:
            logger.warning(f"Removed {len(removed)} assets due to insufficient data: {removed}")

        return prices_clean

    def clean_returns(
        self,
        returns: pd.DataFrame,
        handle_missing: str = "zero_fill",
        remove_outliers: bool = True,
        outlier_std: float = 5.0
    ) -> pd.DataFrame:
        """
        Clean returns data.

        Args:
            returns: DataFrame of returns
            handle_missing: Method to handle missing values
                           ('zero_fill', 'drop', 'forward_fill')
            remove_outliers: Remove statistical outliers
            outlier_std: Number of standard deviations for outlier detection

        Returns:
            Cleaned returns DataFrame
        """
        returns_clean = returns.copy()

        # Handle infinite values
        returns_clean = returns_clean.replace([np.inf, -np.inf], np.nan)

        # Remove outliers
        if remove_outliers:
            for col in returns_clean.columns:
                mean = returns_clean[col].mean()
                std = returns_clean[col].std()
                lower_bound = mean - outlier_std * std
                upper_bound = mean + outlier_std * std

                outliers = (returns_clean[col] < lower_bound) | (returns_clean[col] > upper_bound)
                n_outliers = outliers.sum()

                if n_outliers > 0:
                    logger.debug(f"Replacing {n_outliers} outliers in {col}")
                    returns_clean.loc[outliers, col] = np.nan

        # Handle missing values
        if handle_missing == "zero_fill":
            returns_clean = returns_clean.fillna(0)
        elif handle_missing == "forward_fill":
            returns_clean = returns_clean.ffill()
            returns_clean = returns_clean.fillna(0)
        elif handle_missing == "drop":
            returns_clean = returns_clean.dropna()

        # Remove assets with insufficient history
        valid_assets = (returns_clean.count() >= self.min_history)
        returns_clean = returns_clean.loc[:, valid_assets]

        return returns_clean

    def calculate_returns(
        self,
        prices: pd.DataFrame,
        method: str = "log",
        periods: int = 1
    ) -> pd.DataFrame:
        """
        Calculate returns from prices.

        Args:
            prices: DataFrame of prices
            method: 'log' for log returns, 'simple' for simple returns
            periods: Number of periods for return calculation

        Returns:
            DataFrame of returns
        """
        if method == "log":
            returns = np.log(prices / prices.shift(periods))
        elif method == "simple":
            returns = prices.pct_change(periods=periods)
        else:
            raise ValueError(f"Unknown method: {method}")

        return returns.dropna(how='all')

    def detect_splits_and_dividends(
        self,
        prices: pd.DataFrame,
        threshold: float = 0.25
    ) -> pd.DataFrame:
        """
        Detect potential stock splits and dividend payments.

        Args:
            prices: DataFrame of prices
            threshold: Threshold for detecting splits (25% change)

        Returns:
            DataFrame with split/dividend events
        """
        returns = prices.pct_change()
        events = []

        for col in prices.columns:
            large_changes = returns[col].abs() > threshold
            if large_changes.any():
                dates = returns[large_changes].index
                for date in dates:
                    events.append({
                        'ticker': col,
                        'date': date,
                        'return': returns.loc[date, col],
                        'type': 'split' if returns.loc[date, col] < -threshold else 'unknown'
                    })

        return pd.DataFrame(events)

    def align_data(
        self,
        *dataframes: pd.DataFrame,
        method: str = "inner"
    ) -> List[pd.DataFrame]:
        """
        Align multiple DataFrames to have the same index and columns.

        Args:
            dataframes: Variable number of DataFrames to align
            method: 'inner' (intersection) or 'outer' (union)

        Returns:
            List of aligned DataFrames
        """
        if not dataframes:
            return []

        # Find common index
        if method == "inner":
            common_index = dataframes[0].index
            for df in dataframes[1:]:
                common_index = common_index.intersection(df.index)
        else:
            common_index = dataframes[0].index
            for df in dataframes[1:]:
                common_index = common_index.union(df.index)

        # Find common columns
        if method == "inner":
            common_columns = set(dataframes[0].columns)
            for df in dataframes[1:]:
                common_columns = common_columns.intersection(set(df.columns))
            common_columns = sorted(list(common_columns))
        else:
            common_columns = set()
            for df in dataframes:
                common_columns = common_columns.union(set(df.columns))
            common_columns = sorted(list(common_columns))

        # Align all dataframes
        aligned = []
        for df in dataframes:
            df_aligned = df.reindex(index=common_index, columns=common_columns)
            aligned.append(df_aligned)

        return aligned

    def train_test_split(
        self,
        data: pd.DataFrame,
        train_ratio: float = 0.7,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Split data into train, validation, and test sets.

        Args:
            data: DataFrame to split
            train_ratio: Proportion for training
            val_ratio: Proportion for validation
            test_ratio: Proportion for testing

        Returns:
            Tuple of (train, val, test) DataFrames
        """
        assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6, \
            "Ratios must sum to 1"

        n = len(data)
        train_end = int(n * train_ratio)
        val_end = int(n * (train_ratio + val_ratio))

        train = data.iloc[:train_end]
        val = data.iloc[train_end:val_end]
        test = data.iloc[val_end:]

        logger.info(f"Split data: Train={len(train)}, Val={len(val)}, Test={len(test)}")

        return train, val, test

    def winsorize_returns(
        self,
        returns: pd.DataFrame,
        limits: Tuple[float, float] = (0.01, 0.01)
    ) -> pd.DataFrame:
        """
        Winsorize returns to handle extreme outliers.

        Args:
            returns: DataFrame of returns
            limits: Lower and upper percentile limits (e.g., (0.01, 0.01) for 1%)

        Returns:
            Winsorized returns DataFrame
        """
        returns_winsorized = returns.copy()

        for col in returns.columns:
            returns_winsorized[col] = stats.mstats.winsorize(
                returns[col],
                limits=limits
            )

        return returns_winsorized

    def get_data_quality_report(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate data quality report.

        Args:
            data: DataFrame to analyze

        Returns:
            DataFrame with quality metrics
        """
        report = []

        for col in data.columns:
            series = data[col]

            report.append({
                'asset': col,
                'count': series.count(),
                'missing': series.isna().sum(),
                'missing_pct': series.isna().sum() / len(series) * 100,
                'zeros': (series == 0).sum(),
                'min': series.min(),
                'max': series.max(),
                'mean': series.mean(),
                'std': series.std(),
                'skew': series.skew(),
                'kurtosis': series.kurtosis()
            })

        return pd.DataFrame(report)


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Create sample data
    dates = pd.date_range('2020-01-01', '2022-01-01', freq='D')
    prices = pd.DataFrame({
        'AAPL': np.random.randn(len(dates)).cumsum() + 100,
        'MSFT': np.random.randn(len(dates)).cumsum() + 150,
        'GOOGL': np.random.randn(len(dates)).cumsum() + 2000
    }, index=dates)

    # Add some missing values
    prices.iloc[10:15, 0] = np.nan
    prices.iloc[20:23, 1] = np.nan

    # Preprocess
    preprocessor = DataPreprocessor(min_history=50)
    prices_clean = preprocessor.clean_prices(prices)

    print("Original shape:", prices.shape)
    print("Cleaned shape:", prices_clean.shape)

    # Get quality report
    report = preprocessor.get_data_quality_report(prices_clean)
    print("\nData Quality Report:")
    print(report)
