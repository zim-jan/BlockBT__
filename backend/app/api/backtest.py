from __future__ import annotations

from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.db.session import get_session
from app.models.orm import BacktestJob, JobStatus, Strategy
from app.schemas.backtest import BacktestRequest
from app.services.engine.runner import run_vectorbt_backtest

"""
Backtest routes — Phase 2: real BackgroundTask + SQLite job tracking.

Flow:
  POST /api/backtest/       → creates BacktestJob (PENDING), returns job_id
  GET  /api/backtest/{id}   → polls job status + metrics from SQLite
"""

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _job_to_dict(job: BacktestJob) -> dict[str, Any]:
    """Convert BacktestJob ORM model to dictionary."""
    return {
        "id": str(job.id),
        "job_id": str(job.id),
        "strategy_id": str(job.strategy_id),
        "status": job.status,
        "symbol": job.parameters_snapshot.get("symbol", ""),
        "timeframe": job.parameters_snapshot.get("timeframe", ""),
        "start_date": job.parameters_snapshot.get("start_date", ""),
        "end_date": job.parameters_snapshot.get("end_date", ""),
        "initial_capital": job.parameters_snapshot.get("initial_capital", 10000.0),
        "created_at": job.created_at,
        "metrics": job.metrics,
        "parameters": job.parameters_snapshot,
        "error_message": job.error_message,
    }

# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


@router.post("/", summary="Trigger a backtest", status_code=202)
def trigger_backtest(
    payload: BacktestRequest,
    background_tasks: BackgroundTasks,
) -> dict[str, Any]:
    """Create a BacktestJob (PENDING), enqueue engine execution, return job_id immediately."""
    with get_session() as db:
        strategy = db.get(Strategy, payload.strategy_id)
        if not strategy:
            raise HTTPException(
                status_code=404,
                detail=f"Strategy id={payload.strategy_id} not found",
            )

        # Merge strategy parameters with any per-request overrides
        params: dict[str, Any] = dict(strategy.parameters)
        if payload.symbol is not None:
            params["symbol"] = payload.symbol
        if payload.data_source is not None:
            params["data_source"] = payload.data_source
        if payload.sma_fast is not None:
            params["sma_fast"] = payload.sma_fast
        if payload.sma_slow is not None:
            params["sma_slow"] = payload.sma_slow
        if payload.initial_capital is not None:
            params["initial_capital"] = payload.initial_capital
        if payload.timeframe is not None:
            params["timeframe"] = payload.timeframe
        if payload.start_date is not None:
            params["start_date"] = payload.start_date
        if payload.end_date is not None:
            params["end_date"] = payload.end_date
        if payload.strategy_type is not None:
            params["strategy_type"] = payload.strategy_type
        if payload.macd_fast is not None:
            params["macd_fast"] = payload.macd_fast
        if payload.macd_slow is not None:
            params["macd_slow"] = payload.macd_slow
        if payload.macd_signal is not None:
            params["macd_signal"] = payload.macd_signal
        if payload.parameters is not None:
            params.update(payload.parameters)

        job = BacktestJob(
            strategy_id=strategy.id,
            status=JobStatus.PENDING,
            parameters_snapshot=params,
        )
        db.add(job)
        db.flush()
        job_id = job.id
        result = _job_to_dict(job)

    # Enqueue the engine — runs in FastAPI's background thread pool
    background_tasks.add_task(run_vectorbt_backtest, job_id, params)

    return {"success": True, "data": result, "error": None}


@router.get("/{job_id}", summary="Poll backtest job status")
def get_backtest_status(job_id: int) -> dict[str, Any]:
    """Return the current status and metrics of a backtest job."""
    with get_session() as db:
        job = db.get(BacktestJob, job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job id={job_id} not found")
        return {"success": True, "data": _job_to_dict(job), "error": None}


@router.get("/", summary="List all backtest jobs")
def list_jobs() -> dict[str, Any]:
    """Return all backtest jobs ordered by creation time, newest first."""
    with get_session() as db:
        jobs = db.query(BacktestJob).order_by(BacktestJob.created_at.desc()).all()
        return {
            "success": True,
            "data": [_job_to_dict(j) for j in jobs],
            "error": None,
        }
