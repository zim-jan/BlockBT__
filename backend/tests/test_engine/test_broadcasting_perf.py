"""
Faza 10: testy wydajności/wektoryzacji broadcastingu multi-symbol.

Weryfikują, że backtest wielu tickerów wykonuje się przez wektoryzację po kolumnach
(macierze), a nie przez pętlę pythonową per symbol.
"""

import time

import numpy as np
import pandas as pd

from app.services.engine.opensource_engine import OpenSourceEngine


def _random_walk(n: int, seed: int, start: float = 100.0) -> np.ndarray:
    """Deterministyczny random-walk cen zamknięcia."""
    rng = np.random.default_rng(seed)
    return start + np.cumsum(rng.normal(0.0, 1.0, size=n))


def _make_long_df(symbols: list[str], n: int, seed_base: int = 0) -> pd.DataFrame:
    """Ramka LONG: wierszowy MultiIndex [symbol, date], kolumna 'close'."""
    dates = pd.date_range("2020-01-01", periods=n)
    frames = [
        pd.DataFrame({"close": _random_walk(n, seed=seed_base + i + 1)}, index=dates)
        for i in range(len(symbols))
    ]
    return pd.concat(frames, keys=symbols, names=["symbol", "date"])


def _dag(symbols) -> dict:
    return {
        "nodes": [
            {"id": "d1", "category": "DataIngestion", "type": "dataNode",
             "params": {"symbol": symbols, "timeframe": "1d"}},
            {"id": "i1", "category": "Indicators", "type": "indicatorNode",
             "params": {"indicatorType": "sma_crossover", "smaFast": 10, "smaSlow": 30}},
            {"id": "e1", "category": "Execution", "type": "executionNode",
             "params": {"init_cash": 10000.0}},
        ]
    }


def test_tensor_perf_scaling():
    """20 tickerów nie może skalować się liniowo wobec 1 (dowód wektoryzacji, nie pętli)."""
    engine = OpenSourceEngine()
    n = 1000

    df1 = _make_long_df(["S0"], n=n, seed_base=100)
    df20 = _make_long_df([f"S{i}" for i in range(20)], n=n, seed_base=200)

    # WARM-UP: kompilacja Numba JIT poza pomiarem czasu
    engine.run_dag_backtest(_make_long_df(["W0", "W1"], n=100), _dag(["W0", "W1"]))

    t0 = time.perf_counter()
    engine.run_dag_backtest(df1, _dag(["S0"]))
    t1 = time.perf_counter() - t0

    t0 = time.perf_counter()
    engine.run_dag_backtest(df20, _dag([f"S{i}" for i in range(20)]))
    t20 = time.perf_counter() - t0

    # Wektoryzacja: 20 symboli tanio, znacznie poniżej 20x kosztu jednego symbolu.
    assert t20 < max(0.5, 6 * t1), f"t20={t20:.4f}s vs t1={t1:.4f}s — podejrzenie pętli"
    assert t20 < 5.0, f"t20={t20:.4f}s przekracza budżet absolutny"


def test_tensor_no_row_loop_shape():
    """20 symboli o RÓŻNYCH danych → wszystkie w metrykach, wartości różnią się między symbolami."""
    engine = OpenSourceEngine()
    symbols = [f"S{i}" for i in range(20)]
    df = _make_long_df(symbols, n=300, seed_base=500)

    result = engine.run_dag_backtest(df, _dag(symbols))
    metrics = result["metrics"]

    assert len(metrics) == 20
    for sym in symbols:
        assert sym in metrics

    finals = [metrics[s]["Final Value"] for s in symbols]
    assert len(set(finals)) > 1, "różne dane per symbol powinny dać różne wyniki"
