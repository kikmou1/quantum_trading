# Changelog

All notable changes to this project are documented here. The format is based
on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.1.0] - 2026-09-27

First tagged release.

### Fixed
- Classical optimizers passed returns to PyPortfolioOpt functions that expect
  prices. Mean-Variance, Maximum Sharpe, and Target Return crashed, and
  Minimum Variance, Risk Parity, and Black-Litterman used a wrong covariance
  matrix. They now pass `returns_data=True`.
- Risk Parity imported `RiskParityOpt`, which does not exist in
  PyPortfolioOpt, so the whole classical optimizer module failed to import.
  Risk Parity is now solved directly with SciPy and has a test that checks
  equal risk contributions.
- Black-Litterman passed portfolio weights as the prior returns and crashed
  without views. It now uses market-implied equilibrium returns and accepts
  optional absolute views.
- Maximum Sharpe falls back to Minimum Variance when no asset is expected to
  beat the risk-free rate, instead of failing.
- Short positions in the virtual portfolio were accounted like longs, so a
  profitable short reduced cash and equity.
- `DataPreprocessor.clean_prices` checked minimum history after filling gaps,
  so assets with too little data were never removed.
- `run_backtest.py` compounded log returns as if they were simple returns. It
  now uses simple returns.
- Replaced `fillna(method=...)`, which was removed in pandas 3.
- Hierarchical Risk Parity crashed with SciPy 1.18, because PyPortfolioOpt
  reads a private SciPy attribute that was removed. Added a compatibility
  shim. The `linkage_method` argument is now passed through instead of
  being ignored.
- The QAOA optimizer imported `qiskit.primitives.Sampler`, which was removed
  in Qiskit 2.0, so it was disabled even with Qiskit installed.

### Added
- `qiskit-algorithms` in `requirements.txt`.
- `requirements-core.txt` for a lightweight install without quantum SDKs.
- Test suite (`tests/`) for metrics, optimizers, the backtest engine,
  preprocessing, and the virtual portfolio.
- GitHub Actions CI on Python 3.10–3.12.
- Offline, reproducible example: `examples/synthetic_backtest.py`.
- MIT license, contributing guide, changelog, issue and pull request templates.
- Documented limitations of the backtests and of the quantum-inspired methods.

[Unreleased]: https://github.com/kikmou1/quantum_trading/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/kikmou1/quantum_trading/releases/tag/v0.1.0
