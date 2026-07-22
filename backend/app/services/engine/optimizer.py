"""
Phase 5 — Grid Search Optimizer for parameters.

Allows exhaustive Cartesian-product parameter searches using the open-source vectorbt library.
"""


import itertools
import math
from dataclasses import dataclass, field
from typing import Any

import optuna
import pandas as pd
from loguru import logger

from app.services.engine.opensource_engine import (
    _setup_vbt,
    finite_or_zero,
    periods_per_year_for_timeframe,
)

# Initialize vbt once
try:
    vbt = _setup_vbt()
except Exception:
    vbt = None  # type: ignore

class GridSearchOptimizer:
    """Explores exhaustive combinations of strategy parameters to find optimal variables.

    Generates a flattened cartesian product array from the provided `param_grid` to perform a fully vectorized backtest using vectorbt.

    This ensures that each run is isolated as a distinct sequence for each parameter, ensuring that vectorbt's native broadcasting works seamlessly without throwing MultiIndex errors.
    """

    def __init__(self, engine: Any, **kwargs: Any) -> None:
        """Initialize the optimizer with a compatible BaseStrategyEngine instance.

        Parameters
        ----------
        engine : BaseStrategyEngine
            Instance of the execution engine (OpenSourceEngine or ProEngine).
        """
        self.engine = engine

    def optimize(
        self,
        data: pd.DataFrame,
        param_grid: dict[str, list[Any]],
        base_parameters: dict[str, Any] | None = None,
        metric: str = "Total Return [%]",
    ) -> list[dict[str, Any]]:
        """Run grid search optimization over all parameter combinations.

        Parameters
        ----------
        data : pd.DataFrame
            Market data.
        param_grid : dict[str, list[Any]]
            A dictionary where keys are parameter names and values are lists of discrete values to test.
        base_parameters : dict[str, Any], optional
            The baseline parameters. Keys present in the `param_grid` will overwrite these.
        metric : str, optional
            The performance metric to extract from the returned results.

        Returns
        -------
        list[dict[str, Any]]
            A list of result dictionaries, sorted by metric descending.
        """
        if vbt is None:
            raise RuntimeError("vectorbt not initialized. Check engine setup.")

        if base_parameters is None:
            base_parameters = {}

        # If param_grid is empty, return empty list
        if not param_grid:
            return []

        # 1. Generate all flat combinations
        keys = list(param_grid.keys())
        value_lists = list(param_grid.values())

        # Cartesian product of all value lists
        combinations = list(itertools.product(*value_lists))

        logger.info(
            "Starting Vectorized Grid Search: evaluating {} combinations for parameters: {}",
            len(combinations),
            keys,
        )

        # 2. Build vectorized parameters payload
        grid_params = base_parameters.copy()
        for i, key in enumerate(keys):
            # Extract all values for this parameter across all combinations
            grid_params[key] = [combo[i] for combo in combinations]

        # 3. Execute vectorized backtest
        try:
            execution_result = self.engine.run_backtest(data, grid_params)
            
            if not execution_result.get("is_vectorized"):
                 logger.warning("Engine did not return vectorized results. Falling back to empty.")
                 return []

            vectorized_data = execution_result.get("vectorized_results", [])
            
            results: list[dict[str, Any]] = []
            for i, record in enumerate(vectorized_data):
                # Map back the parameters to the result
                combo_dict = dict(zip(keys, combinations[i], strict=False))
                results.append({
                    "parameters": combo_dict,
                    "metrics": record.get("metrics", {})
                })

        except Exception as e:
            logger.error(f"Failed to execute vectorized grid search: {e}")
            return []

        # 4. Sort results descending by the target metric
        def extract_metric(res: dict[str, Any]) -> float:
            m = res.get("metrics", {}).get(metric)
            if m is None:
                logger.error(f"Metric '{metric}' not found in vectorbt stats.")
                return float("-inf")
            return float(m)

        results.sort(key=extract_metric, reverse=True)

        logger.info("Grid search completed. Best {} -> {}", metric, extract_metric(results[0]) if results else "N/A")

        return results

    @staticmethod
    def get_best_parameters(results: list[dict[str, Any]], metric: str = "Total Return [%]") -> dict[str, Any]:
        """Helper to extract the parameters from the best performing result.

        Parameters
        ----------
        results : list[dict[str, Any]]
            Output of `run_optimization`.
        metric : str
            Metric used for evaluation.

        Returns
        -------
        dict[str, Any]
            The optimal parameter dictionary.
        """
        if not results:
            return {}

        best_result = max(
            results,
            key=lambda x: float(x.get("metrics", {}).get(metric, float("-inf"))),
        )

        return best_result.get("parameters", {})


class OptunaOptimizer:
    """Uses Optuna (TPE) to find optimal parameters efficiently."""

    def __init__(self, engine: Any) -> None:
        self.engine = engine

    def run_optimization(
        self,
        param_bounds: dict[str, Any],
        data: pd.DataFrame,
        base_parameters: dict[str, Any],
        n_trials: int = 20,
        metric: str = "Total Return [%]",
        initial_params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Run Bayesian optimization.

        param_bounds: dict mapping param_name -> {min, max, type, ...}
        initial_params: opcjonalny warm start — parametry kolejkowane jako pierwszy
        trial (np. najlepsze parametry poprzedniego okna WFO zamiast zimnego TPE).
        """
        logger.info("Starting Optuna optimization (trials={})", n_trials)

        def objective(trial: optuna.Trial) -> float:
            current_params = base_parameters.copy()
            for name, bounds in param_bounds.items():
                # Support both Pydantic model and dict
                b = bounds.model_dump() if hasattr(bounds, "model_dump") else bounds
                p_type = b.get("type", "int")

                if p_type == "int":
                    step_val = b.get("step")
                    current_params[name] = trial.suggest_int(
                        name, 
                        int(b["min"]), 
                        int(b["max"]), 
                        step=int(step_val) if step_val is not None else 1
                    )
                elif p_type == "float":
                    step_val = b.get("step")
                    current_params[name] = trial.suggest_float(
                        name, 
                        float(b["min"]), 
                        float(b["max"]), 
                        step=float(step_val) if step_val is not None else None
                    )
                elif p_type == "categorical":
                    current_params[name] = trial.suggest_categorical(name, b["choices"])

            try:
                execution_result = self.engine.run_backtest(data, current_params)
                val = execution_result.get("metrics", {}).get(metric)
                # FIX (review 2026-07-15): brak metryki / crash trialu → -inf (direction=maximize),
                # inaczej 0.0 wygrywało z poprawnymi, ujemnymi wynikami i fałszowało best_params
                return float(val) if val is not None else float("-inf")
            except Exception as e:
                logger.error(f"Trial {trial.number} failed: {e}")
                return float("-inf")

        study = optuna.create_study(direction="maximize")
        if initial_params:
            # Warm start: tylko parametry objęte bounds (reszta i tak jest w base_parameters)
            warm = {k: v for k, v in initial_params.items() if k in param_bounds}
            if warm:
                try:
                    study.enqueue_trial(warm)
                except Exception as e:  # noqa: BLE001 — warm start jest best-effort
                    logger.warning("Optuna warm-start enqueue failed: {}", e)
        study.optimize(objective, n_trials=n_trials)

        # Format history
        trials_history = []
        for t in study.trials:
            trials_history.append(
                {
                    "number": t.number,
                    "value": t.value,
                    "params": t.params,
                    "state": str(t.state),
                }
            )

        logger.info("Optuna optimization finished. Best value: {}", study.best_value)

        return {
            "best_params": study.best_params,
            "best_value": study.best_value,
            "trials": trials_history,
        }

# Klucze infrastrukturalne snapshotu parametrów (dane rynkowe / kapitał / konfiguracja
# przebiegu) — NIE są parametrami strategii. Silnik dostaje pełny słownik (potrzebuje
# np. initial_capital), ale raportowane best_params są z nich odfiltrowane, żeby nie
# udawały wyniku optymalizacji (review 2026-07-16).
_INFRA_PARAM_KEYS: frozenset[str] = frozenset(
    {
        "symbol",
        "data_source",
        "timeframe",
        "initial_capital",
        "start_date",
        "end_date",
        "window_size",
        "step_size",
        "mode",
    }
)


@dataclass(frozen=True)
class WfoConfig:
    """Konfiguracja przebiegu Walk-Forward Optimization (Faza 15).

    Jeden obiekt zamiast 6 parametrów przewlekanych przez sygnatury
    API → runner → run_wfo → _evaluate_window (review 2026-07-16).
    ``asdict(config)`` daje bezpośrednio zawartość kolumny ``bounds_definition``.
    """

    window_size: str = "365d"
    step_size: str = "90d"
    mode: str = "rolling"
    param_bounds: dict[str, Any] | None = field(default=None)
    n_trials: int = 15
    metric: str = "Total Return [%]"


class WalkForwardOptimizer:
    """Realna Walk-Forward Optimization (Faza 15).

    Dzieli szereg czasowy na sekwencję okien in-sample (IS) / out-of-sample (OOS):

    - **rolling** — początek okna IS przesuwa się o ``step_size`` (stała długość IS),
    - **anchored** — początek IS zakotwiczony na starcie danych (IS rośnie o ``step_size``).

    W każdym oknie: (opcjonalnie) optymalizacja parametrów na IS istniejącym
    ``OptunaOptimizer``, następnie backtest OOS na najlepszych parametrach.
    OOS zawsze zaczyna się dokładnie tam, gdzie kończy się IS (brak look-ahead).
    """

    _MODES: tuple[str, ...] = ("rolling", "anchored")

    def __init__(self, engine: Any) -> None:
        self.engine = engine

    @classmethod
    def split_windows(
        cls,
        index: pd.DatetimeIndex,
        window_size: str,
        step_size: str,
        mode: str = "rolling",
    ) -> list[tuple[pd.Timestamp, pd.Timestamp, pd.Timestamp, pd.Timestamp]]:
        """Podziel oś czasu na okna ``(is_start, is_end, oos_start, oos_end)``.

        Konwencja przedziałów półotwartych: IS = ``[is_start, is_end)``,
        OOS = ``[oos_start, oos_end)``, przy czym ``oos_start == is_end`` —
        OOS jest zawsze ściśle PO IS, bez nakładania (brak look-ahead).

        Parameters
        ----------
        index : pd.DatetimeIndex
            Oś czasu danych rynkowych.
        window_size : str
            Długość okna in-sample (np. ``"365d"``, parsowane przez ``pd.Timedelta``).
        step_size : str
            Długość okna out-of-sample ORAZ krok przesuwu (segmenty OOS przylegają
            do siebie — łączna krzywa OOS pokrywa dane bez duplikacji).
        mode : str
            ``"rolling"`` (stała długość IS) lub ``"anchored"`` (IS rośnie).

        Returns
        -------
        list[tuple]
            Lista okien; pusta, gdy dane są krótsze niż jedno okno IS+OOS.
        """
        if mode not in cls._MODES:
            raise ValueError(f"Unknown WFO mode: {mode!r}. Expected one of {cls._MODES}.")
        if len(index) == 0:
            return []
        if not index.is_monotonic_increasing:
            raise ValueError("WFO requires a sorted (monotonic increasing) DatetimeIndex.")

        # Normalize lowercase aliases for pandas 3.x compat ('d' → 'D')
        is_td = pd.Timedelta(window_size.upper() if isinstance(window_size, str) else window_size)
        oos_td = pd.Timedelta(step_size.upper() if isinstance(step_size, str) else step_size)
        if is_td <= pd.Timedelta(0) or oos_td <= pd.Timedelta(0):
            raise ValueError("window_size and step_size must be positive timedeltas.")

        start_ts = index[0]
        last_ts = index[-1]

        windows: list[tuple[pd.Timestamp, pd.Timestamp, pd.Timestamp, pd.Timestamp]] = []
        k = 0
        while True:
            if mode == "rolling":
                # Stała długość IS, okno przesuwa się o step
                is_start = start_ts + k * oos_td
                is_end = is_start + is_td
            else:
                # Anchored: początek IS stały, koniec IS rośnie o step
                is_start = start_ts
                is_end = start_ts + is_td + k * oos_td

            # Okno emitujemy tylko, gdy OOS zawiera co najmniej jedną obserwację
            if is_end > last_ts:
                break

            oos_end = is_end + oos_td
            # searchsorted na posortowanym indeksie: O(log N) zamiast masek O(N) per okno
            i0 = index.searchsorted(is_start, side="left")
            i1 = index.searchsorted(is_end, side="left")
            i2 = index.searchsorted(oos_end, side="left")
            if i1 > i0 and i2 > i1:
                windows.append((is_start, is_end, is_end, oos_end))
            k += 1

        return windows

    @staticmethod
    def _returns_from_equity(equity_curve: Any) -> list[float]:
        """Zwroty procentowe z krzywej kapitału silnika (lista ``{"date", "value"}``).

        Zwroty liczone WEWNĄTRZ okna (pierwszy punkt odpada), więc sklejanie zwrotów
        z kolejnych okien OOS nie tworzy artefaktu na granicy okien. Brak/za krótka
        krzywa lub wartości niefinite → pusta lista (fallback na średnią per okno).
        """
        if not isinstance(equity_curve, list) or len(equity_curve) < 2:
            return []
        try:
            values = [float(point["value"]) for point in equity_curve]
        except (TypeError, KeyError, ValueError):
            return []
        returns: list[float] = []
        for prev, curr in itertools.pairwise(values):
            if prev == 0.0:
                continue
            r = curr / prev - 1.0
            if math.isfinite(r):
                returns.append(r)
        return returns

    def _evaluate_window(
        self,
        data: pd.DataFrame,
        window_index: int,
        bounds: tuple[pd.Timestamp, pd.Timestamp, pd.Timestamp, pd.Timestamp],
        parameters: dict[str, Any],
        config: WfoConfig,
        warm_start: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any], list[float]]:
        """Przetwórz jedno okno WFO: optymalizacja IS (opcjonalna) + backtest OOS.

        Awaria dowolnego etapu (optymalizacja IS lub backtest OOS) nie zrywa całego
        przebiegu — okno dostaje metryki 0.0 + pole ``error`` (review 2026-07-16;
        wcześniej wyjątek Optuny na IS wywalał cały job).

        Returns
        -------
        tuple
            ``(raport okna, best_params z optymalizacji IS — warm start dla
            kolejnego okna, zwroty OOS z krzywej kapitału — do łącznego Sharpe'a)``.
        """
        is_start, is_end, oos_start, oos_end = bounds
        idx = data.index
        i0 = idx.searchsorted(is_start, side="left")
        i1 = idx.searchsorted(is_end, side="left")
        i2 = idx.searchsorted(oos_end, side="left")
        oos_df = data.iloc[i1:i2]

        error_msg: str | None = None
        best_params = dict(parameters)
        opt_best: dict[str, Any] = {}

        # 1) Optymalizacja in-sample (reuse istniejącego OptunaOptimizer)
        if config.param_bounds:
            is_df = data.iloc[i0:i1]  # materializowane tylko gdy jest optymalizacja IS
            try:
                opt_result = OptunaOptimizer(self.engine).run_optimization(
                    config.param_bounds,
                    is_df,
                    parameters,
                    n_trials=config.n_trials,
                    metric=config.metric,
                    initial_params=warm_start,
                )
                opt_best = opt_result.get("best_params", {})
                best_params = {**parameters, **opt_best}
            except Exception as e:  # noqa: BLE001 — pojedyncze okno nie zrywa całego WFO
                logger.error("WFO window {} in-sample optimization failed: {}", window_index, e)
                error_msg = f"In-sample optimization failed: {e}"

        # 2) Backtest out-of-sample na najlepszych parametrach (pomijany po awarii IS —
        #    wynik OOS na parametrach bazowych udawałby wynik optymalizacji)
        oos_raw: dict[str, Any] = {}
        oos_returns: list[float] = []
        if error_msg is None:
            try:
                oos_result = self.engine.run_backtest(oos_df, best_params)
                if "metrics" not in oos_result:
                    # Np. gałąź wektoryzowana silnika — bez guarda kończyłoby się
                    # cichym raportem all-zero (review 2026-07-16)
                    raise ValueError(
                        "engine returned no 'metrics' (unsupported result shape, "
                        "e.g. vectorized run)"
                    )
                oos_raw = oos_result["metrics"] or {}
                oos_returns = self._returns_from_equity(oos_result.get("equity_curve"))
            except Exception as e:  # noqa: BLE001 — pojedyncze okno nie zrywa całego WFO
                logger.error("WFO window {} OOS backtest failed: {}", window_index, e)
                error_msg = str(e)

        oos_metrics = {
            "Total Return [%]": finite_or_zero(oos_raw.get("Total Return [%]")),
            "Sharpe Ratio": finite_or_zero(oos_raw.get("Sharpe Ratio")),
        }
        # Metryka celu zawsze obecna w raporcie okna — wybór najlepszego okna
        # i best_value działają dla dowolnej metryki, nie tylko dwóch domyślnych
        if config.metric not in oos_metrics:
            oos_metrics[config.metric] = finite_or_zero(oos_raw.get(config.metric))

        report: dict[str, Any] = {
            "window_index": window_index,
            "is_start": is_start.isoformat(),
            "is_end": is_end.isoformat(),
            "oos_start": oos_start.isoformat(),
            "oos_end": oos_end.isoformat(),
            "is_rows": int(i1 - i0),
            "oos_rows": int(len(oos_df)),
            "best_params": {k: v for k, v in best_params.items() if k not in _INFRA_PARAM_KEYS},
            "oos_metrics": oos_metrics,
        }
        if error_msg is not None:
            report["error"] = error_msg
        return report, opt_best, oos_returns

    @staticmethod
    def _annualized_sharpe(returns: list[float], periods_per_year: int = 252) -> float | None:
        """Sharpe (rf=0) ze sklejonych zwrotów OOS; ``None`` gdy nieobliczalny.

        Dokładna agregacja zamiast średniej arytmetycznej Sharpe'ów per okno
        (review 2026-07-16) — średnia ignoruje różne długości okien i zmienność
        między oknami. ``None`` (brak krzywych kapitału / zerowa zmienność) →
        wywołujący spada na średnią per okno.
        """
        if len(returns) < 2:
            return None
        mean = sum(returns) / len(returns)
        var = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
        if var <= 0.0:
            return None
        return mean / math.sqrt(var) * math.sqrt(periods_per_year)

    def run_wfo(
        self,
        data: pd.DataFrame,
        parameters: dict[str, Any],
        config: WfoConfig | None = None,
    ) -> dict[str, Any]:
        """Wykonaj pełną walk-forward optimization.

        Dla każdego okna: jeśli podano ``config.param_bounds`` — optymalizacja
        parametrów na danych in-sample przez ``OptunaOptimizer`` (reuse, bez
        duplikacji logiki; najlepsze parametry poprzedniego okna są warm startem
        kolejnego); w przeciwnym razie używane są stałe ``parameters`` (czysta
        ewaluacja walk-forward). Następnie backtest out-of-sample na najlepszych
        parametrach.

        Odporność na awarie (review 2026-07-16): błąd pojedynczego okna trafia do
        jego raportu (``error``) i okno jest WYKLUCZONE z agregatów; awaria
        wszystkich okien podnosi ``RuntimeError`` (job kończy się FAILED, nie
        pseudo-sukcesem z zerami).

        Parameters
        ----------
        data : pd.DataFrame
            Dane rynkowe z kolumną ``close`` i ``DatetimeIndex``.
        parameters : dict[str, Any]
            Bazowe parametry strategii (nadpisywane przez wynik optymalizacji IS).
            Wartości-listy (uruchamiające gałąź wektoryzowaną silnika) są odrzucane.
        config : WfoConfig | None
            Konfiguracja przebiegu (okna, tryb, bounds, metryka); ``None`` → domyślna.

        Returns
        -------
        dict[str, Any]
            Raport: metryki per okno (``trials``), łączne metryki OOS
            (``overall_metrics``: zwrot składany geometrycznie, Sharpe ze
            sklejonych zwrotów OOS z fallbackiem na średnią per okno) oraz
            ``best_params``/``best_value`` (wartość metryki celu w najlepszym
            oknie OOS) dla JobService.
        """
        config = config or WfoConfig()
        if "close" not in data.columns:
            raise KeyError("close")
        if not isinstance(data.index, pd.DatetimeIndex):
            data = data.copy()
            data.index = pd.to_datetime(data.index)

        # Parametry-listy przełączają run_backtest w tryb wektoryzowany (bez klucza
        # "metrics") — w WFO to zawsze błąd użytkownika, odrzucamy jawnie na wejściu
        list_params = sorted(k for k, v in parameters.items() if isinstance(v, (list, tuple)))
        if list_params:
            raise ValueError(
                f"WFO does not support list-valued (vectorized) parameters: {list_params}. "
                "Use param_bounds for per-window optimization instead."
            )

        logger.info(
            "Starting Walk-Forward Optimization | window={} step={} mode={} optimize={}",
            config.window_size,
            config.step_size,
            config.mode,
            bool(config.param_bounds),
        )

        windows = self.split_windows(
            data.index, config.window_size, config.step_size, config.mode
        )
        if not windows:
            raise ValueError(
                f"Data range too short for WFO: need at least window_size "
                f"({config.window_size}) plus one out-of-sample observation "
                f"(step_size={config.step_size}); got {len(data)} rows spanning "
                f"{data.index[0].date()} → {data.index[-1].date()}."
            )

        window_reports: list[dict[str, Any]] = []
        stitched_returns: list[float] = []
        warm_start: dict[str, Any] | None = None
        for i, bounds in enumerate(windows):
            report, opt_best, oos_returns = self._evaluate_window(
                data, i, bounds, parameters, config, warm_start
            )
            window_reports.append(report)
            stitched_returns.extend(oos_returns)
            if opt_best:
                warm_start = opt_best

        # 3) Agregacja metryk OOS — wyłącznie z okien udanych; komplet awarii = błąd jobu
        successful = [w for w in window_reports if "error" not in w]
        if not successful:
            details = "; ".join(
                f"window {w['window_index']}: {w['error']}" for w in window_reports
            )
            raise RuntimeError(
                f"All {len(window_reports)} WFO windows failed: {details}"
            )

        compound = 1.0
        for report in successful:
            compound *= 1.0 + report["oos_metrics"]["Total Return [%]"] / 100.0

        # Audyt 2026-07-17: annualizacja wg timeframe'u danych (wcześniej sztywne 252)
        overall_sharpe = self._annualized_sharpe(
            stitched_returns,
            periods_per_year_for_timeframe(parameters.get("timeframe", "1d")),
        )
        if overall_sharpe is None:
            # Fallback (silnik bez equity_curve, np. atrapy w testach): średnia per okno
            overall_sharpe = sum(w["oos_metrics"]["Sharpe Ratio"] for w in successful) / len(
                successful
            )

        overall_metrics = {
            "Total Return [%]": finite_or_zero((compound - 1.0) * 100.0),
            "Sharpe Ratio": finite_or_zero(overall_sharpe),
        }

        # Najlepsze okno wg metryki celu (zawsze obecnej w oos_metrics)
        best_window = max(successful, key=lambda w: w["oos_metrics"][config.metric])

        logger.info(
            "WFO completed | windows={} failed={} overall_return={:.2f}% overall_sharpe={:.2f}",
            len(window_reports),
            len(window_reports) - len(successful),
            overall_metrics["Total Return [%]"],
            overall_metrics["Sharpe Ratio"],
        )

        return {
            "status": "COMPLETED",
            "method": "walk_forward",
            "mode": config.mode,
            "window": config.window_size,
            "step": config.step_size,
            "n_windows": len(window_reports),
            "n_failed_windows": len(window_reports) - len(successful),
            "overall_metrics": overall_metrics,
            # Kontrakt JobService: best_parameters / best_value / trials_data w DB;
            # best_value = wartość metryki celu w najlepszym oknie OOS (spójnie
            # z kontraktem OptunaOptimizer: best_value = wynik najlepszego triala)
            "best_params": best_window["best_params"],
            "best_value": best_window["oos_metrics"][config.metric],
            "trials": window_reports,
        }
