"""
Analiza alokacji kapitału po backteście (ADR-0009).

Silnik dokłada do wyniku ``run_dag_backtest`` blok ``allocation``:
- ``timeline``: wagi ``asset_value_i / Σ value`` per symbol + ``cash``
  (Σ cash / Σ value) — na każdym punkcie sumują się do ~1,
- ``summary``: per symbol średnia/maks. ekspozycja, % czasu w rynku
  i udział w kapitale końcowym.

Portfel multi-symbol to niezależne kolumny (bez cash_sharing) — analiza
pokazuje strukturę ŁĄCZNEGO kapitału, nie realny wspólny portfel.
"""


import numpy as np
import pandas as pd
import pytest

from app.services.engine.opensource_engine import OpenSourceEngine


def _random_walk(n: int, seed: int, start: float = 100.0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return start * np.exp(np.cumsum(rng.normal(0.0005, 0.02, size=n)))


def _single_df(n: int = 250) -> pd.DataFrame:
    idx = pd.date_range("2022-01-01", periods=n, freq="D")
    return pd.DataFrame({"close": _random_walk(n, seed=7)}, index=idx)


def _long_df(symbols: list[str], n: int = 250) -> pd.DataFrame:
    dates = pd.date_range("2022-01-01", periods=n, freq="D")
    frames = [
        pd.DataFrame({"close": _random_walk(n, seed=11 + i)}, index=dates)
        for i in range(len(symbols))
    ]
    return pd.concat(frames, keys=symbols, names=["symbol", "date"])


def _dag(symbol) -> dict:
    return {
        "nodes": [
            {"id": "d1", "category": "DataIngestion", "type": "dataNode",
             "params": {"symbol": symbol, "timeframe": "1d"}},
            {"id": "i1", "category": "Indicators", "type": "indicatorNode",
             "params": {"indicatorType": "sma_crossover", "smaFast": 10, "smaSlow": 30}},
            {"id": "e1", "category": "Execution", "type": "executionNode",
             "params": {"init_cash": 10000.0, "fees": 0.001, "slippage": 0.001}},
        ],
        "edges": [
            {"id": "e1a", "source": "d1", "target": "i1"},
            {"id": "e1b", "source": "i1", "target": "e1"},
        ],
    }


@pytest.fixture(scope="module")
def engine() -> OpenSourceEngine:
    return OpenSourceEngine()


# ---------------------------------------------------------------------------
# Single-symbol: ekspozycja aktywa vs gotówka
# ---------------------------------------------------------------------------


def test_single_symbol_result_contains_allocation(engine):
    result = engine.run_dag_backtest(_single_df(), _dag("TEST"))

    allocation = result["allocation"]
    timeline = allocation["timeline"]
    assert set(timeline["weights"].keys()) == {"TEST", "cash"}
    n_points = len(timeline["dates"])
    assert n_points > 0
    assert all(len(w) == n_points for w in timeline["weights"].values())

    # wagi aktywa + gotówki sumują się do ~1 w każdym punkcie
    sums = np.array(timeline["weights"]["TEST"]) + np.array(timeline["weights"]["cash"])
    np.testing.assert_allclose(sums, 1.0, atol=1e-6)

    summary = allocation["summary"]["TEST"]
    assert 0.0 <= summary["time_in_market_pct"] <= 100.0
    assert 0.0 <= summary["avg_exposure_pct"] <= summary["max_exposure_pct"] <= 100.0 + 1e-6
    # single-symbol: cały kapitał końcowy należy do jedynego symbolu
    assert summary["final_equity_share_pct"] == pytest.approx(100.0)


def test_single_symbol_strategy_actually_enters_market(engine):
    """Sanity: SMA crossover na random-walku wchodzi w rynek — ekspozycja > 0."""
    result = engine.run_dag_backtest(_single_df(), _dag("TEST"))
    summary = result["allocation"]["summary"]["TEST"]
    assert summary["time_in_market_pct"] > 0.0
    assert summary["max_exposure_pct"] > 0.0


# ---------------------------------------------------------------------------
# Multi-symbol: struktura łącznego kapitału per symbol + cash
# ---------------------------------------------------------------------------


def test_multi_symbol_allocation_weights_sum_to_one(engine):
    symbols = ["ALFA", "BETA", "GAMA"]
    result = engine.run_dag_backtest(_long_df(symbols), _dag(symbols))

    allocation = result["allocation"]
    weights = allocation["timeline"]["weights"]
    assert set(weights.keys()) == {*symbols, "cash"}

    total = np.sum([np.array(w) for w in weights.values()], axis=0)
    np.testing.assert_allclose(total, 1.0, atol=1e-6)


def test_multi_symbol_final_equity_shares_sum_to_100(engine):
    symbols = ["ALFA", "BETA"]
    result = engine.run_dag_backtest(_long_df(symbols), _dag(symbols))

    summary = result["allocation"]["summary"]
    assert set(summary.keys()) == set(symbols)
    shares = [summary[s]["final_equity_share_pct"] for s in symbols]
    assert sum(shares) == pytest.approx(100.0, abs=1e-6)


# ---------------------------------------------------------------------------
# Downsampling: timeline ograniczony, ostatni bar zawsze obecny
# ---------------------------------------------------------------------------


def test_allocation_timeline_is_downsampled(engine):
    n = 1500
    result = engine.run_dag_backtest(_single_df(n), _dag("TEST"))

    timeline = result["allocation"]["timeline"]
    assert len(timeline["dates"]) <= 501  # cap + ewentualny ostatni bar
    # ostatni punkt timeline == ostatni bar danych (koniec symulacji)
    last_date = pd.Timestamp(timeline["dates"][-1])
    assert last_date == pd.date_range("2022-01-01", periods=n, freq="D")[-1]
