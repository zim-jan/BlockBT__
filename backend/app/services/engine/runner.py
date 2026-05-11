"""
run_vectorbt_backtest — Phase 3 background task entry-point.

This is the main orchestrator for async background backtesting.
"""

from __future__ import annotations

import sys
from typing import Any
from pathlib import Path
from loguru import logger

from app.db.session import get_session
from app.models.orm import BacktestJob
from app.services.connectors.registry import ConnectorRegistry
from app.services.engine.loader import EngineLoader

# Ensure the vendored vectorbt directory is importable.
# This prevents mistakenly turning the repo's vectorbt folder into a namespace package
_VENDORED_VBT = Path(__file__).resolve().parents[4] / "vectorbt_src"
if _VENDORED_VBT.exists() and str(_VENDORED_VBT) not in sys.path:
    sys.path.insert(0, str(_VENDORED_VBT))

import vectorbt  # noqa: F401 — ensure it loads the real __init__.py


def _update_job_status(job_id: int, status: str, metrics: dict[str, Any] | None = None) -> None:
    """Helper to update SQLite job state."""
    with get_session() as db:
        job = db.query(BacktestJob).get(job_id)
        if not job:
            logger.warning(f"BacktestRunner: job_id={job_id} not found in DB.")
            return

        job.status = status
        if metrics:
            job.metrics = metrics
            job.total_return_pct = metrics.get("Total Return [%]")
            job.sharpe_ratio = metrics.get("Sharpe Ratio")
            job.max_drawdown_pct = metrics.get("Max Drawdown [%]")
            job.num_trades = metrics.get("Total Trades")
            job.final_capital = metrics.get("Final Value")

        db.commit()


def _fetch_market_data(source: str, symbol: str, start: str, end: str, timeframe: str) -> Any:
    """Helper to grab market data via Connector Registry."""
    logger.info(f"BacktestRunner: fetching data | source={source} symbol={symbol} {start} → {end} {timeframe}")
    connector = ConnectorRegistry.get(source)
    df = connector.fetch(symbol, start, end, timeframe)
    logger.info(f"BacktestRunner: fetched {len(df)} rows from {source}")
    return df


def _execute_backtest(parameters: dict[str, Any]) -> dict[str, Any]:
    """Run a vectorbt backtest with configurable data source and strategy.

    1. Fetches data.
    2. Instantiates correct Engine (OSS or Pro).
    3. Runs backtest and returns flat metrics dictionary.
    """
    try:
        import vectorbt as vbt  # type: ignore[import]
    except ImportError as exc:
        raise RuntimeError(
            f"vectorbt is not importable. Checked vendored path: {_VENDORED_VBT}"
        ) from exc

    source = parameters.get("data_source", "yahoo")
    symbol = parameters.get("symbol", "AAPL")
    start = parameters.get("start_date", "2020-01-01")
    end = parameters.get("end_date", "2023-01-01")
    timeframe = parameters.get("timeframe", "1d")
    strategy = parameters.get("strategy_type", "sma_crossover")

    logger.info(
        f"BacktestRunner: starting | source={source} symbol={symbol} strategy={strategy} "
        f"sma=({parameters.get('sma_fast', 10)}/{parameters.get('sma_slow', 30)}) "
        f"capital={parameters.get('initial_capital', 10000.0)}"
    )

    df = _fetch_market_data(source, symbol, start, end, timeframe)

    if df.empty:
        raise ValueError(f"No data returned for {symbol} from {source}.")

    # Fast validation
    if len(df) < 50:
        logger.warning(f"BacktestRunner: extremely small dataset ({len(df)} rows).")

    # Get Engine (BYOL adapter)
    engine = EngineLoader.load()

    # The engine handles building signals and running vectorbt.Portfolio
    logger.debug(f"BacktestRunner: executing strategy via {engine.__class__.__name__}...")
    metrics = engine.run_backtest(parameters, df)

    # Convert numeric types to basic python floats/ints for JSON serialization
    safe_metrics = {}
    for k, v in metrics.get("metrics", {}).items():
        if isinstance(v, (vbt.tp.Array1d, np.ndarray, pd.Series)):
            safe_metrics[k] = float(v.iloc[0] if hasattr(v, "iloc") else v[0])
        elif isinstance(v, (np.float64, np.float32, float)):
            if np.isnan(v) or np.isinf(v):
                safe_metrics[k] = None
            else:
                safe_metrics[k] = float(v)
        elif isinstance(v, (np.int64, np.int32, int)):
            safe_metrics[k] = int(v)
        else:
            safe_metrics[k] = v

    return {
        "status": "COMPLETED",
        "engine": "vectorbt-opensource",
        "library": "vectorbt (open-source)",
        "vbt_version": getattr(vbt, "__version__", "unknown"),
        "metrics": safe_metrics,
    }


def run_vectorbt_backtest(job_id: int, parameters: dict[str, Any]) -> None:
    """Background worker for executing a backtest.

    1. Marks job RUNNING.
    2. Calls internal execution logic.
    3. Saves metrics and marks COMPLETED.
    4. Handles errors and marks FAILED.
    """
    logger.debug(f"BacktestRunner: processing job_id={job_id} in background...")
    _update_job_status(job_id, "RUNNING")

    try:
        metrics = _execute_backtest(parameters)
        # Store successful metrics to DB
        _update_job_status(job_id, "COMPLETED", metrics["metrics"])
        logger.success(f"BacktestRunner: job_id={job_id} COMPLETED successfully.")

    except Exception as e:
        logger.exception(f"BacktestRunner: job_id={job_id} FAILED: {e}")
        # Build error metrics block for frontend consumption
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
        _update_job_status(job_id, "FAILED", error_metrics)
