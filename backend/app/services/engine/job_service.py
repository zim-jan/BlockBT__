from __future__ import annotations

import math
from typing import Any

from loguru import logger
from sqlalchemy.orm import Session

from app.models.orm import BacktestJob, JobStatus, OptimizationJob, _utcnow


def _finite(value: Any) -> float | None:
    """float(value) jeśli skończone, inaczej None (guard NaN/inf/str)."""
    try:
        fval = float(value)
    except (TypeError, ValueError):
        return None
    return fval if math.isfinite(fval) else None


def _aggregate_multi_symbol(metrics: dict[str, Any]) -> dict[str, float | None]:
    """Agregat equal-weight metryk per-symbol → kolumny skalarne jobu.

    Audyt 2026-07-17: dla wyniku multi-symbol ``metrics`` to zagnieżdżona mapa
    per ticker — ``metrics.get("Total Return [%]")`` zwracało None i kolumny
    skalarne (widoczne na listach jobów) zapisywały się jako NULL. Każdy symbol
    jest symulowany niezależnie z pełnym init_cash, więc uczciwy agregat to:
    średnia metryk wskaźnikowych (po wartościach skończonych), suma liczników
    transakcji i suma kapitału końcowego.
    """
    symbols = metrics.get("symbols")
    if not isinstance(symbols, list):
        symbols = [k for k, v in metrics.items() if isinstance(v, dict) and k != "raw"]
    per_symbol = [metrics[s] for s in symbols if isinstance(metrics.get(s), dict)]

    def mean_of(key: str) -> float | None:
        vals = [f for m in per_symbol if (f := _finite(m.get(key))) is not None]
        return sum(vals) / len(vals) if vals else None

    def sum_of(key: str) -> float | None:
        vals = [f for m in per_symbol if (f := _finite(m.get(key))) is not None]
        return sum(vals) if vals else None

    return {
        "Total Return [%]": mean_of("Total Return [%]"),
        "Sharpe Ratio": mean_of("Sharpe Ratio"),
        "Max Drawdown [%]": mean_of("Max Drawdown [%]"),
        "Total Trades": sum_of("Total Trades"),
        "Final Value": sum_of("Final Value"),
    }


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

        # FAILED to też stan terminalny (audyt 2026-07-17) — spójnie z jobami optymalizacji
        if status in (JobStatus.COMPLETED, JobStatus.FAILED):
            job.completed_at = _utcnow()

        if metrics:
            job.metrics = metrics
            # Multi-symbol: kolumny skalarne z agregatu equal-weight (audyt 2026-07-17)
            scalars = (
                _aggregate_multi_symbol(metrics)
                if metrics.get("is_multi_symbol")
                else metrics
            )
            job.total_return_pct = scalars.get("Total Return [%]")
            job.sharpe_ratio = scalars.get("Sharpe Ratio")
            job.max_drawdown_pct = scalars.get("Max Drawdown [%]")
            job.num_trades = scalars.get("Total Trades")
            job.final_capital = scalars.get("Final Value")

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
            # WFO (Faza 15): metryki zbiorcze OOS i liczniki okien muszą przetrwać
            # zapis do DB — bez nich UI nie ma czego wyświetlić (review 2026-07-16).
            # Wyniki Optuny tych kluczy nie mają, więc dla nich nic się nie zmienia.
            trials_data: dict[str, Any] = {"trials": results.get("trials")}
            for key in ("overall_metrics", "n_windows", "n_failed_windows", "method", "mode"):
                if key in results:
                    trials_data[key] = results[key]
            job.trials_data = trials_data
            job.completed_at = _utcnow()
        elif status == JobStatus.FAILED:
            job.completed_at = _utcnow()

        db.commit()
        db.refresh(job)
        return job
