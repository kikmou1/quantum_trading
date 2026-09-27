import numpy as np
import pandas as pd
import pytest

from metrics.performance import PerformanceMetrics
from metrics.risk import RiskMetrics


def test_total_return_compounds():
    r = pd.Series([0.10, -0.10, 0.05])
    assert PerformanceMetrics().total_return(r) == pytest.approx(1.1 * 0.9 * 1.05 - 1)


def test_annualized_return_of_one_year_equals_total_return():
    r = pd.Series([0.001] * 252)
    pm = PerformanceMetrics(periods_per_year=252)
    assert pm.annualized_return(r) == pytest.approx(pm.total_return(r))


def test_maximum_drawdown_known_path():
    # Value path: 1.0 -> 1.2 -> 0.9 -> 1.08, peak 1.2, trough 0.9
    r = pd.Series([0.2, -0.25, 0.2])
    assert PerformanceMetrics().maximum_drawdown(r) == pytest.approx(-0.25)


def test_sharpe_ratio_matches_definition(returns):
    pm = PerformanceMetrics(risk_free_rate=0.02)
    r = returns["B"]
    expected = (pm.annualized_return(r) - 0.02) / (r.std() * np.sqrt(252))
    assert pm.sharpe_ratio(r) == pytest.approx(expected)


def test_sharpe_ratio_zero_volatility_returns_zero():
    assert PerformanceMetrics().sharpe_ratio(pd.Series([0.0] * 10)) == 0.0


def test_win_rate():
    r = pd.Series([0.01, -0.01, 0.02, 0.0])
    assert PerformanceMetrics().win_rate(r) == pytest.approx(0.5)


def test_historical_var_is_loss_quantile():
    r = pd.Series(np.linspace(-0.05, 0.05, 101))
    var = RiskMetrics(confidence_level=0.95).value_at_risk(r, method="historical")
    assert var == pytest.approx(abs(r.quantile(0.05)))


def test_cvar_is_at_least_var(returns):
    rm = RiskMetrics(confidence_level=0.95)
    r = returns["E"]
    assert rm.conditional_var(r) >= rm.value_at_risk(r)


def test_max_consecutive_losses():
    r = pd.Series([0.01, -0.01, -0.02, -0.01, 0.03, -0.01])
    assert RiskMetrics().max_consecutive_losses(r) == 3
