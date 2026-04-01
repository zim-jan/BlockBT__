import numpy as np
import pandas as pd
import pytest

from app.services.engine.indicators import IndicatorService
from app.services.engine.opensource_engine import OpenSourceEngine


@pytest.fixture
def sample_close():
    # 100 dni po cenie
    dates = pd.date_range("2024-01-01", periods=100)
    # Zaczynamy od 100 i trochę fluktuujemy
    np.random.seed(42)
    prices = 100 + np.cumsum(np.random.randn(100))
    return pd.Series(prices, index=dates, name="close")


@pytest.fixture
def sample_ohlcv(sample_close):
    df = pd.DataFrame(index=sample_close.index)
    df["close"] = sample_close
    df["open"] = sample_close
    df["high"] = sample_close + 1
    df["low"] = sample_close - 1
    df["volume"] = 1000
    return df


def test_indicator_service_sma_fallback(sample_close):
    import vectorbt as vbt

    service = IndicatorService()
    params = {"sma_fast": 5, "sma_slow": 10}

    entries, exits = service.generate_signals(sample_close, params, vbt)

    assert isinstance(entries, pd.Series)
    assert isinstance(exits, pd.Series)
    assert entries.dtype == bool
    assert exits.dtype == bool
    assert len(entries) == len(sample_close)


def test_opensource_engine_run_backtest(sample_ohlcv):
    engine = OpenSourceEngine()
    params = {"sma_fast": 5, "sma_slow": 10, "initial_capital": 10000}

    result = engine.run_backtest(sample_ohlcv, params)

    assert isinstance(result, dict)
    assert result["engine_name"] == "opensource"
    assert "total_return_pct" in result
    assert "sharpe_ratio" in result
    assert "max_drawdown_pct" in result
    assert result["initial_capital"] == 10000
