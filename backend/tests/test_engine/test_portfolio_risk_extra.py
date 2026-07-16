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


# Custom indicator: wejście bar0, wyjście SYGNAŁOWE na barze 1.
_ENTRY_BAR0_EXIT_BAR1 = (
    "entries = pd.Series(False, index=close.index)\n"
    "entries.iloc[0] = True\n"
    "exits = pd.Series(False, index=close.index)\n"
    "exits.iloc[1] = True\n"
)


def test_signal_exit_near_stop_level_not_counted_as_sl():
    """Review 2026-07-15: wyjście sygnałowe w pasie eps NAD poziomem SL nie jest liczone jako stop.

    Wejście @100 (fill 100.1 ze slippage), SL 5% → poziom 95.095. Close bar1 = 95.1
    NIE przebija poziomu (stop nie odpala), ale sygnał exit zamyka @95.0049 — cena
    mieści się w tolerancji eps i stara heurystyka fałszywie liczyła to jako SL.
    Maska exits na barze wyjścia rozstrzyga: to wyjście sygnałowe → licznik SL = 0.
    """
    engine = OpenSourceEngine()
    df = pd.DataFrame({"close": [100.0, 95.1, 96.0, 97.0, 98.0]})
    result = engine.run_dag_backtest(
        df, _dag({"sl_stop": 0.05}, code=_ENTRY_BAR0_EXIT_BAR1)
    )
    assert result["raw"]["Stop Loss Exits"] == 0


def test_gap_through_stop_counted_despite_signal_exit_same_bar():
    """Głębokie przebicie poziomu SL (gap 100→90) liczy się jako stop nawet przy
    koincydencji sygnału exit na tym samym barze — o klasyfikacji decyduje warunek
    triggera (close bara wyjścia za poziomem stopu), nie maska sygnałów."""
    engine = OpenSourceEngine()
    df = pd.DataFrame({"close": [100.0, 90.0, 96.0, 97.0, 98.0]})
    result = engine.run_dag_backtest(
        df, _dag({"sl_stop": 0.05}, code=_ENTRY_BAR0_EXIT_BAR1)
    )
    assert result["raw"]["Stop Loss Exits"] == 1


# Custom indicator: wejście bar0, maska exits STREFOWA (True od bar1 do końca) —
# typowa dla warunków typu fast<slow, gdzie sygnał trzyma się przez cały trend.
_ENTRY_BAR0_EXIT_ZONE = (
    "entries = pd.Series(False, index=close.index)\n"
    "entries.iloc[0] = True\n"
    "exits = pd.Series(False, index=close.index)\n"
    "exits.iloc[1:] = True\n"
)


def test_stop_hit_counted_despite_zone_exit_mask():
    """Review 2026-07-16: realne trafienie stopu przy STREFOWEJ masce exits.

    Close bar1 = 95.05 przekracza poziom SL 95.095 (5% od fill-a wejścia 100.1) —
    vbt uruchamia stop. Poprzednia heurystyka pasa eps unieważniała klasyfikację,
    bo na barze wyjścia był też sygnał exit (maska strefowa), a fill nie był
    "głęboko" za poziomem → systematyczny undercount stopów dla masek strefowych.
    Warunek triggera (close za poziomem) klasyfikuje deterministycznie: to stop.
    """
    engine = OpenSourceEngine()
    df = pd.DataFrame({"close": [100.0, 95.05, 96.0, 97.0, 98.0]})
    result = engine.run_dag_backtest(
        df, _dag({"sl_stop": 0.05}, code=_ENTRY_BAR0_EXIT_ZONE)
    )
    assert result["raw"]["Stop Loss Exits"] == 1
