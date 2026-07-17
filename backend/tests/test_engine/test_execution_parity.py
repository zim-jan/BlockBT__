"""
Parytet egzekucji legacy vs DAG (audyt 2026-07-17, P1).

Grid Search, Optuna i WFO liczą przez ``run_backtest`` — jego semantyka
egzekucji MUSI być identyczna ze ścieżką ``run_dag_backtest``: auto-shift
sygnałów o 1 bar (prewencja look-ahead bias, ADR-0007) oraz koszty
transakcyjne (fees + slippage, Zero-Cost Fallacy). Bez tego optymalizator
wybiera parametry w warunkach nierealnie optymistycznych względem
właściwego backtestu i wyniki optymalizacji są systematycznie zawyżone.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from app.services.engine.opensource_engine import OpenSourceEngine


@pytest.fixture()
def trending_ohlcv() -> pd.DataFrame:
    """Deterministyczny random-walk (seed) — SMA crossover generuje transakcje."""
    idx = pd.date_range("2023-01-01", periods=250, freq="D")
    rng = np.random.default_rng(42)
    close = 100.0 * np.exp(np.cumsum(rng.normal(0.001, 0.02, len(idx))))
    return pd.DataFrame({"close": close}, index=idx)


def _dag(sma_fast: int, sma_slow: int) -> dict:
    return {
        "nodes": [
            {
                "id": "d1",
                "type": "dataNode",
                "category": "DataIngestion",
                "params": {"symbol": "TEST", "timeframe": "1d"},
            },
            {
                "id": "i1",
                "type": "indicatorNode",
                "category": "Indicators",
                "params": {
                    "indicatorType": "sma_crossover",
                    "smaFast": sma_fast,
                    "smaSlow": sma_slow,
                },
            },
            {
                "id": "e1",
                "type": "portfolioNode",
                "category": "Execution",
                "params": {"init_cash": 10000.0, "fees": 0.001, "slippage": 0.001},
            },
        ],
        "edges": [
            {"id": "e-d-i", "source": "d1", "target": "i1"},
            {"id": "e-i-e", "source": "i1", "target": "e1"},
        ],
    }


_LEGACY_PARAMS = {
    "symbol": "TEST",
    "strategy_type": "sma_crossover",
    "sma_fast": 10,
    "sma_slow": 30,
    "initial_capital": 10000.0,
    "fees": 0.001,
    "slippage": 0.001,
    "timeframe": "1d",
}


def test_run_backtest_matches_dag_execution_semantics(trending_ohlcv):
    """Ta sama strategia, te same dane, te same koszty → identyczny wynik obu ścieżek."""
    engine = OpenSourceEngine()

    legacy = engine.run_backtest(trending_ohlcv, dict(_LEGACY_PARAMS))
    dag_result = engine.run_dag_backtest(trending_ohlcv, _dag(10, 30))

    assert legacy["num_trades"] > 0, "scenariusz musi generować transakcje"
    assert legacy["num_trades"] == dag_result["num_trades"]
    assert legacy["total_return_pct"] == pytest.approx(
        dag_result["total_return_pct"], abs=1e-9
    )
    assert legacy["final_capital"] == pytest.approx(
        dag_result["final_capital"], abs=1e-6
    )


def test_run_backtest_applies_slippage(trending_ohlcv):
    """Wyższy slippage MUSI pogarszać wynik — parametr nie może być ignorowany."""
    engine = OpenSourceEngine()

    low = engine.run_backtest(
        trending_ohlcv, {**_LEGACY_PARAMS, "slippage": 0.0005}
    )
    high = engine.run_backtest(
        trending_ohlcv, {**_LEGACY_PARAMS, "slippage": 0.05}
    )

    assert low["num_trades"] > 0
    assert high["total_return_pct"] < low["total_return_pct"]


def test_run_backtest_vectorized_branch_also_shifted(trending_ohlcv):
    """Gałąź wektoryzowana (Grid Search) — wynik kombinacji == wynik pojedynczy.

    Parametry-listy uruchamiają broadcasting; metryki kombinacji (10, 30)
    muszą być identyczne z pojedynczym przebiegiem (10, 30) — czyli shift
    i slippage muszą obowiązywać także w gałęzi wektoryzowanej.
    """
    engine = OpenSourceEngine()

    single = engine.run_backtest(trending_ohlcv, dict(_LEGACY_PARAMS))
    vectorized = engine.run_backtest(
        trending_ohlcv,
        {**_LEGACY_PARAMS, "sma_fast": [10, 12], "sma_slow": [30, 40]},
    )

    assert vectorized.get("is_vectorized") is True
    combo_metrics = vectorized["vectorized_results"][0]["metrics"]
    assert combo_metrics["Total Return [%]"] == pytest.approx(
        single["total_return_pct"], abs=1e-9
    )
    assert combo_metrics["Total Trades"] == single["num_trades"]
