import numpy as np
import pandas as pd
import pytest

from optimizers.classical.portfolio_optimizers import (
    BlackLittermanOptimizer,
    EqualWeightOptimizer,
    HierarchicalRiskParityOptimizer,
    MaximumSharpeOptimizer,
    MeanVarianceOptimizer,
    MinimumVarianceOptimizer,
    RiskParityOptimizer,
    TargetReturnOptimizer,
)
from optimizers.quantum_inspired import qaoa_optimizer, quantum_annealing

CLASSICAL = [
    EqualWeightOptimizer,
    MeanVarianceOptimizer,
    MinimumVarianceOptimizer,
    MaximumSharpeOptimizer,
    HierarchicalRiskParityOptimizer,
    RiskParityOptimizer,
    BlackLittermanOptimizer,
    TargetReturnOptimizer,
]


def portfolio_vol(weights, returns):
    w = weights.reindex(returns.columns).fillna(0).values
    return np.sqrt(w @ returns.cov().values @ w)


@pytest.mark.parametrize("optimizer_cls", CLASSICAL, ids=lambda c: c.__name__)
def test_classical_weights_are_long_only_and_fully_invested(optimizer_cls, returns):
    weights = optimizer_cls().optimize(returns)
    assert set(weights.index) == set(returns.columns)
    assert weights.sum() == pytest.approx(1.0, abs=1e-4)
    assert (weights >= -1e-6).all()


def test_minimum_variance_beats_equal_weight(returns):
    w_mv = MinimumVarianceOptimizer().optimize(returns)
    w_eq = EqualWeightOptimizer().optimize(returns)
    assert portfolio_vol(w_mv, returns) < portfolio_vol(w_eq, returns)


def test_minimum_variance_favours_low_volatility_asset(returns):
    weights = MinimumVarianceOptimizer().optimize(returns)
    assert weights.idxmax() == "A"


def test_risk_parity_equalizes_risk_contributions(returns):
    weights = RiskParityOptimizer().optimize(returns).reindex(returns.columns).values
    cov = returns.cov().values
    contributions = weights * (cov @ weights)
    contributions /= contributions.sum()
    np.testing.assert_allclose(contributions, 1 / len(weights), atol=1e-3)


def test_black_litterman_without_views_returns_market_portfolio(returns):
    caps = {"A": 5, "B": 4, "C": 3, "D": 2, "E": 1}
    weights = BlackLittermanOptimizer(market_caps=caps).optimize(returns)
    expected = pd.Series(caps) / sum(caps.values())
    pd.testing.assert_series_equal(
        weights.reindex(expected.index), expected, check_names=False, atol=1e-3
    )


def test_black_litterman_bullish_view_increases_weight(returns):
    base = BlackLittermanOptimizer().optimize(returns)
    tilted = BlackLittermanOptimizer(views={"C": 0.5}).optimize(returns)
    assert tilted["C"] > base["C"]


def test_qaoa_continuous_weights_are_valid(returns):
    weights = qaoa_optimizer.QAOAContinuousOptimizer().optimize(returns)
    assert weights.sum() == pytest.approx(1.0, abs=1e-6)
    assert (weights >= -1e-9).all()


def test_hybrid_annealing_weights_are_valid(returns):
    weights = quantum_annealing.HybridAnnealingOptimizer(num_reads=20).optimize(returns)
    assert weights.sum() == pytest.approx(1.0, abs=1e-6)
    assert (weights >= -1e-9).all()


@pytest.mark.skipif(not qaoa_optimizer.QISKIT_AVAILABLE, reason="Qiskit not installed")
def test_qaoa_selects_subset_with_equal_weights(returns):
    np.random.seed(0)
    weights = qaoa_optimizer.QAOAPortfolioOptimizer().optimize(returns)
    selected = weights[weights > 0]
    assert weights.sum() == pytest.approx(1.0)
    np.testing.assert_allclose(selected.values, 1 / len(selected))


@pytest.mark.skipif(not quantum_annealing.DWAVE_AVAILABLE, reason="D-Wave Ocean not installed")
def test_quantum_annealing_weights_are_valid(returns):
    weights = quantum_annealing.QuantumAnnealingOptimizer(num_reads=20).optimize(returns)
    assert weights.sum() == pytest.approx(1.0)
    assert (weights >= 0).all()


def test_maximum_sharpe_falls_back_when_nothing_beats_risk_free(returns):
    optimizer = MaximumSharpeOptimizer(risk_free_rate=10.0)
    weights = optimizer.optimize(returns)
    assert weights.sum() == pytest.approx(1.0, abs=1e-4)
    assert optimizer.metadata["fallback"] == "minimum_variance"
