from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from sqlalchemy import select

from app.core.user_scope import get_user_id, scoped_query
from app.db.session import get_session
from app.models.orm import JobStatus, OptimizationJob, Strategy
from app.schemas.base import ApiResponse
from app.schemas.optimizer import OptimizationJobResponse, OptimizationRequest, WalkForwardRequest
from app.services.engine.optimizer import WfoConfig
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
    request: Request,
) -> ApiResponse[dict[str, int]]:
    """Create an OptimizationJob and enqueue the Optuna study in the background."""
    user_id = get_user_id(request)
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
            user_id=user_id,
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
    request: Request,
) -> ApiResponse[dict[str, int]]:
    """Create an OptimizationJob and enqueue the Walk-Forward Optimization in the background."""
    user_id = get_user_id(request)
    with get_session() as db:
        strategy = db.get(Strategy, payload.strategy_id)
        if not strategy:
            raise HTTPException(
                status_code=404,
                detail=f"Strategy id={payload.strategy_id} not found",
            )

        params: dict[str, Any] = dict(strategy.parameters)
        if payload.parameters:
            params.update(payload.parameters)
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

        config = WfoConfig(
            window_size=payload.window_size,
            step_size=payload.step_size,
            mode=payload.mode,
            param_bounds=(
                {k: v.model_dump() for k, v in payload.param_bounds.items()}
                if payload.param_bounds
                else None
            ),
            n_trials=payload.n_trials,
            metric=payload.metric,
        )

        job = OptimizationJob(
            strategy_id=strategy.id,
            status=JobStatus.PENDING,
            parameters_snapshot=params,
            bounds_definition=asdict(config),
            user_id=user_id,
        )
        db.add(job)
        db.flush()
        job_id = job.id

    # Schedule background task
    background_tasks.add_task(run_walk_forward, job_id, params, config)

    return ApiResponse(success=True, data={"job_id": job_id})


@router.get("/{job_id}", summary="Get optimization status", response_model=ApiResponse[OptimizationJobResponse])
def get_optimization_status(job_id: int, request: Request) -> ApiResponse[OptimizationJobResponse]:
    """Return the current status and results of an optimization job."""
    with get_session() as db:
        job = db.get(OptimizationJob, job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job id={job_id} not found")
        
        user_id = get_user_id(request)
        if user_id is not None and job.user_id is not None and job.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
            
        return ApiResponse(success=True, data=_opt_job_to_schema(job))


@router.get("/", summary="List optimization jobs", response_model=ApiResponse[list[OptimizationJobResponse]])
def list_optimization_jobs(request: Request) -> ApiResponse[list[OptimizationJobResponse]]:
    """Return all optimization jobs ordered by creation date."""
    with get_session() as db:
        stmt = scoped_query(select(OptimizationJob).order_by(OptimizationJob.created_at.desc()), OptimizationJob, request)
        jobs = db.scalars(stmt).all()
        data = [_opt_job_to_schema(j) for j in jobs]
        return ApiResponse(success=True, data=data)
