from fastapi.testclient import TestClient

from app.db.session import get_session
from app.main import app
from app.models.orm import Strategy

client = TestClient(app)

def test_trigger_backtest_success(db_session):
    # First, create a strategy
    with get_session() as db:
        new_strat = Strategy(
            name="Test Strategy",
            description="Desc",
            parameters={"symbol": "BTC", "sma_fast": 10},
        )
        db.add(new_strat)
        db.commit()
        db.refresh(new_strat)
        strategy_id = new_strat.id

    # Payload from the error log
    payload = {
        "strategy_id": str(strategy_id),
        "symbol": "SYNTHETIC",
        "sma_fast": 10,
        "sma_slow": 30,
        "initial_capital": 10000
    }

    response = client.post("/api/backtest/", json=payload)

    assert response.status_code == 202

    data = response.json()
    assert data["success"] is True
    assert data["data"]["strategy_id"] == str(strategy_id)
    assert data["data"]["status"] == "PENDING"
    assert data["data"]["symbol"] == "SYNTHETIC"
    assert data["data"]["initial_capital"] == 10000.0
    assert data["data"]["parameters"]["sma_fast"] == 10
    assert data["data"]["parameters"]["sma_slow"] == 30
    assert "id" in data["data"]
