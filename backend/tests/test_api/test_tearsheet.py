"""Faza 13: testy endpointu GET /api/results/{job_id}/tearsheet."""

from fastapi.testclient import TestClient

from app.db.session import get_session
from app.main import app
from app.models.orm import BacktestJob, Strategy

client = TestClient(app)


def _create_job(status: str) -> int:
    """Tworzy strategię i job o zadanym statusie; zwraca job_id."""
    with get_session() as db:
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


def test_tearsheet_completed_job(db_session):
    job_id = _create_job("COMPLETED")

    response = client.get(f"/api/results/{job_id}/tearsheet")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["job_id"] == job_id
    assert data["data"]["format"] == "html"
    assert "<html>" in data["data"]["html"]
    assert "Sharpe Ratio" in data["data"]["html"]


def test_tearsheet_missing_job(db_session):
    response = client.get("/api/results/999999/tearsheet")
    assert response.status_code == 404


def test_tearsheet_not_completed(db_session):
    job_id = _create_job("RUNNING")

    response = client.get(f"/api/results/{job_id}/tearsheet")
    assert response.status_code == 400
