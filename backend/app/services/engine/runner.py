"""
run_vectorbt_backtest — Phase 3 background task entry-point.

This is the main orchestrator for async background backtesting.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from loguru import logger

from app.db.session import get_session
from app.models.orm import JobStatus
from app.services.connectors.registry import ConnectorRegistry
from app.services.engine.loader import EngineLoader
from app.services.engine.optimizer import OptunaOptimizer
from app.services.engine.job_service import JobService

# Ensure the vendored vectorbt directory is importable.
_VENDORED_VBT = Path(__file__).resolve().parents[4] / "vectorbt_src"
if _VENDORED_VBT.exists() and str(_VENDORED_VBT) not in sys.path:
    sys.path.insert(0, str(_VENDORED_VBT))

import vectorbt  # noqa: F401


def _fetch_market_data(source: str, symbol: str, start: str, end: str, timeframe: str) -> Any:
    """Helper to grab market data via Connector Registry."""
    logger.info(f"BacktestRunner: fetching data | source={source} symbol={symbol} {start} → {end} {timeframe}")
    connector = ConnectorRegistry.get(source)
    df = connector.fetch(symbol, start, end, timeframe)
    logger.info(f"BacktestRunner: fetched {len(df)} rows from {source}")
    return df


def _execute_backtest(parameters: dict[str, Any]) -> dict[str, Any]:
    """Internal execution logic for a single backtest run."""
    source = parameters.get("data_source", "yahoo")
    symbol = parameters.get("symbol", "AAPL")
    start = parameters.get("start_date", "2020-01-01")
    end = parameters.get("end_date", "2023-01-01")
    timeframe = parameters.get("timeframe", "1d")

    df = _fetch_market_data(source, symbol, start, end, timeframe)
    if df.empty:
        raise ValueError(f"No data returned for {symbol} from {source}.")

    # Get Engine (BYOL adapter)
    engine = EngineLoader.load()
    
    logger.debug(f"BacktestRunner: executing strategy via {engine.__class__.__name__}...")
    result = engine.run_backtest(parameters, df)
    metrics = result.get("metrics", {})

    # Convert numeric types to basic python floats/ints for JSON serialization
    safe_metrics = {}
    for k, v in metrics.items():
        try:
            if isinstance(v, (np.ndarray, pd.Series)):
                val = v.iloc[0] if hasattr(v, "iloc") else v[0]
                safe_metrics[k] = float(val)
            elif isinstance(v, (np.integer, int)):
                safe_metrics[k] = int(v)
            elif isinstance(v, (np.floating, float)):
                if np.isnan(v) or np.isinf(v):
                    safe_metrics[k] = None
                else:
                    safe_metrics[k] = float(v)
            else:
                safe_metrics[k] = float(v)
        except (TypeError, ValueError):
            safe_metrics[k] = v if isinstance(v, (str, type(None))) else str(v)

    return safe_metrics


def run_vectorbt_backtest(job_id: int, parameters: dict[str, Any]) -> None:
    """Background worker for executing a backtest."""
    logger.debug(f"BacktestRunner: processing job_id={job_id} in background...")
    
    with get_session() as db:
        JobService.update_backtest_status(db, job_id, JobStatus.RUNNING)

    try:
        metrics = _execute_backtest(parameters)
        with get_session() as db:
            JobService.update_backtest_status(db, job_id, JobStatus.COMPLETED, metrics)
        logger.success(f"BacktestRunner: job_id={job_id} COMPLETED successfully.")

    except Exception as e:
        logger.exception(f"BacktestRunner: job_id={job_id} FAILED: {e}")
        error_metrics = {
            "error_msg": str(e),
            "Total Return [%]": 0.0,
            "Benchmark Return [%]": 0.0,
            "Max Drawdown [%]": 0.0,
            "Sharpe Ratio": 0.0,
            "Total Trades": 0,
            "Final Value": 0.0,
            "Win Rate [%]": 0.0,
        }
        with get_session() as db:
            JobService.update_backtest_status(db, job_id, JobStatus.FAILED, error_metrics, error_message=str(e))


def run_optuna_optimization(
    job_id: int,
    parameters: dict[str, Any],
    bounds: dict[str, Any],
    n_trials: int,
    metric: str,
) -> None:
    """Background worker for executing an Optuna optimization study."""
    logger.info(f"OptunaRunner: starting job_id={job_id} | trials={n_trials}")

    with get_session() as db:
        JobService.update_optimization_status(db, job_id, JobStatus.RUNNING)

    try:
        source = parameters.get("data_source", "yahoo")
        symbol = parameters.get("symbol", "AAPL")
        start = parameters.get("start_date")
        end = parameters.get("end_date")
        tf = parameters.get("timeframe", "1d")

        df = _fetch_market_data(source, symbol, start, end, tf)
        engine = EngineLoader.load()

        optimizer = OptunaOptimizer(engine)
        results = optimizer.run_optimization(bounds, df, parameters, n_trials, metric)

        with get_session() as db:
            JobService.update_optimization_status(db, job_id, JobStatus.COMPLETED, results=results)
        logger.success(f"OptunaRunner: job_id={job_id} COMPLETED.")

    except Exception as e:
        logger.exception(f"OptunaRunner: job_id={job_id} FAILED: {e}")
        with get_session() as db:
            JobService.update_optimization_status(db, job_id, JobStatus.FAILED, error_message=str(e))
