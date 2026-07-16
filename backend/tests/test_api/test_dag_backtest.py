"""
Tests for the /api/backtest/dag endpoint — Phase 9 Krok 5.

Validates that DAG payloads are accepted, validated by GraphParser,
and rejected with 422 when the graph structure is invalid.
"""
from fastapi.testclient import TestClient

from app.db.session import get_session
from app.main import app
from app.models.orm import Strategy

client = TestClient(app)


def _create_strategy(db_session) -> int:
    """Helper to create a strategy and return its ID."""
    with get_session() as db:
        strat = Strategy(
            name="DAG Test Strategy",
            description="Created for DAG endpoint testing",
            parameters={"symbol": "AAPL", "sma_fast": 10},
        )
        db.add(strat)
        db.commit()
        db.refresh(strat)
        return strat.id


def _valid_dag() -> dict:
    """Minimal valid DAG: DataIngestion → Indicators → LogicOperators → Execution."""
    return {
        "nodes": [
            {
                "id": "n1",
                "type": "dataNode",
                "category": "DataIngestion",
                "params": {"symbol": "AAPL", "timeframe": "1d"},
            },
            {
                "id": "n2",
                "type": "indicatorNode",
                "category": "Indicators",
                "params": {"windows": [10, 30]},
            },
            {
                "id": "n3",
                "type": "signalNode",
                "category": "LogicOperators",
                "params": {"signalType": "sma_crossover"},
            },
            {
                "id": "n4",
                "type": "portfolioNode",
                "category": "Execution",
                "params": {"initialCapital": 10000.0},
            },
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n2"},
            {"id": "e2", "source": "n2", "target": "n3"},
            {"id": "e3", "source": "n3", "target": "n4"},
        ],
        "meta_nodes": [],
    }


def test_trigger_dag_backtest_success(db_session):
    """Valid DAG → 202 Accepted."""
    strategy_id = _create_strategy(db_session)
    payload = {"strategy_id": strategy_id, "dag": _valid_dag()}

    response = client.post("/api/backtest/dag", json=payload)

    assert response.status_code == 202
    data = response.json()
    assert data["success"] is True
    assert data["data"]["status"] == "PENDING"
    assert data["data"]["strategy_id"] == strategy_id
    assert "id" in data["data"]


def test_dag_job_status_exposes_data_node_params(db_session, monkeypatch):
    """Review Janka 2026-07-16: dla jobów DAG parameters_snapshot = {"dag": ...},
    więc GET /api/backtest/{id} zwracał puste symbol/timeframe/daty. Metadane
    muszą być czytane z węzła DataIngestion grafu."""
    import app.api.backtest as backtest_mod

    # Nie uruchamiaj realnego backtestu w tle (sieć/dane bez znaczenia dla schematu)
    monkeypatch.setattr(backtest_mod, "run_vectorbt_backtest", lambda *a, **k: None)

    strategy_id = _create_strategy(db_session)
    dag = _valid_dag()
    dag["nodes"][0]["params"] = {
        "symbol": "MSFT",
        "dataSource": "yahoo",
        "timeframe": "1h",
        "startDate": "2024-01-01",
        "endDate": "2024-06-30",
    }
    payload = {"strategy_id": strategy_id, "dag": dag}
    response = client.post("/api/backtest/dag", json=payload)
    assert response.status_code == 202
    job_id = response.json()["data"]["id"]

    data = client.get(f"/api/backtest/{job_id}").json()["data"]
    assert data["symbol"] == "MSFT"
    assert data["timeframe"] == "1h"
    assert data["start_date"] == "2024-01-01"
    assert data["end_date"] == "2024-06-30"


def test_trigger_dag_backtest_missing_execution(db_session):
    """DAG without Execution node → 422 Unprocessable."""
    strategy_id = _create_strategy(db_session)
    dag = _valid_dag()
    # Remove the Execution node and its edge
    dag["nodes"] = [n for n in dag["nodes"] if n["category"] != "Execution"]
    dag["edges"] = [e for e in dag["edges"] if e["target"] != "n4"]

    payload = {"strategy_id": strategy_id, "dag": dag}
    response = client.post("/api/backtest/dag", json=payload)

    assert response.status_code == 422


def test_trigger_dag_backtest_invalid_connection(db_session):
    """DAG with invalid edge (DataIngestion → LogicOperators) → 422."""
    strategy_id = _create_strategy(db_session)
    dag = {
        "nodes": [
            {
                "id": "n1",
                "type": "dataNode",
                "category": "DataIngestion",
                "params": {"symbol": "AAPL", "timeframe": "1d"},
            },
            {
                "id": "n3",
                "type": "signalNode",
                "category": "LogicOperators",
                "params": {"signalType": "sma_crossover"},
            },
            {
                "id": "n4",
                "type": "portfolioNode",
                "category": "Execution",
                "params": {"initialCapital": 10000.0},
            },
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n3"},  # Invalid!
            {"id": "e2", "source": "n3", "target": "n4"},
        ],
    }
    payload = {"strategy_id": strategy_id, "dag": dag}
    response = client.post("/api/backtest/dag", json=payload)

    assert response.status_code == 422
    assert "Invalid connection" in response.json()["detail"]


def test_trigger_dag_backtest_strategy_not_found(db_session):
    """DAG with nonexistent strategy_id → 404."""
    payload = {"strategy_id": 999999, "dag": _valid_dag()}
    response = client.post("/api/backtest/dag", json=payload)

    assert response.status_code == 404


def test_trigger_dag_backtest_bad_schema(db_session):
    """Completely invalid payload → 422 from Pydantic."""
    payload = {"strategy_id": 1, "dag": {"nodes": "not_a_list"}}
    response = client.post("/api/backtest/dag", json=payload)

    assert response.status_code == 422
