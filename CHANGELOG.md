# Changelog

All notable changes to this project are documented here. The format is based
on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Fixed
- `trading_simulator.py` crashed on its first trading day because the
  signal generators received closing prices only. It now downloads full
  daily bars (`DataFetcher.get_ohlcv`).
- The dashboard's trade simulation failed whenever a signal was generated,
  because yfinance's two-level column headers turned prices into Series.
  Bars are now flattened on load (`normalize_ohlcv`).
- `run_backtest.py` reported the worst drawdown as the "lowest drawdown",
  and compared quantum-inspired and classical Sharpe ratios as a ratio. It
  now reports the least severe drawdown and the Sharpe difference.
- The trading simulator ran each day's next five days of prices through the
  portfolio before simulating the following day, so later decisions depended
  on future prices. Each day now only marks positions to its own close.
- Alpha, beta and information ratio were always empty because the benchmark
  was never passed to the metrics. They are now computed against SPY.
- Backtest metrics included the lookback period before the first allocation,
  when the portfolio holds only cash. They now start at the first allocation.

### Changed
- `requirements.txt` lists only packages the code imports. It dropped about
  20 unused ones, including PyTorch, PennyLane, vectorbt, backtrader and
  pandas-ta, so the full install takes seconds instead of many minutes.
- Removed config settings that nothing reads (walk-forward analysis, VQE,
  statistical tests, parallel runs and others) and the `large_portfolio`
  universe, which had no tickers.
- Replaced `QUICKSTART.md`, `README_BACKTEST.md`,
  `TRADING_SIMULATOR_README.md` and `DASHBOARD_GUIDE.md`, which described
  features that do not exist and showed invented output, with the README and
  two guides in `docs/`. Moved the planning and background notes to
  `docs/notes/`, labeled as notes.
- Plain-text console and dashboard output.

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
