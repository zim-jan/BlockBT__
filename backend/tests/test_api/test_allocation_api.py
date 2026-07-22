"""
Przepływ bloku ``allocation`` przez API (ADR-0009).

Silnik zapisuje analizę alokacji w ``job.metrics["allocation"]`` — GET /{id}
ma ją zwracać w polu ``allocation`` odpowiedzi, a lista jobów pozostaje
lekka (bez timeline'u — jak przy ``equity_curve``).
"""


from fastapi.testclient import TestClient

from app.db.session import get_session
from app.main import app
from app.models.orm import BacktestJob, Strategy

client = TestClient(app)

_ALLOCATION = {
    "timeline": {
        "dates": ["2023-01-01", "2023-01-02"],
        "weights": {"TEST": [0.0, 0.6], "cash": [1.0, 0.4]},
    },
    "summary": {
        "TEST": {
            "avg_exposure_pct": 30.0,
            "max_exposure_pct": 60.0,
            "time_in_market_pct": 50.0,
            "final_equity_share_pct": 100.0,
        }
    },
}


def _create_job(metrics: dict) -> int:
    with get_session() as db:
        strat = Strategy(name="Alloc Strat", description="d", parameters={})
        db.add(strat)
        db.commit()
        db.refresh(strat)

        job = BacktestJob(
            strategy_id=strat.id,
            status="COMPLETED",
            parameters_snapshot={"symbol": "TEST", "timeframe": "1d"},
            metrics=metrics,
            total_return_pct=10.0,
            num_trades=3,
            final_capital=11000.0,
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job.id


def test_get_job_returns_allocation(db_session):
    job_id = _create_job({"Win Rate [%]": 50.0, "allocation": _ALLOCATION})

    resp = client.get(f"/api/backtest/{job_id}")

    assert resp.status_code == 200
    assert resp.json()["data"]["allocation"] == _ALLOCATION


def test_get_multi_symbol_job_returns_allocation(db_session):
    job_id = _create_job(
        {
            "is_multi_symbol": True,
            "symbols": ["ALFA", "BETA"],
            "ALFA": {"Total Return [%]": 5.0},
            "BETA": {"Total Return [%]": -2.0},
            "allocation": _ALLOCATION,
        }
    )

    resp = client.get(f"/api/backtest/{job_id}")

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["is_multi_symbol"] is True
    assert data["allocation"] == _ALLOCATION


def test_list_jobs_omits_allocation(db_session):
    job_id = _create_job({"allocation": _ALLOCATION})

    listing = client.get("/api/backtest/")
    assert listing.status_code == 200
    item = next(i for i in listing.json()["data"] if i["id"] == job_id)
    assert item.get("allocation") is None, "lista jobów nie może nieść timeline'ów alokacji"
