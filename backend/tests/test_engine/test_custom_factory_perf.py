"""
Faza 11 — dowód działania Custom Factory + numba JIT (Filary 2 i 3).

Testy uzupełniające do `test_custom_factory.py` (kontrakt RED). Weryfikują, że
skompilowany wskaźnik faktycznie liczy poprawnie na tablicach numpy (`.run()`
uruchamia rdzeń `@njit`) oraz że ścieżka JIT daje realną „prędkość C" względem
czystego Pythona.
"""
import time

import numpy as np

from app.services.engine.indicators import IndicatorService

# Wskaźnik pętlowy w stylu numba (numpy in → numpy out). Rolling mean.
NUMBA_INDICATOR_CODE = """
def rolling_mean(close):
    n = close.shape[0]
    out = np.empty(n)
    window = 5
    acc = 0.0
    for i in range(n):
        acc += close[i]
        if i >= window:
            acc -= close[i - window]
        if i >= window - 1:
            out[i] = acc / window
        else:
            out[i] = np.nan
    return out
"""


def _rolling_mean_py(close: np.ndarray) -> np.ndarray:
    """Referencyjna implementacja w czystym Pythonie (bez JIT) do porównań."""
    n = close.shape[0]
    out = np.empty(n)
    window = 5
    acc = 0.0
    for i in range(n):
        acc += close[i]
        if i >= window:
            acc -= close[i - window]
        if i >= window - 1:
            out[i] = acc / window
        else:
            out[i] = np.nan
    return out


def test_compiled_indicator_runs_and_is_correct():
    """Fabryka nie tylko się buduje — `.run()` liczy poprawny wynik na numpy."""
    factory = IndicatorService.compile_custom_indicator(NUMBA_INDICATOR_CODE)
    assert getattr(factory, "run", None) is not None

    close = np.arange(1, 51, dtype=np.float64)  # 1..50
    result = factory.run(close)

    out = np.asarray(result.out).ravel()
    expected = _rolling_mean_py(close)

    # Porównanie ignorujące NaN z okresu rozbiegowego.
    mask = ~np.isnan(expected)
    np.testing.assert_allclose(out[mask], expected[mask], rtol=1e-9)


def test_njit_faster_than_pure_python():
    """
    Filar 3 („Prędkość C"): rdzeń @njit po rozgrzewce jest istotnie szybszy niż
    identyczna pętla w czystym Pythonie na dużej tablicy.
    """
    factory = IndicatorService.compile_custom_indicator(NUMBA_INDICATOR_CODE)
    close = np.random.random(500_000).astype(np.float64)

    # Rozgrzewka — koszt kompilacji JIT poza pomiarem.
    factory.run(close[:1000])

    t0 = time.perf_counter()
    factory.run(close)
    t_jit = time.perf_counter() - t0

    t0 = time.perf_counter()
    _rolling_mean_py(close)
    t_py = time.perf_counter() - t0

    # Konserwatywny próg — JIT powinien być wyraźnie szybszy niż pętla Pythona.
    assert t_jit < t_py, f"JIT ({t_jit:.4f}s) nie szybszy niż Python ({t_py:.4f}s)"
