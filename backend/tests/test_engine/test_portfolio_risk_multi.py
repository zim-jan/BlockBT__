"""Review-backlog 2026-07-15: multi-symbol surfacing liczników wyjść SL/TP.

Cięcie Fazy 12 (ADR-0003): `_count_stop_exits` działał tylko dla single-symbol.
Kontrakt: gałąź multi-symbol (`is_multi_symbol=True`, Faza 10) zwraca liczniki
per symbol w zagnieżdżonym `raw`: `result["raw"][symbol]["Stop Loss Exits"]`.
"""

import pandas as pd

from app.services.engine.opensource_engine import OpenSourceEngine

# Custom indicator (ścieżka Fazy 11): wejście na barze 0, brak własnych exitów —
# Series broadcastuje się po kolumnach close (DataFrame) w from_signals.
_ENTRY_BAR0 = (
    "entries = pd.Series(False, index=close.index)\n"
    "entries.iloc[0] = True\n"
    "exits = pd.Series(False, index=close.index)\n"
)


def _long_df(prices: dict[str, list[float]]) -> pd.DataFrame:
    """Ramka LONG (wierszowy MultiIndex [symbol, date]) — format wejścia Fazy 10."""
    n = len(next(iter(prices.values())))
    dates = pd.date_range("2020-01-01", periods=n)
    frames = [pd.DataFrame({"close": vals}, index=dates) for vals in prices.values()]
    return pd.concat(frames, keys=list(prices.keys()), names=["symbol", "date"])


def _dag(symbols: list[str], exec_params: dict) -> dict:
    return {
        "nodes": [
            {"id": "d1", "category": "DataIngestion", "type": "dataNode",
             "params": {"symbol": symbols, "timeframe": "1d"}},
            {"id": "i1", "category": "Indicators", "type": "indicatorNode",
             "params": {"indicatorType": "custom", "codeContent": _ENTRY_BAR0}},
            {"id": "e1", "category": "Execution", "type": "portfolioNode",
             "params": exec_params},
        ]
    }


def test_multi_symbol_stop_exit_counts_per_symbol():
    """AAPL łamie SL (100→90), MSFT łamie TP (100→112) — liczniki rozdzielone per symbol."""
    engine = OpenSourceEngine()
    # Bar wyściółkowy [0]: auto-shift silnika (ADR-0007) przesuwa entries o 1.
    df = _long_df({
        "AAPL": [100.0, 100.0, 90.0, 92.0, 94.0, 93.0, 95.0],
        "MSFT": [100.0, 100.0, 112.0, 120.0, 118.0, 130.0, 125.0],
    })
    result = engine.run_dag_backtest(
        df, _dag(["AAPL", "MSFT"], {"sl_stop": 0.05, "tp_stop": 0.10})
    )

    assert result.get("is_multi_symbol") is True
    raw = result.get("raw", {})
    assert "AAPL" in raw and "MSFT" in raw, f"Brak zagnieżdżonego raw per symbol: {raw}"

    # AAPL: spadek -10% odpala SL=5%; TP=10% nieosiągnięty przed zamknięciem.
    assert raw["AAPL"]["Stop Loss Exits"] >= 1
    assert raw["AAPL"]["Take Profit Exits"] == 0
    # MSFT: wzrost +12% odpala TP=10%; SL nietknięty.
    assert raw["MSFT"]["Take Profit Exits"] >= 1
    assert raw["MSFT"]["Stop Loss Exits"] == 0


def test_multi_symbol_no_stops_no_raw_counters():
    """Bez sl_stop/tp_stop gałąź multi nie dokłada liczników (spójnie z single-symbol)."""
    engine = OpenSourceEngine()
    df = _long_df({
        "AAPL": [100.0, 101.0, 102.0, 103.0, 104.0, 105.0],
        "MSFT": [100.0, 99.0, 98.0, 99.0, 100.0, 101.0],
    })
    result = engine.run_dag_backtest(df, _dag(["AAPL", "MSFT"], {}))

    assert result.get("is_multi_symbol") is True
    raw = result.get("raw", {})
    for sym_counts in raw.values():
        assert "Stop Loss Exits" not in sym_counts
        assert "Take Profit Exits" not in sym_counts


def test_multi_symbol_only_sl_configured():
    """Tylko sl_stop ustawiony → w raw per symbol jest wyłącznie licznik SL."""
    engine = OpenSourceEngine()
    # Bar wyściółkowy [0]: auto-shift silnika (ADR-0007) przesuwa entries o 1.
    df = _long_df({
        "AAPL": [100.0, 100.0, 90.0, 92.0, 94.0, 93.0, 95.0],
        "MSFT": [100.0, 100.0, 112.0, 120.0, 118.0, 130.0, 125.0],
    })
    result = engine.run_dag_backtest(df, _dag(["AAPL", "MSFT"], {"sl_stop": 0.05}))

    raw = result.get("raw", {})
    assert raw["AAPL"]["Stop Loss Exits"] >= 1
    assert "Take Profit Exits" not in raw["AAPL"]
    assert raw["MSFT"]["Stop Loss Exits"] == 0
