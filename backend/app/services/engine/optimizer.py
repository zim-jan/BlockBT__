"""
Phase 5 — Grid Search Optimizer for parameters.

Allows exhaustive Cartesian-product parameter searches using the open-source vectorbt library.
"""

from __future__ import annotations

import itertools
import math
from typing import Any

import optuna
import pandas as pd
from loguru import logger

from app.services.engine.opensource_engine import _setup_vbt

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
    ) -> dict[str, Any]:
        """Run Bayesian optimization.

        param_bounds: dict mapping param_name -> {min, max, type, ...}
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

    @staticmethod
    def _finite_or_zero(value: Any) -> float:
        """Guard NaN/inf → 0.0 (spójnie z konwencją silnika dla metryk)."""
        try:
            v = float(value)
        except (TypeError, ValueError):
            return 0.0
        if math.isnan(v) or math.isinf(v):
            return 0.0
        return v

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

        is_td = pd.Timedelta(window_size)
        oos_td = pd.Timedelta(step_size)
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
            has_is = bool(((index >= is_start) & (index < is_end)).any())
            has_oos = bool(((index >= is_end) & (index < oos_end)).any())
            if has_is and has_oos:
                windows.append((is_start, is_end, is_end, oos_end))
            k += 1

        return windows

    def run_wfo(
        self,
        data: pd.DataFrame,
        parameters: dict[str, Any],
        window_size: str = "365d",
        step_size: str = "90d",
        mode: str = "rolling",
        param_bounds: dict[str, Any] | None = None,
        n_trials: int = 15,
        metric: str = "Total Return [%]",
    ) -> dict[str, Any]:
        """Wykonaj pełną walk-forward optimization.

        Dla każdego okna: jeśli podano ``param_bounds`` — optymalizacja parametrów
        na danych in-sample przez ``OptunaOptimizer`` (reuse, bez duplikacji logiki);
        w przeciwnym razie używane są stałe ``parameters`` (czysta ewaluacja
        walk-forward). Następnie backtest out-of-sample na najlepszych parametrach.

        Parameters
        ----------
        data : pd.DataFrame
            Dane rynkowe z kolumną ``close`` i ``DatetimeIndex``.
        parameters : dict[str, Any]
            Bazowe parametry strategii (nadpisywane przez wynik optymalizacji IS).
        window_size : str
            Długość okna in-sample (``pd.Timedelta``, np. ``"365d"``).
        step_size : str
            Długość okna out-of-sample i krok przesuwu (np. ``"90d"``).
        mode : str
            ``"rolling"`` lub ``"anchored"``.
        param_bounds : dict[str, Any] | None
            Zakresy parametrów dla optymalizacji IS (format ``OptunaOptimizer``);
            ``None`` → brak optymalizacji, stałe parametry.
        n_trials : int
            Liczba prób Optuny per okno (ignorowane bez ``param_bounds``).
        metric : str
            Metryka celu optymalizacji i wyboru najlepszego okna OOS.

        Returns
        -------
        dict[str, Any]
            Raport: metryki per okno (``windows``/``trials``), łączne metryki OOS
            (``overall_metrics``: zwrot składany geometrycznie, średni Sharpe;
            guard NaN/inf → 0.0) oraz ``best_params``/``best_value`` dla JobService.
        """
        if "close" not in data.columns:
            raise KeyError("close")
        if not isinstance(data.index, pd.DatetimeIndex):
            data = data.copy()
            data.index = pd.to_datetime(data.index)

        logger.info(
            "Starting Walk-Forward Optimization | window={} step={} mode={} optimize={}",
            window_size,
            step_size,
            mode,
            bool(param_bounds),
        )

        windows = self.split_windows(data.index, window_size, step_size, mode)
        if not windows:
            raise ValueError(
                f"Data range too short for WFO: need at least window_size ({window_size}) "
                f"plus one out-of-sample observation (step_size={step_size})."
            )

        idx = data.index
        window_reports: list[dict[str, Any]] = []

        for i, (is_start, is_end, oos_start, oos_end) in enumerate(windows):
            is_df = data.loc[(idx >= is_start) & (idx < is_end)]
            oos_df = data.loc[(idx >= oos_start) & (idx < oos_end)]

            # 1) Optymalizacja in-sample (reuse istniejącego OptunaOptimizer)
            if param_bounds:
                optimizer = OptunaOptimizer(self.engine)
                opt_result = optimizer.run_optimization(
                    param_bounds, is_df, parameters, n_trials=n_trials, metric=metric
                )
                best_params = {**parameters, **opt_result.get("best_params", {})}
            else:
                best_params = dict(parameters)

            # 2) Backtest out-of-sample na najlepszych parametrach
            error_msg: str | None = None
            try:
                oos_result = self.engine.run_backtest(oos_df, best_params)
                oos_raw = oos_result.get("metrics", {})
            except Exception as e:  # noqa: BLE001 — pojedyncze okno nie zrywa całego WFO
                logger.error("WFO window {} OOS backtest failed: {}", i, e)
                oos_raw = {}
                error_msg = str(e)

            oos_metrics = {
                "Total Return [%]": self._finite_or_zero(oos_raw.get("Total Return [%]")),
                "Sharpe Ratio": self._finite_or_zero(oos_raw.get("Sharpe Ratio")),
            }

            report: dict[str, Any] = {
                "window_index": i,
                "is_start": is_start.isoformat(),
                "is_end": is_end.isoformat(),
                "oos_start": oos_start.isoformat(),
                "oos_end": oos_end.isoformat(),
                "is_rows": int(len(is_df)),
                "oos_rows": int(len(oos_df)),
                "best_params": best_params,
                "oos_metrics": oos_metrics,
            }
            if error_msg is not None:
                report["error"] = error_msg
            window_reports.append(report)

        # 3) Agregacja metryk OOS: zwrot składany geometrycznie + średni Sharpe
        compound = 1.0
        sharpe_sum = 0.0
        for report in window_reports:
            compound *= 1.0 + report["oos_metrics"]["Total Return [%]"] / 100.0
            sharpe_sum += report["oos_metrics"]["Sharpe Ratio"]

        overall_metrics = {
            "Total Return [%]": self._finite_or_zero((compound - 1.0) * 100.0),
            "Sharpe Ratio": self._finite_or_zero(sharpe_sum / len(window_reports)),
        }

        # Najlepsze okno wg metryki celu (fallback: Total Return [%])
        best_window = max(
            window_reports,
            key=lambda w: w["oos_metrics"].get(metric, w["oos_metrics"]["Total Return [%]"]),
        )

        logger.info(
            "WFO completed | windows={} overall_return={:.2f}% overall_sharpe={:.2f}",
            len(window_reports),
            overall_metrics["Total Return [%]"],
            overall_metrics["Sharpe Ratio"],
        )

        return {
            "status": "COMPLETED",
            "method": "walk_forward",
            "mode": mode,
            "window": window_size,
            "step": step_size,
            "n_windows": len(window_reports),
            "windows": window_reports,
            "overall_metrics": overall_metrics,
            # Kontrakt JobService: best_parameters / best_value / trials_data w DB
            "best_params": best_window["best_params"],
            "best_value": overall_metrics["Total Return [%]"],
            "trials": window_reports,
        }
