"""
Cykl życia jobów w JobService (audyt 2026-07-17, P3).

FAILED to stan terminalny — musi dostawać ``completed_at`` tak samo jak
COMPLETED (job optymalizacji już to robił, backtest nie).
"""


from app.models.orm import BacktestJob, JobStatus, Strategy
from app.services.engine.job_service import JobService


def _mk_job(db) -> BacktestJob:
    strat = Strategy(name="Lifecycle", description="", parameters={})
    db.add(strat)
    db.flush()
    job = BacktestJob(strategy_id=strat.id, status=JobStatus.PENDING, parameters_snapshot={})
    db.add(job)
    db.flush()
    return job


def test_failed_backtest_gets_completed_at(db_session):
    job = _mk_job(db_session)

    updated = JobService.update_backtest_status(
        db_session, job.id, JobStatus.FAILED, error_message="boom"
    )

    assert updated.status == JobStatus.FAILED
    assert updated.completed_at is not None


def test_running_backtest_has_no_completed_at(db_session):
    job = _mk_job(db_session)

    updated = JobService.update_backtest_status(db_session, job.id, JobStatus.RUNNING)

    assert updated.completed_at is None
