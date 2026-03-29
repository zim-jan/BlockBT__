"""
Backtest routes — Phase 2: real BackgroundTask + SQLite job tracking.

Flow:
  POST /api/backtest/       → creates BacktestJob (PENDING), returns job_id
  GET  /api/backtest/{id}   → polls job status + metrics from SQLite
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from blockbt.engine.runner import run_vectorbt_backtest
from blockbt.models.orm import BacktestJob, JobStatus, Strategy
from blockbt.models.session import get_session

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class BacktestRequest(BaseModel):
    strategy_id: int
    # Optional overrides — if provided they take precedence over strategy.parameters
    symbol: str | None = None
    sma_fast: int | None = None
    sma_slow: int | None = None
    initial_capital: float | None = None


class BacktestJobResponse(BaseModel):
    job_id: int
    strategy_id: int
    status: str
    metrics: dict[str, Any] | None = None
    error_message: str | None = None
    created_at: str
    completed_at: str | None = None


def _job_to_dict(job: BacktestJob) -> dict[str, Any]:
    return {
        "job_id": job.id,
        "strategy_id": job.strategy_id,
        "status": job.status,
        "metrics": job.metrics,
        "total_return_pct": job.total_return_pct,
        "sharpe_ratio": job.sharpe_ratio,
        "max_drawdown_pct": job.max_drawdown_pct,
        "num_trades": job.num_trades,
        "final_capital": job.final_capital,
        "error_message": job.error_message,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
    }


# ---------------------------------------------------------------------------
# Endpoints
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
