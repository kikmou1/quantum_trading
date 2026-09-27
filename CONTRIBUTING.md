# Contributing

Thanks for your interest in improving Quantum Trading. Bug reports, fixes,
new optimizers, and documentation improvements are all welcome.

## Development setup

```bash
git clone https://github.com/kikmou1/quantum_trading.git
cd quantum_trading
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements-core.txt ruff
```

Install `requirements.txt` instead if you work on the Qiskit or D-Wave code
or the dashboard.

## Before opening a pull request

```bash
ruff check .
pytest
python examples/synthetic_backtest.py
```

CI runs the same commands on Python 3.10–3.12, plus a job with the quantum
libraries installed.

## Guidelines

- Keep pull requests focused on one change.
- Add a test for each bug fix and new feature. Tests must not need network
  access: use synthetic data like the fixtures in `tests/conftest.py`.
- A new optimizer should subclass `BaseOptimizer` and return a `pd.Series` of
  weights indexed by ticker that sums to 1.
- Describe what a method actually does. For example, do not call a classical
  approximation "quantum" without saying it runs on classical hardware.
- Do not present backtest results as evidence of future performance.

## Reporting bugs

Open an issue using the bug report template. Include the command you ran,
the full error, and your Python and package versions.
