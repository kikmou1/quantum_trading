"""
Shared test fixtures.

The project modules are imported the same way the entry-point scripts do it:
`src/` is put on sys.path, and the optimizer modules additionally expect
`src/optimizers/` on the path for `from base import BaseOptimizer`.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "src" / "optimizers"))


@pytest.fixture
def returns():
    """Deterministic daily returns for 5 assets with different volatilities."""
    rng = np.random.default_rng(42)
    dates = pd.bdate_range("2020-01-01", periods=600)
    vols = np.array([0.005, 0.01, 0.015, 0.02, 0.025])
    data = rng.normal(0.0004, 1.0, (len(dates), len(vols))) * vols
    return pd.DataFrame(data, index=dates, columns=["A", "B", "C", "D", "E"])
