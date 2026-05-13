from __future__ import annotations

from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.db.session import get_session
from app.models.orm import JobStatus, OptimizationJob, Strategy
from app.schemas.base import ApiResponse
from app.schemas.optimizer import OptimizationJobResponse, OptimizationRequest, WalkForwardRequest
from app.services.engine.runner import run_optuna_optimization, run_walk_forward

"""
Optimization routes — Phase 4.

Handles Bayesian optimization requests via Optuna.
"""

router = APIRouter()


def _opt_job_to_schema(job: OptimizationJob) -> OptimizationJobResponse:
    """Helper to convert ORM OptimizationJob to OptimizationJobResponse."""
    return OptimizationJobResponse(
        id=job.id,
        job_id=job.id,
        strategy_id=job.strategy_id,
        status=job.status,
        symbol=job.parameters_snapshot.get("symbol", ""),
        initial_capital=job.parameters_snapshot.get("initial_capital", 10000.0),
        created_at=job.created_at,
        best_parameters=job.best_parameters,
        best_value=job.best_value,
        trials_data=job.trials_data,
        error_message=job.error_message,
        completed_at=job.completed_at,
    )


@router.post("/", summary="Trigger optimization", status_code=202, response_model=ApiResponse[dict[str, int]])
def trigger_optimization(
    payload: OptimizationRequest,
    background_tasks: BackgroundTasks,
) -> ApiResponse[dict[str, int]]:
    """Create an OptimizationJob and enqueue the Optuna study in the background."""
    with get_session() as db:
        strategy = db.get(Strategy, payload.strategy_id)
        if not strategy:
            raise HTTPException(
                status_code=404,
                detail=f"Strategy id={payload.strategy_id} not found",
            )

        # Build parameters snapshot
        params: dict[str, Any] = dict(strategy.parameters)
        params.update(
            {
                "symbol": payload.symbol,
                "data_source": payload.data_source,
                "timeframe": payload.timeframe,
                "initial_capital": payload.initial_capital,
            }
        )
        if payload.start_date:
            params["start_date"] = payload.start_date
        if payload.end_date:
            params["end_date"] = payload.end_date
        if payload.parameters:
            params.update(payload.parameters)

        # Convert Pydantic bounds to dicts for storage
        bounds_dict = {k: v.model_dump() for k, v in payload.param_bounds.items()}

        job = OptimizationJob(
            strategy_id=strategy.id,
            status=JobStatus.PENDING,
            parameters_snapshot=params,
            bounds_definition=bounds_dict,
        )
        db.add(job)
        db.flush()
        job_id = job.id

    # Schedule background task
    background_tasks.add_task(
        run_optuna_optimization,
        job_id,
        params,
        bounds_dict,
        payload.n_trials,
        payload.metric,
    )

    return ApiResponse(success=True, data={"job_id": job_id})


@router.post("/wfo", summary="Trigger walk-forward optimization", status_code=202, response_model=ApiResponse[dict[str, int]])
def trigger_wfo(
    payload: WalkForwardRequest,
    background_tasks: BackgroundTasks,
) -> ApiResponse[dict[str, int]]:
    """Create an OptimizationJob and enqueue the Walk-Forward Optimization in the background."""
    with get_session() as db:
        strategy = db.get(Strategy, payload.strategy_id)
        if not strategy:
            raise HTTPException(
                status_code=404,
                detail=f"Strategy id={payload.strategy_id} not found",
            )

        # Build parameters snapshot
        params: dict[str, Any] = dict(strategy.parameters)
        params.update(
            {
                "symbol": payload.symbol,
                "data_source": payload.data_source,
                "timeframe": payload.timeframe,
                "initial_capital": payload.initial_capital,
                "window_size": payload.window_size,
                "step_size": payload.step_size,
            }
        )
        if payload.start_date:
            params["start_date"] = payload.start_date
        if payload.end_date:
            params["end_date"] = payload.end_date
        if payload.parameters:
            params.update(payload.parameters)

        job = OptimizationJob(
            strategy_id=strategy.id,
            status=JobStatus.PENDING,
            parameters_snapshot=params,
            bounds_definition={"window_size": payload.window_size, "step_size": payload.step_size},
        )
        db.add(job)
        db.flush()
        job_id = job.id

    # Schedule background task
    background_tasks.add_task(
        run_walk_forward,
        job_id,
        params,
        payload.window_size,
        payload.step_size,
    )

    return ApiResponse(success=True, data={"job_id": job_id})


@router.get("/{job_id}", summary="Get optimization status", response_model=ApiResponse[OptimizationJobResponse])
def get_optimization_status(job_id: int) -> ApiResponse[OptimizationJobResponse]:
    """Return the current status and results of an optimization job."""
    with get_session() as db:
        job = db.get(OptimizationJob, job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job id={job_id} not found")
        return ApiResponse(success=True, data=_opt_job_to_schema(job))


@router.get("/", summary="List optimization jobs", response_model=ApiResponse[list[OptimizationJobResponse]])
def list_optimization_jobs() -> ApiResponse[list[OptimizationJobResponse]]:
    """Return all optimization jobs ordered by creation date."""
    with get_session() as db:
        jobs = (
            db.query(OptimizationJob)
            .order_by(OptimizationJob.created_at.desc())
            .all()
        )
        data = [_opt_job_to_schema(j) for j in jobs]
        return ApiResponse(success=True, data=data)
