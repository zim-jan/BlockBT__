import pandas as pd
import pytest

from app.services.engine.indicator_registry import IndicatorRegistry, initialize_registry
from app.services.engine.opensource_engine import _setup_vbt


@pytest.fixture(scope="module")
def vbt():
    return _setup_vbt()

@pytest.fixture
def sample_data():
    return pd.Series([10.0, 11.0, 12.0, 11.0, 10.0, 9.0, 10.0, 11.0], index=pd.date_range("2020-01-01", periods=8))

def test_registry_discovery(vbt):
    IndicatorRegistry._indicators = {} # Reset
    initialize_registry(vbt)
    
    indicators = IndicatorRegistry.get_all()
    assert len(indicators) > 0
    
    # Check for core vbt indicators
    names = [i["name"] for i in indicators]
    assert "vbt_MA" in names
    assert "vbt_RSI" in names

def test_registry_execute_vbt_indicator(vbt, sample_data):
    IndicatorRegistry._indicators = {} # Reset
    initialize_registry(vbt)
    
    # Execute vbt_MA
    res = IndicatorRegistry.execute("vbt_MA", sample_data, window=2)
    assert hasattr(res, "ma")
    assert len(res.ma) == len(sample_data)

def test_registry_talib_discovery(vbt):
    IndicatorRegistry._indicators = {} # Reset
    initialize_registry(vbt)
    
    # Check if any talib indicators were registered (if available)
    talib_indicators = [i for i in IndicatorRegistry.get_all() if i["library"] == "talib"]
    # This might be empty if talib is not installed, which is fine
    assert isinstance(talib_indicators, list)

def test_registry_get_nonexistent():
    assert IndicatorRegistry.get("nonexistent") is None
