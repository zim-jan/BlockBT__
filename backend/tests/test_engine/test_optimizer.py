import numpy as np
import pandas as pd
import pytest

from app.services.engine.opensource_engine import OpenSourceEngine
from app.services.engine.optimizer import GridSearchOptimizer


def indicator_layer(data, **kwargs):
    # Retrieve vectorbt via engine to simulate real scenario
    import vectorbt as vbt

    close = data["close"]
    fast = kwargs.get("sma_fast", [10])
    slow = kwargs.get("sma_slow", [30])

    fast_ma = vbt.MA.run(close, window=fast).ma
    slow_ma = vbt.MA.run(close, window=slow).ma

    entries = fast_ma.vbt.crossed_above(slow_ma)
    exits = fast_ma.vbt.crossed_below(slow_ma)

    return entries, exits


@pytest.fixture
def dummy_data():
    np.random.seed(42)
    # 100 periods of synthetic data
    prices = np.random.normal(0, 1, 100).cumsum() + 100
    dates = pd.date_range("2020-01-01", periods=100, freq="D")
    df = pd.DataFrame({"close": prices}, index=dates)
    return df


def test_grid_search_optimizer_basic(dummy_data):
    """
    Test that GridSearchOptimizer correctly evaluates a grid of parameters
    and returns the best combination without shape errors.
    """
    engine = OpenSourceEngine()
    optimizer = GridSearchOptimizer(engine=engine, indicator_layer=indicator_layer)

    param_grid = {
        "sma_fast": [5, 10],
        "sma_slow": [20, 50],
    }

    results = optimizer.optimize(dummy_data, param_grid, metric="Total Return [%]")

    assert results is not None
    assert len(results) == 4
    
    # Best result is first
    best_result = results[0]
    assert "parameters" in best_result
    assert "metrics" in best_result
    
    best_params = best_result["parameters"]
    assert "sma_fast" in best_params
    assert "sma_slow" in best_params

    # Check if best_params is one of our combinations
    assert best_params["sma_fast"] in [5, 10]
    assert best_params["sma_slow"] in [20, 50]


def test_grid_search_optimizer_empty_grid(dummy_data):
    """
    Test that an empty param grid is handled gracefully.
    """
    engine = OpenSourceEngine()
    optimizer = GridSearchOptimizer(engine=engine, indicator_layer=indicator_layer)

    result = optimizer.optimize(dummy_data, {}, metric="Total Return [%]")

    assert result == []
