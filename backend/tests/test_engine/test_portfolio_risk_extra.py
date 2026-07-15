"""Faza 12: dodatkowe testy zarządzania ryzykiem i sizingu portfela."""

import pandas as pd
import pytest

from app.core.utils.graph_parser import GraphValidationError
from app.services.engine.opensource_engine import OpenSourceEngine

# Custom indicator (ścieżka Fazy 11): wejście na barze 0, brak własnych exitów.
_ENTRY_BAR0 = (
    "entries = pd.Series(False, index=close.index)\n"
    "entries.iloc[0] = True\n"
    "exits = pd.Series(False, index=close.index)\n"
)


def _dag(exec_params: dict, code: str = _ENTRY_BAR0) -> dict:
    return {
        "nodes": [
            {"id": "i1", "category": "Indicators", "type": "indicatorNode",
             "params": {"indicatorType": "custom", "codeContent": code}},
            {"id": "e1", "category": "Execution", "type": "portfolioNode", "params": exec_params},
        ]
    }


def test_trailing_stop_runs():
    """Trailing stop (sl_trail=True) — ścieżka wykonuje się i zwraca wynik."""
    engine = OpenSourceEngine()
    df = pd.DataFrame({"close": [100.0, 115, 120, 118, 130]})
    result = engine.run_dag_backtest(df, _dag({"sl_stop": 0.05, "sl_trail": True}))
    assert result["status"] == "COMPLETED"
    # sl_stop ustawiony → licznik SL obecny w raw.
    assert "Stop Loss Exits" in result["raw"]


def test_trailing_stop_counted_relative_to_peak():
    """H2: trailing SL liczony względem biegnącego szczytu, nie ceny wejścia.

    Ruch 100→130→110: trailing SL (5% od szczytu 130 = 123.5) odpala i JEST liczony;
    ten sam ruch przy stopie stałym (5% od 100 = 95) nie odpala — 110 nie łamie 95.
    Gdyby licznik używał poziomu od wejścia, trailing byłby błędnie 0 (regresja z review).
    """
    engine = OpenSourceEngine()
    df = pd.DataFrame({"close": [100.0, 130, 120, 115, 110]})
    trail = engine.run_dag_backtest(df, _dag({"sl_stop": 0.05, "sl_trail": True}))
    fixed = engine.run_dag_backtest(df, _dag({"sl_stop": 0.05}))
    assert trail["raw"]["Stop Loss Exits"] > 0
    assert fixed["raw"]["Stop Loss Exits"] == 0


def test_position_sizing_reflected():
    """Sizing: większy size => inna (wyższa na rosnącej serii) wartość końcowa."""
    engine = OpenSourceEngine()
    df = pd.DataFrame({"close": [100.0, 115, 120, 118, 130]})
    small = engine.run_dag_backtest(df, _dag({"size": 1, "size_type": "amount"}))
    large = engine.run_dag_backtest(df, _dag({"size": 5, "size_type": "amount"}))
    assert large["final_capital"] != small["final_capital"]
    assert large["final_capital"] > small["final_capital"]


def test_guard_missing_indicators_node():
    """Brak węzła Indicators → GraphValidationError."""
    engine = OpenSourceEngine()
    df = pd.DataFrame({"close": [100.0, 90, 110, 105, 95]})
    dag = {"nodes": [{"id": "e1", "category": "Execution", "type": "portfolioNode", "params": {}}]}
    with pytest.raises(GraphValidationError):
        engine.run_dag_backtest(df, dag)


def test_no_stops_absent_counts():
    """Bez sl_stop/tp_stop — liczniki SL/TP nie są dodawane do raw."""
    engine = OpenSourceEngine()
    df = pd.DataFrame({"close": [100.0, 115, 120, 118, 130]})
    result = engine.run_dag_backtest(df, _dag({}))
    assert "Stop Loss Exits" not in result["raw"]
    assert "Take Profit Exits" not in result["raw"]


def test_take_profit_fires():
    """Rosnąca seria: wejście bar0 @100, bar1 +15% > tp_stop 10% → Take Profit Exits > 0."""
    engine = OpenSourceEngine()
    df = pd.DataFrame({"close": [100.0, 115, 120, 118, 130]})
    result = engine.run_dag_backtest(df, _dag({"sl_stop": 0.05, "tp_stop": 0.10}))
    assert result["raw"].get("Take Profit Exits", 0) > 0
    assert result["raw"].get("Stop Loss Exits", 0) == 0
