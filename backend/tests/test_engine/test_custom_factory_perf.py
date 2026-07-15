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
    np.random.seed(42)  # deterministyczne dane → stabilny pomiar
    close = np.random.random(500_000).astype(np.float64)

    # Rozgrzewka — koszt kompilacji JIT poza pomiarem.
    factory.run(close[:1000])

    t0 = time.perf_counter()
    factory.run(close)
    t_jit = time.perf_counter() - t0

    t0 = time.perf_counter()
    _rolling_mean_py(close)
    t_py = time.perf_counter() - t0

    # Próg z marginesem: JIT musi być co najmniej 5× szybszy. Goły `t_jit < t_py`
    # bywał niestabilny — narzut vbt na wywołaniu potrafi zbliżyć czasy przy szumie.
    assert t_jit < t_py / 5, (
        f"JIT ({t_jit:.4f}s) nie ≥5× szybszy niż Python ({t_py:.4f}s)"
    )


# Kontrakt wyboru funkcji (Faza 11, #8 z code review): przy wielu funkcjach
# rdzeniem jest PIERWSZA funkcja najwyższego poziomu, kolejne są pomocnicze.
MULTI_FUNC_CODE = """
def main_indicator(close):
    return close * 2.0

def helper(close):
    return close + 999.0
"""


def test_first_function_is_the_core_not_last():
    """Regresja #8: dawniej brano ostatnią funkcję (`funcs[-1]`) → zły rdzeń."""
    factory = IndicatorService.compile_custom_indicator(MULTI_FUNC_CODE)
    close = np.array([1.0, 2.0, 3.0], dtype=np.float64)

    out = np.asarray(factory.run(close).out).ravel()

    # main_indicator → *2 = [2,4,6]; błąd (helper) dałby [1000,1001,1002].
    np.testing.assert_allclose(out, [2.0, 4.0, 6.0], rtol=1e-9)


# Kontrakt funkcji pomocniczych (code review #1): rdzeń MOŻE wołać helpera.
# Rozdzielone globals/locals w exec sprawiały, że helper był niewidoczny w
# `__globals__` rdzenia → `NameError` przy `.run()`. Ten test to wychwytuje.
CORE_CALLS_HELPER_CODE = """
def indicator(close):
    return _double(close) + 1.0

def _double(x):
    return x * 2.0
"""


def test_core_can_call_helper_function():
    """#1: rdzeń wołający funkcję pomocniczą liczy poprawnie (brak NameError)."""
    factory = IndicatorService.compile_custom_indicator(CORE_CALLS_HELPER_CODE)
    close = np.array([1.0, 2.0, 3.0], dtype=np.float64)

    out = np.asarray(factory.run(close).out).ravel()

    # indicator = _double(close) + 1 = close*2 + 1 = [3, 5, 7].
    np.testing.assert_allclose(out, [3.0, 5.0, 7.0], rtol=1e-9)
