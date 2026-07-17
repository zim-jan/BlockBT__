"""
JobService × multi-symbol (audyt 2026-07-17, P2).

Dla wyniku multi-symbol ``metrics`` to zagnieżdżona mapa per ticker —
``metrics.get("Total Return [%]")`` zwracało ``None`` i wszystkie kolumny
skalarne jobu (total_return_pct, sharpe_ratio, ...) zapisywały się jako
NULL bez ostrzeżenia. Oczekiwanie: agregat equal-weight (każdy symbol
symulowany niezależnie z pełnym init_cash): średnia metryk wskaźnikowych
po wartościach skończonych, suma liczników i kapitału końcowego.
"""

from __future__ import annotations

import pytest

from app.models.orm import BacktestJob, JobStatus, Strategy
from app.services.engine.job_service import JobService


def _mk_job(db) -> BacktestJob:
    strat = Strategy(name="Multi", description="", parameters={})
    db.add(strat)
    db.flush()
    job = BacktestJob(strategy_id=strat.id, status=JobStatus.PENDING, parameters_snapshot={})
    db.add(job)
    db.flush()
    return job


def _sym(total, sharpe, dd, trades, final, win=50.0) -> dict:
    return {
        "Total Return [%]": total,
        "Sharpe Ratio": sharpe,
        "Max Drawdown [%]": dd,
        "Total Trades": trades,
        "Final Value": final,
        "Win Rate [%]": win,
    }


def test_multi_symbol_scalar_columns_aggregated(db_session):
    job = _mk_job(db_session)
    metrics = {
        "AAPL": _sym(10.0, 1.0, -5.0, 3, 11000.0),
        "MSFT": _sym(20.0, 2.0, -10.0, 5, 12000.0),
        "is_multi_symbol": True,
        "symbols": ["AAPL", "MSFT"],
    }

    updated = JobService.update_backtest_status(
        db_session, job.id, JobStatus.COMPLETED, metrics
    )

    assert updated.total_return_pct == pytest.approx(15.0)
    assert updated.sharpe_ratio == pytest.approx(1.5)
    assert updated.max_drawdown_pct == pytest.approx(-7.5)
    assert updated.num_trades == 8
    assert updated.final_capital == pytest.approx(23000.0)
    # Pełne zagnieżdżone metryki zostają nietknięte w JSON
    assert updated.metrics["AAPL"]["Total Return [%]"] == 10.0


def test_multi_symbol_aggregation_skips_none_values(db_session):
    """Metryki wskaźnikowe None (NaN u źródła) nie zaniżają średniej."""
    job = _mk_job(db_session)
    metrics = {
        "AAPL": _sym(10.0, None, -5.0, 0, 10000.0),
        "MSFT": _sym(20.0, 2.0, -10.0, 5, 12000.0),
        "is_multi_symbol": True,
        "symbols": ["AAPL", "MSFT"],
    }

    updated = JobService.update_backtest_status(
        db_session, job.id, JobStatus.COMPLETED, metrics
    )

    assert updated.total_return_pct == pytest.approx(15.0)
    assert updated.sharpe_ratio == pytest.approx(2.0)  # średnia tylko z finite
    assert updated.num_trades == 5


def test_single_symbol_metrics_unchanged(db_session):
    """Płaskie metryki single-symbol — zachowanie bez zmian (regresja)."""
    job = _mk_job(db_session)
    metrics = _sym(12.5, 1.2, -4.0, 7, 11250.0)

    updated = JobService.update_backtest_status(
        db_session, job.id, JobStatus.COMPLETED, metrics
    )

    assert updated.total_return_pct == pytest.approx(12.5)
    assert updated.sharpe_ratio == pytest.approx(1.2)
    assert updated.num_trades == 7
    assert updated.final_capital == pytest.approx(11250.0)
