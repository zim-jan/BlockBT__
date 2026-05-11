"""
Phase 5 — Grid Search Optimizer for parameters.

Allows exhaustive Cartesian-product parameter searches using the open-source vectorbt library.
"""

from __future__ import annotations

import sys
import itertools
from typing import Any
from pathlib import Path

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

    def __init__(self, engine_instance: Any) -> None:
        """Initialize the optimizer with a compatible BaseStrategyEngine instance.

        Parameters
        ----------
        engine_instance : BaseStrategyEngine
            Instance of the execution engine (OpenSourceEngine or ProEngine).
        """
        self.engine = engine_instance

    def run_optimization(
        self,
        param_grid: dict[str, list[Any]],
        data: pd.DataFrame,
        base_parameters: dict[str, Any],
        metric: str = "Total Return [%]",
    ) -> list[dict[str, Any]]:
        """Run grid search optimization over all parameter combinations.

        Parameters
        ----------
        param_grid : dict[str, list[Any]]
            A dictionary where keys are parameter names and values are lists of discrete values to test. (e.g., {"sma_fast": [5, 10, 15], "sma_slow": [20, 30]}).
        data : pd.DataFrame
            Market data.
        base_parameters : dict[str, Any]
            The baseline parameters. Keys present in the `param_grid` will overwrite these.
        metric : str, optional
            The performance metric to extract from the returned results, must exactly match a key in vectorbt's `portfolio.stats()`. Defaults to 'Total Return [%]'.

        Returns
        -------
        list[dict[str, Any]]
            A list of result dictionaries, each containing the 'parameters' used and the resulting 'metrics'.
        """
        try:
            import vectorbt as vbt  # type: ignore[import]
        except ImportError as exc:
            raise RuntimeError(
                "vectorbt is not importable. Ensure the vendored copy is intact "
                f"at {_VENDORED_VBT}."
            ) from exc

        # 1. Generate all flat combinations
        keys = list(param_grid.keys())
        value_lists = list(param_grid.values())

        # Cartesian product of all value lists
        combinations = list(itertools.product(*value_lists))

        logger.info(
            "Starting Grid Search: evaluating {} combinations for parameters: {}",
            len(combinations),
            keys,
        )

        results: list[dict[str, Any]] = []

        # 2. Iterate combinations (Flat iteration for stability in OSS vectorbt)
        # Note: True vectorization of entire grids is difficult without Pro,
        # so we iterate. The engine itself still runs vectorized per-iteration.
        for combo in combinations:
            # Create a localized parameter payload
            current_params = base_parameters.copy()
            combo_dict = dict(zip(keys, combo))
            current_params.update(combo_dict)

            logger.debug("Testing grid parameters: {}", combo_dict)

            # 3. Execute
            try:
                # We expect the engine to return a flat dictionary mapping metrics -> values
                execution_result = self.engine.run_backtest(current_params, data)
                metrics_output = execution_result.get("metrics", {})

                # Construct a clean result object
                run_record = {
                    "parameters": combo_dict,
                    "metrics": metrics_output,
                }

                results.append(run_record)

            except Exception as e:
                logger.error(f"Failed to generate stats from vectorbt portfolio: {e}")
                # Append a failed marker
                results.append({"parameters": combo_dict, "metrics": {metric: float("-inf")}})

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
