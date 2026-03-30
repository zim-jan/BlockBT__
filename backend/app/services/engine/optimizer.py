"""
Static parameter optimization module using Grid Search.

This module provides the GridSearchOptimizer class, which executes vectorized
parameter searches using the open-source vectorbt library.
"""

import itertools
import sys
from collections.abc import Callable
from typing import Any

import pandas as pd
from loguru import logger

from app.core.config import settings
from app.services.engine.base import BaseStrategyEngine

# Make vendored vectorbt importable
_VENDORED_VBT = settings.PROJECT_ROOT / "vectorbt"
if _VENDORED_VBT.exists() and str(_VENDORED_VBT) not in sys.path:
    sys.path.insert(0, str(_VENDORED_VBT))


class GridSearchOptimizer:
    """
    Executes a static grid search optimization for a given strategy.

    This optimizer generates a Cartesian product of all parameters in the
    `param_grid` to perform a fully vectorized backtest using vectorbt.
    Instead of passing lists directly (which could cause shape errors or
    MultiIndex conflicts), it generates perfectly matched flat lists for
    each parameter, ensuring that vectorbt's native broadcasting works
    efficiently and safely.
    """

    def __init__(
        self,
        engine: BaseStrategyEngine,
        indicator_layer: Callable[
            ..., tuple[pd.Series | pd.DataFrame, pd.Series | pd.DataFrame]
        ],
    ):
        """
        Initialize the optimizer.

        Args:
            engine: The strategy execution engine (e.g., OpenSourceEngine).
            indicator_layer: A callable that accepts a data DataFrame/Series and
                parameter lists as keyword arguments, and returns a tuple of
                (entries, exits) as vectorized boolean masks.
        """
        self.engine = engine
        self.indicator_layer = indicator_layer

    def optimize(
        self,
        data: pd.DataFrame,
        param_grid: dict[str, list[Any]],
        metric: str = "Total Return [%]",
    ) -> dict[str, Any]:
        """
        Run a vectorized grid search optimization.

        Args:
            data: Market data DataFrame (must contain 'close' column).
            param_grid: A dictionary where keys are parameter names and values are
                lists of parameter values to test.
            metric: The performance metric to maximize, exactly as it appears in
                vectorbt's `portfolio.stats()`. Defaults to 'Total Return [%]'.

        Returns:
            A dictionary containing the best parameter combination and its performance metrics.
        """
        try:
            import vectorbt as vbt  # type: ignore[import]
        except ImportError as exc:
            raise RuntimeError(
                "vectorbt is not importable. Ensure the vendored copy is intact "
                f"at {_VENDORED_VBT}."
            ) from exc

        if not param_grid:
            logger.warning("Empty param_grid provided to GridSearchOptimizer.")
            return {}

        keys = list(param_grid.keys())
        value_lists = [param_grid[k] for k in keys]

        # Generate Cartesian product of all parameters
        combinations = list(itertools.product(*value_lists))

        if not combinations:
            logger.warning("Empty param_grid provided to GridSearchOptimizer.")
            return {}

        # Transpose combinations to get a flat list for each parameter
        flat_args = list(zip(*combinations, strict=False))
        kwargs = {keys[i]: list(flat_args[i]) for i in range(len(keys))}

        logger.info(f"Running GridSearchOptimizer for {len(combinations)} combinations.")

        # Call indicator layer to get vectorized entries and exits
        entries, exits = self.indicator_layer(data, **kwargs)

        if isinstance(data, pd.DataFrame) and "close" in data.columns:
            close = data["close"]
        else:
            close = data

        portfolio = vbt.Portfolio.from_signals(
            close,
            entries=entries,
            exits=exits,
            freq="D",
        )

        try:
            stats_df = portfolio.stats(agg_func=None)
        except Exception as e:
            logger.error(f"Failed to generate stats from vectorbt portfolio: {e}")
            return {}

        # If there's only one combination, stats_df is a Series instead of a DataFrame
        if isinstance(stats_df, pd.Series):
            if metric not in stats_df.index:
                logger.error(f"Metric '{metric}' not found in vectorbt stats.")
                return {}
            # For a single combination, we handle it explicitly
            best_idx = 0
            best_metric_val = stats_df[metric]
            best_params = {keys[i]: combinations[0][i] for i in range(len(keys))}
            best_stats = stats_df.to_dict()

            logger.info(
                f"Optimization finished. Best combination: {best_params} "
                f"with {metric} = {best_metric_val}"
            )

            return {
                "best_params": best_params,
                "best_metric_value": best_metric_val,
                "metric_name": metric,
                "stats": best_stats,
            }

        if metric not in stats_df.columns:
            logger.error(f"Metric '{metric}' not found in vectorbt stats.")
            return {}

        metric_series = stats_df[metric]

        try:
            best_idx = metric_series.argmax()
        except Exception:
            best_idx = metric_series.fillna(-float("inf")).argmax()

        best_metric_val = metric_series.iloc[best_idx]
        best_combination_tuple = combinations[best_idx]

        best_params = {keys[i]: best_combination_tuple[i] for i in range(len(keys))}
        best_stats = stats_df.iloc[best_idx].to_dict()

        logger.info(
            f"Optimization finished. Best combination: {best_params} "
            f"with {metric} = {best_metric_val}"
        )

        return {
            "best_params": best_params,
            "best_metric_value": best_metric_val,
            "metric_name": metric,
            "stats": best_stats,
        }
