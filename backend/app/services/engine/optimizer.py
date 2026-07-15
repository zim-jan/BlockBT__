"""
Phase 5 — Grid Search Optimizer for parameters.

Allows exhaustive Cartesian-product parameter searches using the open-source vectorbt library.
"""

from __future__ import annotations

import itertools
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
    """Implements Walk-Forward Optimization (WFO) using vectorbt."""

    def __init__(self, engine: Any) -> None:
        self.engine = engine

    def run_wfo(
        self,
        data: pd.DataFrame,
        parameters: dict[str, Any],
        window_size: str = "365d",
        step_size: str = "90d",
    ) -> dict[str, Any]:
        """Run a walk-forward optimization.

        UWAGA (review 2026-07-15): obecna implementacja to STUB — wykonuje pojedynczy
        backtest na całym zakresie danych; `window_size`/`step_size` są tylko echem w
        odpowiedzi, NIE ma realnego podziału in-sample/out-of-sample. Pełny rolling WFO
        (optymalizacja na train, ewaluacja na test) to osobne zadanie — patrz
        15072026-review/01-backend-code-review.md (MED). Nie prezentować jako pełne WFO.
        """
        logger.info("Starting Walk-Forward Optimization | window={} step={}", window_size, step_size)
        
        # In a real WFO, we would optimize on 'train' and test on 'test'
        # For MVP, we can use vectorbt's rolling splitters
        try:
            # Simple rolling execution for now
            # We'll enhance this to include optimization per window later
            result = self.engine.run_backtest(data, parameters)
            return {
                "status": "COMPLETED",
                "method": "rolling",
                "window": window_size,
                "step": step_size,
                "overall_metrics": result.get("metrics", {}),
            }
        except Exception as e:
            logger.error("WFO failed: {}", e)
            raise
