"""
Higiena /api/results i /api/backtest (audyt 2026-07-17, P2).

- win_rate_pct czytane pod złym kluczem (silnik zapisuje "Win Rate [%]") —
  zawsze None w odpowiedzi i w payloadzie analizy AI.
- list_jobs zwracało pełne equity_curve KAŻDEGO joba (tysiące punktów per job,
  multi-MB payload listy) — lista ma być lekka, pełna krzywa tylko w GET /{id}.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.db.session import get_session
from app.main import app
from app.models.orm import BacktestJob, Strategy

client = TestClient(app)

_CURVE = [{"date": f"2023-01-{d:02d}", "value": 10000.0 + d} for d in range(1, 30)]


def _create_job() -> int:
    with get_session() as db:
        strat = Strategy(name="Hygiene Strat", description="d", parameters={})
        db.add(strat)
        db.commit()
        db.refresh(strat)

        job = BacktestJob(
            strategy_id=strat.id,
            status="COMPLETED",
            parameters_snapshot={"symbol": "TEST", "timeframe": "1d"},
            metrics={"Win Rate [%]": 55.0, "equity_curve": _CURVE},
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


def test_results_win_rate_read_from_engine_key(db_session):
    job_id = _create_job()

    resp = client.get(f"/api/results/{job_id}")

    assert resp.status_code == 200
    assert resp.json()["data"]["metrics"]["win_rate_pct"] == 55.0


def test_list_jobs_omits_equity_curve(db_session):
    job_id = _create_job()

    listing = client.get("/api/backtest/")
    assert listing.status_code == 200
    items = listing.json()["data"]
    item = next(i for i in items if i["id"] == job_id)
    assert item["equity_curve"] in (None, []), "lista jobów nie może nieść pełnych krzywych"

    # Pełna krzywa nadal dostępna w widoku szczegółowym
    detail = client.get(f"/api/backtest/{job_id}")
    assert detail.status_code == 200
    assert detail.json()["data"]["equity_curve"] == _CURVE
