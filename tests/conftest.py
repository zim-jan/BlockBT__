"""
Tests conftest — shared fixtures for the BlockBT test suite.
"""

from __future__ import annotations

import os

# Set a dummy SECRET_KEY so imports won't fail globally during pytest collection
os.environ["SECRET_KEY"] = "yNmj9oJp0YJXY7vWvJ0M2bI-W3k6U_X1qR5u7M_fA-Q="

import pandas as pd
import pytest

from blockbt.db.session import drop_db, init_db

# ---------------------------------------------------------------------------
# Database fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def db_session(tmp_path, monkeypatch):
    """Provide an isolated in-memory SQLite session per test function.

    Uses a nested SAVEPOINT so that tests which intentionally trigger
    IntegrityError (or any rollback) don't leave the outer session in a
    broken state at teardown.
    """
    db_url = f"sqlite:///{tmp_path}/test_blockbt.db"
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("SECRET_KEY", "yNmj9oJp0YJXY7vWvJ0M2bI-W3k6U_X1qR5u7M_fA-Q=")

    from importlib import reload

    import blockbt.config as cfg_mod

    reload(cfg_mod)
    from blockbt.config import settings

    settings.DATA_DIR.mkdir(parents=True, exist_ok=True)

    import blockbt.db.session as sess_mod

    reload(sess_mod)

    init_db()

    # Start outer transaction
    connection = sess_mod._engine.connect()
    transaction = connection.begin()

    from sqlalchemy.orm import Session

    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()
    drop_db()


# ---------------------------------------------------------------------------
# Data / DataFrame fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def sample_ohlcv() -> pd.DataFrame:
    """Minimal OHLCV DataFrame (100 daily bars) for engine / connector tests."""
    import numpy as np

    n = 100
    rng = np.random.default_rng(0)
    dates = pd.date_range("2023-01-01", periods=n, freq="D")
    close = 100.0 * (1 + rng.normal(0, 0.01, n)).cumprod()
    return pd.DataFrame(
        {
            "open":   close * (1 + rng.uniform(-0.005, 0.005, n)),
            "high":   close * (1 + rng.uniform(0, 0.01, n)),
            "low":    close * (1 - rng.uniform(0, 0.01, n)),
            "close":  close,
            "volume": rng.integers(1_000_000, 10_000_000, n).astype(float),
        },
        index=dates,
    )


@pytest.fixture()
def minimal_params() -> dict:
    """Minimal wizard_state params dict for engine run tests."""
    return {
        "symbol": "TEST",
        "timeframe": "1d",
        "initial_capital": 10_000.0,
        "indicators": [
            {"type": "SMA", "params": {"window": 10}},
            {"type": "SMA", "params": {"window": 30}},
        ],
        "fees": {"commission_pct": 0.001},
    }
