from __future__ import annotations

from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from loguru import logger

from app.db.session import get_session
from app.models.orm import BacktestJob, JobStatus, Strategy
from app.schemas.backtest import BacktestJobResponse, BacktestRequest
from app.schemas.base import ApiResponse
from app.services.engine.runner import run_vectorbt_backtest

"""Trasy obsługujące backtestowanie — Faza 2.

Flow:
  POST /api/backtest/       → tworzy obiekt BacktestJob (PENDING), zwraca natychmiast job_id
  GET  /api/backtest/{id}   → służy do odpytywania statusu i metryk pracy zapisanej w SQLite.
"""

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _job_to_schema(job: BacktestJob) -> BacktestJobResponse:
    """Konwertuje model ORM BacktestJob na schemat BacktestJobResponse."""
    raw_metrics = job.metrics or {}
    params = job.parameters_snapshot or {}

    # Helper to find values in raw_metrics or job attributes
    def get_metric(json_key: str, db_attr: Any):
        val = raw_metrics.get(json_key)
        if val is None:
            return db_attr
        return val

    # Robust mapping for trades and capital - force types and handle None
    raw_trades = raw_metrics.get("Total Trades")
    if raw_trades is None:
        raw_trades = job.num_trades
    num_trades = int(raw_trades) if raw_trades is not None else 0

    raw_final = raw_metrics.get("Final Value")
    if raw_final is None:
        raw_final = job.final_capital
    final_capital = float(raw_final) if raw_final is not None else 0.0

    frontend_metrics = {
        "engine": raw_metrics.get("engine", "vectorbt-opensource"),
        "symbol": params.get("symbol", ""),
        "data_source": params.get("data_source", "yahoo"),
        "strategy_type": params.get("strategy_type", "sma_crossover"),
        "sma_fast": params.get("sma_fast", 10),
        "sma_slow": params.get("sma_slow", 30),
        "initial_capital": params.get("initial_capital", 10000.0),
        "total_return_pct": get_metric("Total Return [%]", job.total_return_pct),
        "sharpe_ratio": get_metric("Sharpe Ratio", job.sharpe_ratio),
        "max_drawdown_pct": get_metric("Max Drawdown [%]", job.max_drawdown_pct),
        "win_rate_pct": raw_metrics.get("Win Rate [%]"),
        "num_trades": num_trades,
        "final_capital": final_capital,
    }

    # Populate metrics ONLY if status is COMPLETED
    is_completed = (job.status == JobStatus.COMPLETED or job.status == "COMPLETED")
    
    return BacktestJobResponse(
        id=job.id,
        job_id=job.id,
        strategy_id=job.strategy_id,
        status=job.status,
        symbol=params.get("symbol", ""),
        timeframe=params.get("timeframe", ""),
        start_date=params.get("start_date", ""),
        end_date=params.get("end_date", ""),
        initial_capital=params.get("initial_capital", 10000.0),
        created_at=job.created_at,
        metrics=frontend_metrics if is_completed else None,
        parameters=params,
        error_message=job.error_message,
        total_return_pct=job.total_return_pct,
        sharpe_ratio=job.sharpe_ratio,
        max_drawdown_pct=job.max_drawdown_pct,
        num_trades=job.num_trades,
        final_capital=job.final_capital,
    )


# ---------------------------------------------------------------------------
# API Routes
# ---------------------------------------------------------------------------


@router.post("/", summary="Wyzwalanie backtestu", status_code=202, response_model=ApiResponse[BacktestJobResponse])
def trigger_backtest(
    payload: BacktestRequest,
    background_tasks: BackgroundTasks,
) -> ApiResponse[BacktestJobResponse]:
    """Tworzy rekord BacktestJob o statusie PENDING, planuje wykonanie w tle i natychmiastowo
    zwraca jego identyfikator."""
    with get_session() as db:
        strategy = db.get(Strategy, payload.strategy_id)
        if not strategy:
            raise HTTPException(
                status_code=404,
                detail=f"Strategy id={payload.strategy_id} not found",
            )

        # Merge strategy parameters with any per-request overrides
        params: dict[str, Any] = dict(strategy.parameters)
        params["code_content"] = strategy.code_content
        overrides = payload.model_dump(exclude_unset=True, exclude={"strategy_id", "parameters"})
        params.update(overrides)
        if payload.parameters:
            params.update(payload.parameters)

        job = BacktestJob(
            strategy_id=strategy.id,
            status=JobStatus.PENDING,
            parameters_snapshot=params,
        )
        db.add(job)
        db.flush()
        data = _job_to_schema(job)

    # Enqueue the engine — runs in FastAPI's background thread pool
    background_tasks.add_task(run_vectorbt_backtest, job.id, params)

    return ApiResponse(success=True, data=data)


@router.get("/{job_id}", summary="Pobieranie statusu pojedynczego zadania", response_model=ApiResponse[BacktestJobResponse])
def get_backtest_status(job_id: int) -> ApiResponse[BacktestJobResponse]:
    """Zwraca aktualny status i wyniki wyliczonych metryk określonego zadania."""
    with get_session() as db:
        job = db.get(BacktestJob, job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job id={job_id} not found")
        db.refresh(job)  # Force refresh from DB to see latest metrics
        return ApiResponse(success=True, data=_job_to_schema(job))


@router.get("/", summary="Listowanie wszystkich zadań backtestów", response_model=ApiResponse[list[BacktestJobResponse]])
def list_jobs() -> ApiResponse[list[BacktestJobResponse]]:
    """Zwraca listę wszystkich zadań backtestowania posortowanych od najnowszych."""
    with get_session() as db:
        jobs = db.query(BacktestJob).order_by(BacktestJob.created_at.desc()).all()
        data = [_job_to_schema(j) for j in jobs]
        return ApiResponse(success=True, data=data)
