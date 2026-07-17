import pytest

from app.services.engine.indicators import IndicatorService


def test_custom_indicator_compilation():
    custom_code = """
def custom_oscillator(close):
    return close / close.shift(1)
"""
    # Powinno skompilować przez @njit (wymaga implementacji)
    result = IndicatorService.compile_custom_indicator(custom_code)
    assert result is not None
    assert getattr(result, "run", None) is not None

def test_custom_indicator_sandbox_security():
    malicious_code = "import os; os.system('echo hacked')"
    with pytest.raises(ValueError, match="Unsafe code detected"):
        IndicatorService.compile_custom_indicator(malicious_code)
