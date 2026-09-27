import numpy as np
import pandas as pd
import pytest

from data_collection.preprocessors import DataPreprocessor


def test_simple_and_log_returns():
    prices = pd.DataFrame({"X": [100.0, 110.0, 99.0]})
    pre = DataPreprocessor()
    simple = pre.calculate_returns(prices, method="simple")
    log = pre.calculate_returns(prices, method="log")
    np.testing.assert_allclose(simple["X"].values, [0.10, -0.10])
    np.testing.assert_allclose(log["X"].values, np.log([1.1, 0.9]))


def test_clean_prices_fills_gaps_and_drops_short_history():
    dates = pd.bdate_range("2021-01-01", periods=10)
    prices = pd.DataFrame(
        {
            "FULL": [1.0, 2.0, np.nan, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
            "SHORT": [np.nan] * 8 + [1.0, 2.0],
        },
        index=dates,
    )
    cleaned = DataPreprocessor(min_history=5).clean_prices(prices)
    assert list(cleaned.columns) == ["FULL"]
    assert cleaned["FULL"].iloc[2] == 2.0


def test_unknown_return_method_raises():
    with pytest.raises(ValueError):
        DataPreprocessor().calculate_returns(pd.DataFrame({"X": [1.0, 2.0]}), method="bogus")
