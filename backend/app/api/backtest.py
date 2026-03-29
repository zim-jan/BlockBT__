from __future__ import annotations

from app.schemas.backtest import BacktestRequest

"""
Backtest routes — Phase 2: real BackgroundTask + SQLite job tracking.

Flow:
  POST /api/backtest/       → creates BacktestJob (PENDING), returns job_id
  GET  /api/backtest/{id}   → polls job status + metrics from SQLite
"""


from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.db.session import get_session
from app.models.orm import BacktestJob, JobStatus, Strategy
from app.services.engine.runner import run_vectorbt_backtest

router = APIRouter()


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
        if payload.sma_fast is not None:
            params["sma_fast"] = payload.sma_fast
        if payload.sma_slow is not None:
            params["sma_slow"] = payload.sma_slow
        if payload.initial_capital is not None:
            params["initial_capital"] = payload.initial_capital

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
