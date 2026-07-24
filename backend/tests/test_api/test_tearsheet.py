"""Faza 13: testy endpointu GET /api/results/{job_id}/tearsheet."""

import pytest
from fastapi.testclient import TestClient

from app.db.session import get_session
from app.main import app
from app.models.orm import AppSetting, BacktestJob, Strategy


@pytest.fixture
def client(db_session):
    return TestClient(app)



def _create_job(status: str) -> int:
    """Tworzy strategię i job o zadanym statusie; zwraca job_id."""
    with get_session() as db:
        setting = db.get(AppSetting, "auth_enabled")
        if setting:
            setting.value = "false"
        strat = Strategy(name="Tearsheet Strat", description="d", parameters={"symbol": "TEST"})
        db.add(strat)
        db.commit()
        db.refresh(strat)

        job = BacktestJob(
            strategy_id=strat.id,
            status=status,
            parameters_snapshot={"symbol": "TEST", "timeframe": "1d"},
            metrics={"win_rate_pct": 55.0},
            total_return_pct=12.5,
            sharpe_ratio=1.5,
            max_drawdown_pct=-8.0,
            num_trades=10,
            final_capital=11250.0,
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job.id


def test_tearsheet_completed_job(client):
    job_id = _create_job("COMPLETED")

    response = client.get(f"/api/results/{job_id}/tearsheet")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["job_id"] == job_id
    assert data["data"]["format"] == "html"
    assert "<html>" in data["data"]["html"]
    assert "Sharpe Ratio" in data["data"]["html"]


def test_tearsheet_missing_job(client):
    response = client.get("/api/results/999999/tearsheet")
    assert response.status_code == 404


def test_tearsheet_not_completed(client):
    job_id = _create_job("RUNNING")

    response = client.get(f"/api/results/{job_id}/tearsheet")
    assert response.status_code == 400


def _create_job_without_metrics() -> int:
    """Job COMPLETED z ``metrics=None`` i wszystkimi kolumnami skalarnymi None."""
    with get_session() as db:
        setting = db.get(AppSetting, "auth_enabled")
        if setting:
            setting.value = "false"
        strat = Strategy(name="Empty Metrics Strat", description="d", parameters={"symbol": "TEST"})
        db.add(strat)
        db.commit()
        db.refresh(strat)

        job = BacktestJob(
            strategy_id=strat.id,
            status="COMPLETED",
            parameters_snapshot={"symbol": "TEST", "timeframe": "1d"},
            metrics=None,
            total_return_pct=None,
            sharpe_ratio=None,
            max_drawdown_pct=None,
            num_trades=None,
            final_capital=None,
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job.id


def test_tearsheet_completed_job_without_metrics(client):
    """Job COMPLETED bez metryk (metrics=None, wszystkie kolumny None) → 200 + HTML z pustą gałęzią."""
    job_id = _create_job_without_metrics()

    response = client.get(f"/api/results/{job_id}/tearsheet")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["job_id"] == job_id
    assert data["data"]["format"] == "html"
    assert "<html>" in data["data"]["html"]
    assert "No metrics available" in data["data"]["html"]
