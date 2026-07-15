"""
run_vectorbt_backtest — Phase 3 background task entry-point.

This is the main orchestrator for async background backtesting.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from loguru import logger

from app.db.session import get_session
from app.models.orm import JobStatus
from app.services.connectors.registry import ConnectorRegistry
from app.services.engine.job_service import JobService
from app.services.engine.loader import EngineLoader
from app.services.engine.opensource_engine import _setup_vbt
from app.services.engine.optimizer import OptunaOptimizer, WalkForwardOptimizer

# Initialize vbt once — reeksportowane i używane przez app.api.indicators (NIE usuwać)
try:
    vbt = _setup_vbt()
except Exception:  # noqa: BLE001 — fallback gdy vbt niedostępne przy imporcie
    vbt = None
    logger.warning("runner: _setup_vbt() nieudane przy imporcie — vbt=None")


def _serialize_metric_value(v: Any) -> Any:
    """Faza 10: pojedyncza metryka → typ JSON-safe (skalar/np/pd → python; NaN/inf → None)."""
    try:
        if isinstance(v, (np.ndarray, pd.Series)):
            val = v.iloc[0] if hasattr(v, "iloc") else v[0]
            return float(val)
        if isinstance(v, (np.integer, int)):
            return int(v)
        if isinstance(v, (np.floating, float)):
            if np.isnan(v) or np.isinf(v):
                return None
            return float(v)
        return float(v)
    except (TypeError, ValueError):
        return v if isinstance(v, (str, type(None))) else str(v)


def _serialize_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    """Faza 10: serializacja metryk z rekursją 1 poziom.

    Gdy wartość jest słownikiem (nested per-symbol, np. ``{"AAPL": {...}}``) — serializuje
    jego wartości wewnętrzne, ZACHOWUJĄC zagnieżdżenie (nie spłaszcza multi-symbol).
    W przeciwnym razie serializuje skalar.
    """
    out: dict[str, Any] = {}
    for k, v in metrics.items():
        if isinstance(v, dict):
            out[k] = {ik: _serialize_metric_value(iv) for ik, iv in v.items()}
        else:
            out[k] = _serialize_metric_value(v)
    return out


def _fetch_market_data(source: str, symbol: str | list[str], start: str, end: str, timeframe: str) -> Any:
    """Helper to grab market data via Connector Registry."""
    logger.info(f"BacktestRunner: fetching data | source={source} symbol={symbol} {start} → {end} {timeframe}")
    connector = ConnectorRegistry.get(source)
    df = connector.fetch(symbol, start, end, timeframe)
    logger.info(f"BacktestRunner: fetched {len(df)} rows from {source}")
    return df


def _execute_backtest(parameters: dict[str, Any]) -> dict[str, Any]:
    """Internal execution logic for a single backtest run."""
    # Get Engine (BYOL adapter)
    engine = EngineLoader.load()
    
    if "dag" in parameters:
        return _execute_dag_backtest(engine, parameters["dag"])

    logger.warning("Using legacy non-DAG backtest path. This is deprecated and will be removed in future versions.")
    source = parameters.get("data_source", "yahoo")
    symbol = parameters.get("symbol", "AAPL")
    start = parameters.get("start_date", "2020-01-01")
    end = parameters.get("end_date", "2023-01-01")
    timeframe = parameters.get("timeframe", "1d")

    df = _fetch_market_data(source, symbol, start, end, timeframe)
    if df.empty:
        raise ValueError(f"No data returned for {symbol} from {source}.")

    logger.debug(f"BacktestRunner: executing strategy via {engine.__class__.__name__}...")
    result = engine.run_backtest(df, parameters)
    
    # Extract metrics robustly
    metrics = result.get("metrics", {})
    if not metrics:
        # Fallback for engines returning flat results or vectorized
        if result.get("is_vectorized"):
            # For vectorized, we might want to return the whole list or a summary
            return result
            
        metrics = {
            "Total Return [%]": result.get("total_return_pct"),
            "Sharpe Ratio": result.get("sharpe_ratio"),
            "Max Drawdown [%]": result.get("max_drawdown_pct"),
            "Total Trades": result.get("num_trades"),
            "Final Value": result.get("final_capital"),
        }
        # If still empty, try extracting from raw if it exists
        if not any(v is not None for v in metrics.values()) and "raw" in result:
             metrics.update(result["raw"])

    # Convert numeric types to basic python floats/ints for JSON serialization
    return _serialize_metrics(metrics)


def _execute_dag_backtest(engine, dag_dict: dict[str, Any]) -> dict[str, Any]:
    nodes = dag_dict.get("nodes", [])
    data_node = next((n for n in nodes if n.get("category") == "DataIngestion"), None)
    if not data_node:
        raise ValueError("No DataIngestion node found in DAG.")
    
    params = data_node.get("params", {})
    source = params.get("dataSource", params.get("data_source", "yahoo"))
    symbol = params.get("symbol", "AAPL")
    start = params.get("startDate", params.get("start_date", "2020-01-01"))
    end = params.get("endDate", params.get("end_date", "2023-01-01"))
    timeframe = params.get("timeframe", "1d")

    df = _fetch_market_data(source, symbol, start, end, timeframe)
    if df.empty:
        raise ValueError(f"No data returned for {symbol} from {source}.")

    logger.debug(f"BacktestRunner: executing DAG strategy via {engine.__class__.__name__}...")
    
    # We must assume the engine has a run_dag_backtest method implemented.
    if not hasattr(engine, "run_dag_backtest"):
        raise NotImplementedError(f"{engine.__class__.__name__} does not support run_dag_backtest")
        
    result = engine.run_dag_backtest(df, dag_dict)
    
    # Extract metrics safely
    metrics = result.get("metrics", {})
    if not metrics:
        metrics = {
            "Total Return [%]": result.get("total_return_pct"),
            "Sharpe Ratio": result.get("sharpe_ratio"),
            "Max Drawdown [%]": result.get("max_drawdown_pct"),
            "Total Trades": result.get("num_trades"),
            "Final Value": result.get("final_capital"),
        }
        if not any(v is not None for v in metrics.values()) and "raw" in result:
             metrics.update(result["raw"])

    safe_metrics = _serialize_metrics(metrics)

    # Faza 10: przenieś pola multi-symbol / krzywą kapitału z wyniku silnika (nie gub ich).
    payload: dict[str, Any] = dict(safe_metrics)
    for key in ("equity_curve", "is_multi_symbol", "symbols"):
        if key in result:
            payload[key] = result[key]

    return payload


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


def run_walk_forward(
    job_id: int,
    parameters: dict[str, Any],
    window_size: str,
    step_size: str,
) -> None:
    """Background worker for executing Walk-Forward Optimization."""
    logger.info(f"WFORunner: starting job_id={job_id} | window={window_size} step={step_size}")

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

        optimizer = WalkForwardOptimizer(engine)
        results = optimizer.run_wfo(df, parameters, window_size, step_size)

        with get_session() as db:
            JobService.update_optimization_status(db, job_id, JobStatus.COMPLETED, results=results)
        logger.success(f"WFORunner: job_id={job_id} COMPLETED.")

    except Exception as e:
        logger.exception(f"WFORunner: job_id={job_id} FAILED: {e}")
        with get_session() as db:
            JobService.update_optimization_status(db, job_id, JobStatus.FAILED, error_message=str(e))
