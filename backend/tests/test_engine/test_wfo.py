"""Testy Walk-Forward Optimization (Faza 15 + poprawki review 2026-07-16).

Obejmuje: podział na okna IS/OOS (rolling i anchored, brak look-ahead),
przebieg WFO na stałych parametrach, optymalizację in-sample (Optuna, warm start),
odporność na awarie okien, honorowanie metryki celu, agregację metryk OOS
(dokładny Sharpe ze sklejonych zwrotów) oraz przypadki brzegowe.
"""

import numpy as np
import pandas as pd
import pytest

from app.services.engine.opensource_engine import OpenSourceEngine
from app.services.engine.optimizer import OptunaOptimizer, WalkForwardOptimizer, WfoConfig


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
    """Sztuczny silnik — rejestruje wywołania i zwraca deterministyczne metryki.

    ``metrics_fn(data, params, call_no)`` może rzucić wyjątkiem (symulacja awarii
    okna) albo zwrócić metryki; ``result_fn`` pozwala podmienić CAŁY wynik
    (np. kształt wektoryzowany bez klucza ``metrics``).
    """

    def __init__(self, metrics_fn=None, result_fn=None):
        self.calls: list[dict] = []
        self._metrics_fn = metrics_fn
        self._result_fn = result_fn

    def run_backtest(self, data: pd.DataFrame, params: dict) -> dict:
        self.calls.append(
            {
                "start": data.index[0],
                "end": data.index[-1],
                "rows": len(data),
                "params": dict(params),
            }
        )
        if self._result_fn is not None:
            return self._result_fn(data, params, len(self.calls))
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
        assert is_end - is_start == pd.Timedelta("365D")
        assert oos_end - oos_start == pd.Timedelta("90D")

        is_slice = idx[(idx >= is_start) & (idx < is_end)]
        oos_slice = idx[(idx >= oos_start) & (idx < oos_end)]
        assert len(is_slice) > 0
        assert len(oos_slice) > 0
        # Brak look-ahead: cały OOS jest ściśle po IS
        assert is_slice.max() < oos_slice.min()

    # Rolling: kolejne okna przesunięte o step, segmenty OOS przylegają (bez nakładania)
    for prev, nxt in zip(windows, windows[1:], strict=False):
        assert nxt[0] - prev[0] == pd.Timedelta("90D")
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
        assert is_end - is_start == pd.Timedelta("365D") + i * pd.Timedelta("90D")
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


def test_split_windows_unsorted_index_rejected(dummy_data):
    """searchsorted wymaga posortowanego indeksu — jawny błąd zamiast cichych bzdur."""
    shuffled = dummy_data.index[::-1]
    with pytest.raises(ValueError):
        WalkForwardOptimizer.split_windows(
            shuffled, window_size="365d", step_size="90d", mode="rolling"
        )


# ---------------------------------------------------------------------------
# Przebieg WFO — stałe parametry (bez optymalizacji IS)
# ---------------------------------------------------------------------------


def test_run_wfo_fixed_params_evaluates_each_oos_window(dummy_data):
    engine = FakeEngine()
    optimizer = WalkForwardOptimizer(engine)
    params = {"sma_fast": 10, "sma_slow": 30}

    result = optimizer.run_wfo(
        dummy_data, params, WfoConfig(window_size="365d", step_size="90d")
    )

    assert result["status"] == "COMPLETED"
    assert result["method"] == "walk_forward"
    assert result["mode"] == "rolling"
    assert result["n_windows"] == 5
    assert result["n_failed_windows"] == 0
    assert len(result["trials"]) == 5

    # Bez param_bounds: dokładnie 1 backtest OOS na okno
    assert len(engine.calls) == 5

    first_oos_start = dummy_data.index[0] + pd.Timedelta("365D")
    for call, window in zip(engine.calls, result["trials"], strict=True):
        # Silnik dostał wyłącznie dane OOS (nigdy dane in-sample)
        assert call["start"] >= first_oos_start
        assert call["rows"] <= 90
        assert window["best_params"]["sma_fast"] == 10
        assert window["best_params"]["sma_slow"] == 30
        assert "oos_metrics" in window
        assert window["oos_metrics"]["Total Return [%]"] == 10.0
        assert window["oos_metrics"]["Sharpe Ratio"] == 1.0

    # Agregacja: zwroty składane geometrycznie; Sharpe — fallback na średnią per okno
    # (FakeEngine nie zwraca equity_curve)
    overall = result["overall_metrics"]
    assert overall["Total Return [%]"] == pytest.approx((1.1**5 - 1) * 100)
    assert overall["Sharpe Ratio"] == pytest.approx(1.0)

    # Pola kontraktu JobService: best_value = wartość metryki celu najlepszego okna OOS
    assert result["best_params"] == params
    assert result["best_value"] == pytest.approx(10.0)


def test_run_wfo_nan_inf_guard(dummy_data):
    """Metryki NaN/inf z silnika -> 0.0 w metrykach okna i skończone metryki łączne."""

    def metrics_fn(data, params, call_no):
        if call_no == 1:
            return {"Total Return [%]": float("nan"), "Sharpe Ratio": float("inf")}
        return {"Total Return [%]": 5.0, "Sharpe Ratio": 2.0}

    engine = FakeEngine(metrics_fn)
    optimizer = WalkForwardOptimizer(engine)

    result = optimizer.run_wfo(
        dummy_data, {"sma_fast": 10}, WfoConfig(window_size="365d", step_size="90d")
    )

    first = result["trials"][0]["oos_metrics"]
    assert first["Total Return [%]"] == 0.0
    assert first["Sharpe Ratio"] == 0.0

    overall = result["overall_metrics"]
    assert np.isfinite(overall["Total Return [%]"])
    assert np.isfinite(overall["Sharpe Ratio"])


def test_run_wfo_anchored_mode(dummy_data):
    engine = FakeEngine()
    optimizer = WalkForwardOptimizer(engine)

    result = optimizer.run_wfo(
        dummy_data,
        {"sma_fast": 10},
        WfoConfig(window_size="365d", step_size="90d", mode="anchored"),
    )

    assert result["mode"] == "anchored"
    assert result["n_windows"] == 5
    # Okna raportują granice IS/OOS (ISO daty) — audytowalność braku look-ahead
    for window in result["trials"]:
        assert window["is_end"] <= window["oos_start"]


# ---------------------------------------------------------------------------
# Odporność na awarie okien (review 2026-07-16)
# ---------------------------------------------------------------------------


def test_run_wfo_partial_window_failure_excluded_from_aggregates(dummy_data):
    """Awaria jednego okna OOS: raport z ``error``, agregaty TYLKO z okien udanych."""

    def metrics_fn(data, params, call_no):
        if call_no == 2:
            raise RuntimeError("engine exploded")
        return {"Total Return [%]": 10.0, "Sharpe Ratio": 1.0}

    engine = FakeEngine(metrics_fn)
    optimizer = WalkForwardOptimizer(engine)

    result = optimizer.run_wfo(
        dummy_data, {"sma_fast": 10}, WfoConfig(window_size="365d", step_size="90d")
    )

    assert result["status"] == "COMPLETED"
    assert result["n_failed_windows"] == 1
    failed = result["trials"][1]
    assert "engine exploded" in failed["error"]
    assert failed["oos_metrics"]["Total Return [%]"] == 0.0

    # Okno z błędem nie zaniża agregatów (wcześniej wstrzykiwało 0.0 do średniej)
    overall = result["overall_metrics"]
    assert overall["Total Return [%]"] == pytest.approx((1.1**4 - 1) * 100)
    assert overall["Sharpe Ratio"] == pytest.approx(1.0)


def test_run_wfo_all_windows_failed_raises(dummy_data):
    """Awaria WSZYSTKICH okien -> RuntimeError (job FAILED), nie COMPLETED z zerami."""

    def metrics_fn(data, params, call_no):
        raise RuntimeError("always broken")

    engine = FakeEngine(metrics_fn)
    optimizer = WalkForwardOptimizer(engine)

    with pytest.raises(RuntimeError, match="All 5 WFO windows failed"):
        optimizer.run_wfo(
            dummy_data, {"sma_fast": 10}, WfoConfig(window_size="365d", step_size="90d")
        )


def test_run_wfo_is_optimization_failure_reported_per_window(dummy_data):
    """Awaria Optuny na IS (np. min>max w bounds) nie ucieka surowym wyjątkiem
    z przebiegu — trafia do raportów okien; komplet awarii -> RuntimeError."""
    engine = FakeEngine()
    optimizer = WalkForwardOptimizer(engine)

    with pytest.raises(RuntimeError, match="In-sample optimization failed"):
        optimizer.run_wfo(
            dummy_data,
            {"sma_slow": 30},
            WfoConfig(
                window_size="365d",
                step_size="90d",
                param_bounds={"sma_fast": {"min": 12, "max": 2, "type": "int"}},
                n_trials=2,
            ),
        )


def test_run_wfo_missing_metrics_is_window_error(dummy_data):
    """Wynik silnika bez klucza ``metrics`` (kształt wektoryzowany) to błąd okna,
    a nie ciche all-zero COMPLETED."""

    def result_fn(data, params, call_no):
        return {"is_vectorized": True, "vectorized_results": []}

    engine = FakeEngine(result_fn=result_fn)
    optimizer = WalkForwardOptimizer(engine)

    with pytest.raises(RuntimeError, match="no 'metrics'"):
        optimizer.run_wfo(
            dummy_data, {"sma_fast": 10}, WfoConfig(window_size="365d", step_size="90d")
        )


def test_run_wfo_rejects_list_parameters(dummy_data):
    """Parametry-listy (tryb wektoryzowany silnika) są odrzucane na wejściu."""
    engine = FakeEngine()
    optimizer = WalkForwardOptimizer(engine)

    with pytest.raises(ValueError, match="list-valued"):
        optimizer.run_wfo(
            dummy_data,
            {"sma_fast": [5, 10]},
            WfoConfig(window_size="365d", step_size="90d"),
        )
    assert engine.calls == []


# ---------------------------------------------------------------------------
# Metryka celu i raportowane parametry (review 2026-07-16)
# ---------------------------------------------------------------------------


def test_run_wfo_custom_metric_selects_best_window(dummy_data):
    """Żądana metryka steruje wyborem najlepszego okna i best_value —
    wcześniej metryki spoza {Total Return, Sharpe} cicho spadały na Total Return."""

    def metrics_fn(data, params, call_no):
        # Wg Total Return najlepsze byłoby okno 0; wg Calmar — okno 4
        return {
            "Total Return [%]": 10.0 - call_no,
            "Sharpe Ratio": 1.0,
            "Calmar": float(call_no),
        }

    engine = FakeEngine(metrics_fn)
    optimizer = WalkForwardOptimizer(engine)

    result = optimizer.run_wfo(
        dummy_data,
        {"sma_fast": 10},
        WfoConfig(window_size="365d", step_size="90d", metric="Calmar"),
    )

    for window in result["trials"]:
        assert "Calmar" in window["oos_metrics"]
    assert result["best_value"] == pytest.approx(5.0)


def test_run_wfo_infra_keys_stripped_from_best_params(dummy_data):
    """Klucze infrastrukturalne snapshotu (symbol, kapitał, okna) nie udają
    parametrów strategii w best_params — silnik nadal dostaje pełny zestaw."""
    engine = FakeEngine()
    optimizer = WalkForwardOptimizer(engine)
    params = {
        "sma_fast": 10,
        "symbol": "AAPL",
        "data_source": "yahoo",
        "timeframe": "1d",
        "initial_capital": 10000.0,
    }

    result = optimizer.run_wfo(
        dummy_data, params, WfoConfig(window_size="365d", step_size="90d")
    )

    assert result["best_params"] == {"sma_fast": 10}
    for window in result["trials"]:
        assert set(window["best_params"]) == {"sma_fast"}
    # Silnik dostał pełny snapshot (initial_capital jest mu potrzebny)
    assert engine.calls[0]["params"]["initial_capital"] == 10000.0


# ---------------------------------------------------------------------------
# Agregacja Sharpe'a ze sklejonych zwrotów OOS (review 2026-07-16)
# ---------------------------------------------------------------------------


def test_run_wfo_overall_sharpe_from_stitched_equity(dummy_data):
    """Silnik z equity_curve: łączny Sharpe liczony ze SKLEJONYCH zwrotów OOS,
    a nie jako średnia arytmetyczna Sharpe'ów per okno."""
    curve = [100.0, 102.0, 101.0, 103.0]

    def result_fn(data, params, call_no):
        return {
            "metrics": {"Total Return [%]": 3.0, "Sharpe Ratio": 9.9},
            "equity_curve": [{"date": str(i), "value": v} for i, v in enumerate(curve)],
        }

    engine = FakeEngine(result_fn=result_fn)
    optimizer = WalkForwardOptimizer(engine)

    result = optimizer.run_wfo(
        dummy_data, {"sma_fast": 10}, WfoConfig(window_size="365d", step_size="90d")
    )

    window_returns = np.diff(curve) / np.array(curve[:-1])
    stitched = np.tile(window_returns, 5)
    expected = stitched.mean() / stitched.std(ddof=1) * np.sqrt(252)

    overall_sharpe = result["overall_metrics"]["Sharpe Ratio"]
    assert overall_sharpe == pytest.approx(expected)
    # Naiwna średnia per okno dałaby 9.9 — dokładna agregacja daje inną wartość
    assert overall_sharpe != pytest.approx(9.9)


# ---------------------------------------------------------------------------
# Optymalizacja in-sample (Optuna) + warm start
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
        WfoConfig(
            window_size="365d",
            step_size="90d",
            param_bounds={"sma_fast": {"min": 2, "max": 12, "type": "int"}},
            n_trials=n_trials,
        ),
    )

    assert result["status"] == "COMPLETED"
    assert result["n_windows"] == 5
    # Na okno: n_trials backtestów IS + 1 backtest OOS
    assert len(engine.calls) == 5 * (n_trials + 1)

    for window in result["trials"]:
        best = window["best_params"]
        # Parametr zoptymalizowany w granicach bounds, parametry bazowe zachowane
        assert 2 <= best["sma_fast"] <= 12
        assert best["sma_slow"] == 30

    # best_params wyniku = parametry najlepszego okna OOS
    assert result["best_params"] in [w["best_params"] for w in result["trials"]]


def test_optuna_warm_start_enqueues_initial_params(dummy_data):
    """initial_params trafiają do Optuny jako pierwszy trial (warm start okien WFO)."""
    engine = FakeEngine()
    optimizer = OptunaOptimizer(engine)

    result = optimizer.run_optimization(
        {"sma_fast": {"min": 2, "max": 12, "type": "int"}},
        dummy_data,
        {"sma_slow": 30},
        n_trials=2,
        initial_params={"sma_fast": 7, "not_in_bounds": 99},
    )

    assert result["trials"][0]["params"]["sma_fast"] == 7


# ---------------------------------------------------------------------------
# Przypadki brzegowe + E2E na realnym silniku
# ---------------------------------------------------------------------------


def test_run_wfo_too_short_data_raises(dummy_data):
    engine = FakeEngine()
    optimizer = WalkForwardOptimizer(engine)
    short = dummy_data.iloc[:100]

    with pytest.raises(ValueError, match="too short"):
        optimizer.run_wfo(short, {"sma_fast": 10}, WfoConfig(window_size="365d", step_size="90d"))


def test_walk_forward_optimizer_basic(wave_data):
    """E2E na realnym OpenSourceEngine — kontrakt odpowiedzi zachowany."""
    engine = OpenSourceEngine()
    optimizer = WalkForwardOptimizer(engine)

    params = {"sma_fast": 10, "sma_slow": 30}

    result = optimizer.run_wfo(
        wave_data, params, WfoConfig(window_size="365d", step_size="90d")
    )

    assert result["status"] == "COMPLETED"
    assert "overall_metrics" in result
    assert result["window"] == "365d"
    assert result["step"] == "90d"
    assert result["n_windows"] == 5
    assert np.isfinite(result["overall_metrics"]["Total Return [%]"])
    assert np.isfinite(result["overall_metrics"]["Sharpe Ratio"])


def test_walk_forward_optimizer_zero_close_real_engine(wave_data):
    """Regresja review 2026-07-16: cena 0.0 w środku okna OOS nie wywala przebiegu
    (guardy NaN/inf lub error per okno) — pokrycie utracone przy przepisaniu
    testów stubu na FakeEngine."""
    data = wave_data.copy()
    data.iloc[400, data.columns.get_loc("close")] = 0.0

    engine = OpenSourceEngine()
    optimizer = WalkForwardOptimizer(engine)

    result = optimizer.run_wfo(
        data, {"sma_fast": 10, "sma_slow": 30}, WfoConfig(window_size="365d", step_size="90d")
    )

    assert result["status"] == "COMPLETED"
    assert result["n_windows"] == 5
    assert np.isfinite(result["overall_metrics"]["Total Return [%]"])
    assert np.isfinite(result["overall_metrics"]["Sharpe Ratio"])
    for window in result["trials"]:
        for value in window["oos_metrics"].values():
            assert np.isfinite(value)


def test_walk_forward_optimizer_invalid_data():
    engine = OpenSourceEngine()
    optimizer = WalkForwardOptimizer(engine)

    with pytest.raises(KeyError):
        optimizer.run_wfo(pd.DataFrame(), {}, WfoConfig(window_size="365d", step_size="90d"))
