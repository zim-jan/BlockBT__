from __future__ import annotations

from typing import Any

from loguru import logger
from sqlalchemy.orm import Session

from app.models.orm import BacktestJob, JobStatus, OptimizationJob, _utcnow


class JobService:
    """Service for managing Backtest and Optimization jobs in the database."""

    @staticmethod
    def update_backtest_status(
        db: Session, 
        job_id: int, 
        status: str, 
        metrics: dict[str, Any] | None = None,
        error_message: str | None = None
    ) -> BacktestJob | None:
        """Update the state and results of a BacktestJob."""
        job = db.get(BacktestJob, job_id)
        if not job:
            logger.warning(f"JobService: BacktestJob(id={job_id}) not found.")
            return None

        job.status = status
        if error_message:
            job.error_message = error_message
        
        if status == JobStatus.COMPLETED:
            job.completed_at = _utcnow()

        if metrics:
            job.metrics = metrics
            job.total_return_pct = metrics.get("Total Return [%]")
            job.sharpe_ratio = metrics.get("Sharpe Ratio")
            job.max_drawdown_pct = metrics.get("Max Drawdown [%]")
            job.num_trades = metrics.get("Total Trades")
            job.final_capital = metrics.get("Final Value")

        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def update_optimization_status(
        db: Session,
        job_id: int,
        status: str,
        results: dict[str, Any] | None = None,
        error_message: str | None = None
    ) -> OptimizationJob | None:
        """Update the state and results of an OptimizationJob."""
        job = db.get(OptimizationJob, job_id)
        if not job:
            logger.warning(f"JobService: OptimizationJob(id={job_id}) not found.")
            return None

        job.status = status
        if error_message:
            job.error_message = error_message

        if status == JobStatus.COMPLETED and results:
            job.best_parameters = results.get("best_params")
            job.best_value = results.get("best_value")
            job.trials_data = {"trials": results.get("trials")}
            job.completed_at = _utcnow()
        elif status == JobStatus.FAILED:
            job.completed_at = _utcnow()

        db.commit()
        db.refresh(job)
        return job
