"""Testy Walk-Forward Optimization (Faza 15).

Obejmuje: podział na okna IS/OOS (rolling i anchored, brak look-ahead),
przebieg WFO na stałych parametrach, optymalizację in-sample (Optuna),
agregację metryk OOS z guardem NaN/inf oraz przypadki brzegowe.
"""

import numpy as np
import pandas as pd
import pytest

from app.services.engine.opensource_engine import OpenSourceEngine
from app.services.engine.optimizer import WalkForwardOptimizer


@pytest.fixture
def dummy_data():
    # Create 2 years of daily data
    dates = pd.date_range("2020-01-01", periods=730, freq="D")
    return pd.DataFrame({"close": pd.Series(range(730), dtype=float)}, index=dates)


@pytest.fixture
def wave_data():
    """Syntetyczne dane sinusoidalne — 730 dni, bez zer w cenie."""
    n = 730
    dates = pd.date_range("2020-01-01", periods=n, freq="D")
    close = 100.0 + np.sin(np.arange(n) / 10.0) * 5.0 + np.arange(n) * 0.01
    return pd.DataFrame({"close": close}, index=dates)


class FakeEngine:
    """Sztuczny silnik — rejestruje wywołania i zwraca deterministyczne metryki."""

    def __init__(self, metrics_fn=None):
        self.calls: list[dict] = []
        self._metrics_fn = metrics_fn

    def run_backtest(self, data: pd.DataFrame, params: dict) -> dict:
        self.calls.append(
            {
                "start": data.index[0],
                "end": data.index[-1],
                "rows": len(data),
                "params": dict(params),
            }
        )
        if self._metrics_fn is not None:
            metrics = self._metrics_fn(data, params, len(self.calls))
        else:
            metrics = {"Total Return [%]": 10.0, "Sharpe Ratio": 1.0}
        return {"metrics": metrics}


# ---------------------------------------------------------------------------
# Podział na okna — brak look-ahead
# ---------------------------------------------------------------------------


def test_split_windows_rolling_no_lookahead(dummy_data):
    """Rolling: IS przesuwa się o step; OOS zawsze PO IS, bez nakładania IS na OOS."""
    windows = WalkForwardOptimizer.split_windows(
        dummy_data.index, window_size="365d", step_size="90d", mode="rolling"
    )

    # 730 dni: IS 365d, OOS/step 90d -> 5 okien (ostatnie OOS obcięte końcem danych)
    assert len(windows) == 5

    idx = dummy_data.index
    for is_start, is_end, oos_start, oos_end in windows:
        # OOS zaczyna się dokładnie tam, gdzie kończy się IS (konwencja [start, end))
        assert oos_start == is_end
        assert is_end - is_start == pd.Timedelta("365d")
        assert oos_end - oos_start == pd.Timedelta("90d")

        is_slice = idx[(idx >= is_start) & (idx < is_end)]
        oos_slice = idx[(idx >= oos_start) & (idx < oos_end)]
        assert len(is_slice) > 0
        assert len(oos_slice) > 0
        # Brak look-ahead: cały OOS jest ściśle po IS
        assert is_slice.max() < oos_slice.min()

    # Rolling: kolejne okna przesunięte o step, segmenty OOS przylegają (bez nakładania)
    for prev, nxt in zip(windows, windows[1:], strict=False):
        assert nxt[0] - prev[0] == pd.Timedelta("90d")
        assert nxt[2] == prev[3]


def test_split_windows_anchored(dummy_data):
    """Anchored: początek IS zakotwiczony na starcie danych, IS rośnie o step."""
    windows = WalkForwardOptimizer.split_windows(
        dummy_data.index, window_size="365d", step_size="90d", mode="anchored"
    )

    assert len(windows) == 5

    idx = dummy_data.index
    for i, (is_start, is_end, oos_start, oos_end) in enumerate(windows):
        assert is_start == idx[0]
        assert is_end - is_start == pd.Timedelta("365d") + i * pd.Timedelta("90d")
        assert oos_start == is_end

        is_slice = idx[(idx >= is_start) & (idx < is_end)]
        oos_slice = idx[(idx >= oos_start) & (idx < oos_end)]
        assert len(is_slice) > 0 and len(oos_slice) > 0
        assert is_slice.max() < oos_slice.min()


def test_split_windows_too_short_returns_empty(dummy_data):
    """Dane krótsze niż jedno okno IS+OOS -> brak okien."""
    short_idx = dummy_data.index[:100]
    windows = WalkForwardOptimizer.split_windows(
        short_idx, window_size="365d", step_size="90d", mode="rolling"
    )
    assert windows == []


def test_split_windows_invalid_mode(dummy_data):
    with pytest.raises(ValueError):
        WalkForwardOptimizer.split_windows(
            dummy_data.index, window_size="365d", step_size="90d", mode="banana"
        )


# ---------------------------------------------------------------------------
# Przebieg WFO — stałe parametry (bez optymalizacji IS)
# ---------------------------------------------------------------------------


def test_run_wfo_fixed_params_evaluates_each_oos_window(dummy_data):
    engine = FakeEngine()
    optimizer = WalkForwardOptimizer(engine)
    params = {"sma_fast": 10, "sma_slow": 30}

    result = optimizer.run_wfo(dummy_data, params, window_size="365d", step_size="90d")

    assert result["status"] == "COMPLETED"
    assert result["method"] == "walk_forward"
    assert result["mode"] == "rolling"
    assert result["n_windows"] == 5
    assert len(result["windows"]) == 5

    # Bez param_bounds: dokładnie 1 backtest OOS na okno
    assert len(engine.calls) == 5

    first_oos_start = dummy_data.index[0] + pd.Timedelta("365d")
    for call, window in zip(engine.calls, result["windows"], strict=True):
        # Silnik dostał wyłącznie dane OOS (nigdy dane in-sample)
        assert call["start"] >= first_oos_start
        assert call["rows"] <= 90
        assert window["best_params"]["sma_fast"] == 10
        assert window["best_params"]["sma_slow"] == 30
        assert "oos_metrics" in window
        assert window["oos_metrics"]["Total Return [%]"] == 10.0
        assert window["oos_metrics"]["Sharpe Ratio"] == 1.0

    # Agregacja: zwroty składane geometrycznie, Sharpe uśredniony
    overall = result["overall_metrics"]
    assert overall["Total Return [%]"] == pytest.approx((1.1**5 - 1) * 100)
    assert overall["Sharpe Ratio"] == pytest.approx(1.0)

    # Pola kontraktu JobService (best_params / best_value / trials)
    assert result["best_params"] == params
    assert result["best_value"] == pytest.approx(overall["Total Return [%]"])
    assert result["trials"] == result["windows"]


def test_run_wfo_nan_inf_guard(dummy_data):
    """Metryki NaN/inf z silnika -> 0.0 w metrykach okna i skończone metryki łączne."""

    def metrics_fn(data, params, call_no):
        if call_no == 1:
            return {"Total Return [%]": float("nan"), "Sharpe Ratio": float("inf")}
        return {"Total Return [%]": 5.0, "Sharpe Ratio": 2.0}

    engine = FakeEngine(metrics_fn)
    optimizer = WalkForwardOptimizer(engine)

    result = optimizer.run_wfo(dummy_data, {"sma_fast": 10}, window_size="365d", step_size="90d")

    first = result["windows"][0]["oos_metrics"]
    assert first["Total Return [%]"] == 0.0
    assert first["Sharpe Ratio"] == 0.0

    overall = result["overall_metrics"]
    assert np.isfinite(overall["Total Return [%]"])
    assert np.isfinite(overall["Sharpe Ratio"])


def test_run_wfo_anchored_mode(dummy_data):
    engine = FakeEngine()
    optimizer = WalkForwardOptimizer(engine)

    result = optimizer.run_wfo(
        dummy_data, {"sma_fast": 10}, window_size="365d", step_size="90d", mode="anchored"
    )

    assert result["mode"] == "anchored"
    assert result["n_windows"] == 5
    # Okna raportują granice IS/OOS (ISO daty) — audytowalność braku look-ahead
    for window in result["windows"]:
        assert window["is_end"] <= window["oos_start"]


# ---------------------------------------------------------------------------
# Przebieg WFO — optymalizacja in-sample (Optuna)
# ---------------------------------------------------------------------------


def test_run_wfo_with_param_bounds_optimizes_in_sample(dummy_data):
    """Z param_bounds: per okno optymalizacja IS (Optuna) + 1 backtest OOS."""

    def metrics_fn(data, params, call_no):
        # Parabola z maksimum w sma_fast=7 — Optuna ma do czego zbiegać
        x = float(params.get("sma_fast", 0))
        return {"Total Return [%]": -((x - 7.0) ** 2), "Sharpe Ratio": 0.5}

    engine = FakeEngine(metrics_fn)
    optimizer = WalkForwardOptimizer(engine)

    n_trials = 4
    result = optimizer.run_wfo(
        dummy_data,
        {"sma_slow": 30},
        window_size="365d",
        step_size="90d",
        param_bounds={"sma_fast": {"min": 2, "max": 12, "type": "int"}},
        n_trials=n_trials,
    )

    assert result["status"] == "COMPLETED"
    assert result["n_windows"] == 5
    # Na okno: n_trials backtestów IS + 1 backtest OOS
    assert len(engine.calls) == 5 * (n_trials + 1)

    for window in result["windows"]:
        best = window["best_params"]
        # Parametr zoptymalizowany w granicach bounds, parametry bazowe zachowane
        assert 2 <= best["sma_fast"] <= 12
        assert best["sma_slow"] == 30

    # best_params wyniku = parametry najlepszego okna OOS
    assert result["best_params"] in [w["best_params"] for w in result["windows"]]


# ---------------------------------------------------------------------------
# Przypadki brzegowe + kompatybilność wsteczna kontraktu
# ---------------------------------------------------------------------------


def test_run_wfo_too_short_data_raises(dummy_data):
    engine = FakeEngine()
    optimizer = WalkForwardOptimizer(engine)
    short = dummy_data.iloc[:100]

    with pytest.raises(ValueError):
        optimizer.run_wfo(short, {"sma_fast": 10}, window_size="365d", step_size="90d")


def test_walk_forward_optimizer_basic(wave_data):
    """E2E na realnym OpenSourceEngine — kontrakt odpowiedzi zachowany."""
    engine = OpenSourceEngine()
    optimizer = WalkForwardOptimizer(engine)

    params = {"sma_fast": 10, "sma_slow": 30}

    result = optimizer.run_wfo(
        wave_data,
        params,
        window_size="365d",
        step_size="90d",
    )

    assert result["status"] == "COMPLETED"
    assert "overall_metrics" in result
    assert result["window"] == "365d"
    assert result["step"] == "90d"
    assert result["n_windows"] == 5
    assert np.isfinite(result["overall_metrics"]["Total Return [%]"])
    assert np.isfinite(result["overall_metrics"]["Sharpe Ratio"])


def test_walk_forward_optimizer_invalid_data():
    engine = OpenSourceEngine()
    optimizer = WalkForwardOptimizer(engine)

    with pytest.raises(KeyError):
        optimizer.run_wfo(pd.DataFrame(), {}, window_size="365d", step_size="90d")
