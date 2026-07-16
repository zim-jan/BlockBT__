"""Auto-shift sygnałów w silniku DAG (review Janka 2026-07-16).

Blok TimeShift znika z kanwy: silnik bezwarunkowo przesuwa entries/exits
o 1 okres (fshift) po wygenerowaniu sygnałów wskaźnika, a jawne węzły
time_shift w starych zapisach DAG są traktowane jako no-op — dzięki temu
nie ma ryzyka podwójnego shiftu przy wczytaniu starej strategii.
"""

import numpy as np
import pandas as pd
import pytest

from app.services.engine.indicators import IndicatorService
from app.services.engine.opensource_engine import OpenSourceEngine

FLAT_PARAMS = {
    "strategy_type": "sma_crossover",
    "sma_fast": 10,
    "sma_slow": 30,
    "macd_fast": 12,
    "macd_slow": 26,
    "macd_signal": 9,
    "code_content": "",
}


def _close_df(n: int = 160, seed: int = 7) -> pd.DataFrame:
    """Deterministyczny random-walk — niestały, więc crossovery generują trade'y."""
    rng = np.random.default_rng(seed)
    close = 100.0 + np.cumsum(rng.normal(0.0, 1.0, size=n))
    return pd.DataFrame({"close": close}, index=pd.date_range("2020-01-01", periods=n))


def _dag(extra_nodes: list | None = None) -> dict:
    nodes = [
        {"id": "d1", "category": "DataIngestion", "type": "dataNode",
         "params": {"symbol": "TEST", "timeframe": "1d"}},
        {"id": "i1", "category": "Indicators", "type": "indicatorNode",
         "params": {"indicatorType": "sma_crossover", "smaFast": 10, "smaSlow": 30}},
        {"id": "e1", "category": "Execution", "type": "executionNode",
         "params": {"init_cash": 10000.0}},
    ]
    if extra_nodes:
        nodes.extend(extra_nodes)
    return {"nodes": nodes}


def _return_with_shift(engine: OpenSourceEngine, df: pd.DataFrame, periods: int) -> float:
    """Oczekiwany Total Return [%] dla sygnałów przesuniętych ręcznie o ``periods``."""
    close = engine._prepare_close(df)
    entries, exits = IndicatorService.generate_signals(close, FLAT_PARAMS, engine.vbt)
    if periods:
        entries = engine.apply_time_shift(entries, periods)
        exits = engine.apply_time_shift(exits, periods)
    portfolio = engine.execute_dag_portfolio(
        price_data=close, entries=entries, exits=exits, params={"init_cash": 10000.0}
    )
    return float(portfolio.total_return() * 100)


def test_engine_auto_shifts_signals_without_logic_node():
    """DAG Data→Indicators→Execution (bez węzła shiftu) musi być shiftowany o 1."""
    engine = OpenSourceEngine()
    df = _close_df()

    expected_shifted = _return_with_shift(engine, df, 1)
    unshifted = _return_with_shift(engine, df, 0)
    assert expected_shifted != unshifted, "dane testowe muszą rozróżniać shift"

    result = engine.run_dag_backtest(df, _dag())
    assert result["metrics"]["Total Return [%]"] == pytest.approx(expected_shifted)


def test_legacy_time_shift_node_is_noop():
    """Stary DAG z jawnym timeShiftNode — wynik identyczny jak bez węzła (1× shift)."""
    engine = OpenSourceEngine()
    df = _close_df()
    legacy = {
        "id": "ts1", "category": "LogicOperators", "type": "timeShiftNode",
        "params": {"operator_type": "time_shift", "shift_periods": 1},
    }

    with_node = engine.run_dag_backtest(df, _dag([legacy]))
    without_node = engine.run_dag_backtest(df, _dag())

    assert with_node["metrics"]["Total Return [%]"] == pytest.approx(
        without_node["metrics"]["Total Return [%]"]
    )
    assert with_node["metrics"]["Total Return [%]"] == pytest.approx(
        _return_with_shift(engine, df, 1)
    )


def test_legacy_signal_node_custom_periods_ignored():
    """signalNode z operator_type=time_shift i shift_periods=3 — też no-op (zawsze 1× shift o 1)."""
    engine = OpenSourceEngine()
    df = _close_df()
    legacy = {
        "id": "s1", "category": "LogicOperators", "type": "signalNode",
        "params": {"signalType": "sma_crossover", "operator_type": "time_shift", "shift_periods": 3},
    }

    result = engine.run_dag_backtest(df, _dag([legacy]))
    assert result["metrics"]["Total Return [%]"] == pytest.approx(_return_with_shift(engine, df, 1))
