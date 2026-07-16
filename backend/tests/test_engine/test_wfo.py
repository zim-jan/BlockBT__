import pandas as pd
import pytest

from app.services.engine.opensource_engine import OpenSourceEngine
from app.services.engine.optimizer import WalkForwardOptimizer


@pytest.fixture
def dummy_data():
    # Create 2 years of daily data
    dates = pd.date_range("2020-01-01", periods=730, freq="D")
    return pd.DataFrame({"close": pd.Series(range(730), dtype=float)}, index=dates)

def test_walk_forward_optimizer_basic(dummy_data):
    engine = OpenSourceEngine()
    optimizer = WalkForwardOptimizer(engine)
    
    params = {"sma_fast": 10, "sma_slow": 30}
    
    result = optimizer.run_wfo(
        dummy_data, 
        params, 
        window_size="365d", 
        step_size="90d"
    )
    
    assert result["status"] == "COMPLETED"
    assert "overall_metrics" in result
    assert result["window"] == "365d"
    assert result["step"] == "90d"

def test_walk_forward_optimizer_invalid_data():
    engine = OpenSourceEngine()
    optimizer = WalkForwardOptimizer(engine)
    
    with pytest.raises(KeyError):
        optimizer.run_wfo(pd.DataFrame(), {}, window_size="365d", step_size="90d")
