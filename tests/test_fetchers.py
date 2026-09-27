import pandas as pd
import pytest

from data_collection.fetchers import OHLCV_COLUMNS, normalize_ohlcv

DATES = pd.bdate_range("2024-01-01", periods=3)


def bars():
    return pd.DataFrame(
        {
            "Close": [10.0, 11.0, 12.0],
            "High": [10.5, 11.5, 12.5],
            "Low": [9.5, 10.5, 11.5],
            "Open": [10.0, 10.8, 11.9],
            "Volume": [100, 200, 300],
        },
        index=DATES,
    )


def test_flat_columns_are_reordered():
    result = normalize_ohlcv(bars(), "XYZ")
    assert list(result.columns) == OHLCV_COLUMNS


def test_multiindex_field_ticker_columns_are_flattened():
    # Layout of recent yfinance versions: (field, ticker)
    data = bars()
    data.columns = pd.MultiIndex.from_product([data.columns, ["XYZ"]])
    result = normalize_ohlcv(data, "XYZ")
    assert list(result.columns) == OHLCV_COLUMNS
    assert result["Close"].tolist() == [10.0, 11.0, 12.0]
    assert isinstance(result["Close"], pd.Series)


def test_multiindex_ticker_field_columns_are_flattened():
    # Layout when grouping by ticker: (ticker, field)
    data = bars()
    data.columns = pd.MultiIndex.from_product([["XYZ"], data.columns])
    result = normalize_ohlcv(data, "XYZ")
    assert result["High"].tolist() == [10.5, 11.5, 12.5]


def test_rows_with_missing_values_are_dropped():
    data = bars()
    data.loc[DATES[1], "Close"] = float("nan")
    assert len(normalize_ohlcv(data, "XYZ")) == 2


def test_missing_columns_raise():
    with pytest.raises(ValueError):
        normalize_ohlcv(bars().drop(columns="Volume"), "XYZ")
