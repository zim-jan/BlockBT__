import json

import numpy as np
import pandas as pd
import pytest

from app.services.engine.opensource_engine import OpenSourceEngine

# ---------------------------------------------------------------------------
# Faza 10: pomocnicze budowanie danych (LONG MultiIndex [symbol, date])
# ---------------------------------------------------------------------------


def _random_walk(n: int, seed: int, start: float = 100.0) -> np.ndarray:
    """Deterministyczny random-walk cen zamknięcia (nie-stały → powstają sygnały/trade'y)."""
    rng = np.random.default_rng(seed)
    steps = rng.normal(0.0, 1.0, size=n)
    return start + np.cumsum(steps)


def _make_long_df(
    symbols: list[str], n: int = 120, seed_base: int = 0
) -> pd.DataFrame:
    """Buduje ramkę LONG: wierszowy MultiIndex [symbol, date], kolumna 'close'."""
    dates = pd.date_range("2020-01-01", periods=n)
    frames = []
    for i, _sym in enumerate(symbols):
        close = _random_walk(n, seed=seed_base + i + 1)
        frames.append(pd.DataFrame({"close": close}, index=dates))
    combined = pd.concat(frames, keys=symbols, names=["symbol", "date"])
    return combined


def _dag(symbols, *, fast=10, slow=30, extra_nodes=None) -> dict:
    """DAG zgodny z kontraktem: DataIngestion → Indicators → (opc.) → Execution."""
    nodes = [
        {"id": "d1", "category": "DataIngestion", "type": "dataNode",
         "params": {"symbol": symbols, "timeframe": "1d"}},
        {"id": "i1", "category": "Indicators", "type": "indicatorNode",
         "params": {"indicatorType": "sma_crossover", "smaFast": fast, "smaSlow": slow}},
        {"id": "e1", "category": "Execution", "type": "executionNode",
         "params": {"init_cash": 10000.0}},
    ]
    if extra_nodes:
        nodes.extend(extra_nodes)
    return {"nodes": nodes}

def test_broadcasting_multiple_tickers():
    engine = OpenSourceEngine()
    # Przekazujemy listę tickerów
    dag_dict = {
        "nodes": [
            {"id": "d1", "category": "DataIngestion", "type": "dataNode", "params": {"symbol": ["AAPL", "MSFT"]}},
            {"id": "i1", "category": "Indicators", "type": "indicatorNode", "params": {"indicatorType": "sma_crossover", "smaFast": 10, "smaSlow": 30}},
            {"id": "e1", "category": "Execution", "type": "executionNode", "params": {"init_cash": 10000.0}}
        ]
    }
    # Symulujemy df z MultiIndex (wymaga implementacji)
    dummy_index = pd.MultiIndex.from_product([["AAPL", "MSFT"], pd.date_range("2020-01-01", periods=100)], names=["symbol", "date"])
    df = pd.DataFrame({"close": [100.0]*200}, index=dummy_index)
    
    # Próba uruchomienia - powinna rzucić błąd lub nie zwrócić oczekiwanego formatu
    result = engine.run_dag_backtest(df, dag_dict)
    
    # Oczekujemy że metryki będą zgrupowane per ticker (nowa funkcjonalność)
    # Obecna implementacja prawdopodobnie zwróci słownik bez kluczy AAPL/MSFT na tym poziomie
    assert "AAPL" in result.get("metrics", {}), "Metric AAPL missing from result"
    assert "MSFT" in result.get("metrics", {}), "Metric MSFT missing from result"
    assert result.get("metrics", {}).get("AAPL") is not None
    assert result.get("metrics", {}).get("MSFT") is not None


# ---------------------------------------------------------------------------
# Faza 10: nowe testy multi-symbol broadcasting
# ---------------------------------------------------------------------------


def test_prepare_close_pivots_long_to_wide():
    """_prepare_close: LONG [symbol, date] → WIDE (index=daty, kolumny=[AAPL, MSFT] sort)."""
    engine = OpenSourceEngine()
    df = _make_long_df(["MSFT", "AAPL"], n=50)  # celowo odwrotna kolejność
    wide = engine._prepare_close(df)

    assert isinstance(wide, pd.DataFrame)
    assert list(wide.columns) == ["AAPL", "MSFT"], "kolumny muszą być posortowane"
    assert isinstance(wide.index, pd.DatetimeIndex)
    assert wide.index.is_monotonic_increasing


def test_multiindex_unsorted_input_sorted_correctly():
    """Przetasowane wiersze LONG → identyczny wynik jak posortowane (pivot sortuje deterministycznie)."""
    engine = OpenSourceEngine()
    symbols = ["AAPL", "MSFT"]
    sorted_df = _make_long_df(symbols, n=120, seed_base=10)

    shuffled_df = sorted_df.sample(frac=1.0, random_state=123)

    # pivot posortowany rosnąco po datach
    wide = engine._prepare_close(shuffled_df)
    assert wide.index.is_monotonic_increasing

    res_sorted = engine.run_dag_backtest(sorted_df, _dag(symbols))
    res_shuffled = engine.run_dag_backtest(shuffled_df, _dag(symbols))

    for sym in symbols:
        fv_a = res_sorted["metrics"][sym]["Final Value"]
        fv_b = res_shuffled["metrics"][sym]["Final Value"]
        assert abs(fv_a - fv_b) < 1e-9, f"Final Value różni się dla {sym}"


def test_single_symbol_backward_compat():
    """Single-symbol DataFrame → płaskie metryki, brak 'is_multi_symbol', equity_curve to lista."""
    engine = OpenSourceEngine()
    dates = pd.date_range("2020-01-01", periods=120)
    df = pd.DataFrame({"close": _random_walk(120, seed=7)}, index=dates)

    result = engine.run_dag_backtest(df, _dag("AAPL"))

    assert "is_multi_symbol" not in result
    metrics = result["metrics"]
    assert "Total Return [%]" in metrics
    assert not isinstance(metrics.get("Total Return [%]"), dict)
    assert isinstance(result["equity_curve"], list)
    assert isinstance(result["symbol"], str)


def test_nan_alignment_different_calendars():
    """Dwa symbole z częściowo nie pokrywającymi się datami → brak crasha, oba w metrykach."""
    engine = OpenSourceEngine()
    dates_a = pd.date_range("2020-01-01", periods=120)
    dates_b = pd.date_range("2020-01-15", periods=120)  # przesunięty kalendarz
    fa = pd.DataFrame({"close": _random_walk(120, seed=1)}, index=dates_a)
    fb = pd.DataFrame({"close": _random_walk(120, seed=2)}, index=dates_b)
    df = pd.concat([fa, fb], keys=["AAPL", "MSFT"], names=["symbol", "date"])

    result = engine.run_dag_backtest(df, _dag(["AAPL", "MSFT"]))

    assert result.get("is_multi_symbol") is True
    assert "AAPL" in result["metrics"]
    assert "MSFT" in result["metrics"]


def test_time_shift_multi_column():
    """DAG z węzłem LogicOperators time_shift + multi-symbol → brak crasha, oba symbole obecne."""
    engine = OpenSourceEngine()
    symbols = ["AAPL", "MSFT"]
    df = _make_long_df(symbols, n=120, seed_base=20)

    shift_node = {
        "id": "l1", "category": "LogicOperators", "type": "timeShiftNode",
        "params": {"operator_type": "time_shift", "shift_periods": 1},
    }
    dag = _dag(symbols, extra_nodes=[shift_node])

    result = engine.run_dag_backtest(df, dag)

    assert result.get("is_multi_symbol") is True
    assert "AAPL" in result["metrics"]
    assert "MSFT" in result["metrics"]


def test_param_list_plus_multi_symbol_raises():
    """Multi-symbol close + lista okien smaFast → ValueError (Faza 10 nie łączy obu wektoryzacji)."""
    from app.services.engine.indicators import IndicatorService

    engine = OpenSourceEngine()
    dates = pd.date_range("2020-01-01", periods=80)
    close = pd.DataFrame(
        {"AAPL": _random_walk(80, seed=3), "MSFT": _random_walk(80, seed=4)},
        index=dates,
    )
    with pytest.raises(ValueError):
        IndicatorService.generate_sma_crossover(close, [10, 20], 30, engine.vbt)


def test_runner_serializes_nested_metrics():
    """Runner: nested per-symbol metrics przechodzą przez serializację bez spłaszczenia i są JSON-serializowalne."""
    from app.services.engine.runner import _serialize_metrics

    fake_metrics = {
        "AAPL": {
            "Total Return [%]": np.float64(12.5),
            "Sharpe Ratio": np.float64(1.1),
            "Total Trades": np.int64(4),
        },
        "MSFT": {
            "Total Return [%]": np.float64(-3.2),
            "Sharpe Ratio": np.float64(np.nan),  # NaN → None
            "Total Trades": np.int64(2),
        },
    }

    serialized = _serialize_metrics(fake_metrics)

    # struktura zagnieżdżona zachowana
    assert "AAPL" in serialized and "MSFT" in serialized
    assert isinstance(serialized["AAPL"], dict)
    assert serialized["AAPL"]["Total Trades"] == 4
    assert serialized["MSFT"]["Sharpe Ratio"] is None  # NaN → None

    # JSON-serializowalne
    dumped = json.dumps(serialized)
    reloaded = json.loads(dumped)
    assert reloaded["AAPL"]["Total Return [%]"] == 12.5


def test_dag_schema_accepts_symbol_list():
    """DataIngestionParams akceptuje zarówno listę tickerów, jak i pojedynczy string."""
    from app.schemas.dag import DataIngestionParams

    multi = DataIngestionParams(symbol=["AAPL", "MSFT"], timeframe="1d")
    assert multi.symbol == ["AAPL", "MSFT"]

    single = DataIngestionParams(symbol="AAPL", timeframe="1d")
    assert single.symbol == "AAPL"
