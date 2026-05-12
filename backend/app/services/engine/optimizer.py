"""
Phase 5 — Grid Search Optimizer for parameters.

Allows exhaustive Cartesian-product parameter searches using the open-source vectorbt library.
"""

from __future__ import annotations

import sys
import itertools
from typing import Any
from pathlib import Path

import optuna
import numpy as np
import pandas as pd
from loguru import logger

from app.core.config import settings

# Make vendored vectorbt importable
_VENDORED_VBT = settings.PROJECT_ROOT / "vectorbt_src"
if _VENDORED_VBT.exists() and str(_VENDORED_VBT) not in sys.path:
    sys.path.insert(0, str(_VENDORED_VBT))


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
        if base_parameters is None:
            base_parameters = {}

        try:
            import vectorbt as vbt  # type: ignore[import]
        except ImportError as exc:
            raise RuntimeError(
                "vectorbt is not importable. Ensure the vendored copy is intact "
                f"at {_VENDORED_VBT}."
            ) from exc

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
                combo_dict = dict(zip(keys, combinations[i]))
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
                b = bounds.dict() if hasattr(bounds, "dict") else bounds
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
                execution_result = self.engine.run_backtest(current_params, data)
                val = execution_result.get("metrics", {}).get(metric, 0.0)
                return float(val) if val is not None else 0.0
            except Exception as e:
                logger.error(f"Trial {trial.number} failed: {e}")
                return 0.0

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
