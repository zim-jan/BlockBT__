import pytest
from fastapi.testclient import TestClient

from blockbt.api.main import app
from blockbt.db.models import StrategyTemplate, User

client = TestClient(app)

HEADERS = {
    "X-API-Key": "blockbt-secret-key-123"
}

import contextlib
from unittest.mock import patch


@pytest.fixture(autouse=True)
def override_get_session(db_session):
    @contextlib.contextmanager
    def mock_get_session():
        yield db_session
    
    with patch("blockbt.api.routes.strategies.get_session", mock_get_session), \
         patch("blockbt.api.routes.results.get_session", mock_get_session):
        yield

def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_list_strategies_unauthorized():
    response = client.get("/api/v1/strategies/")
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authenticated"

def test_list_strategies_authorized(db_session):
    # Setup dummy data in the injected session
    user = User(username="testapi", email="api@test.com", password_hash="hash")
    db_session.add(user)
    db_session.flush()
    
    st_tpl = StrategyTemplate(
        user_id=user.id,
        name="API Test Strategy",
        engine_type="opensource",
        wizard_state={"symbol": "AAPL", "initial_capital": 1000}
    )
    db_session.add(st_tpl)
    db_session.commit()
    
    response = client.get("/api/v1/strategies/", headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "count" in data
    assert data["count"] >= 1
    assert any(s["name"] == "API Test Strategy" for s in data["strategies"])

def test_trigger_backtest(db_session):
    user = User(username="testapi2", email="api2@test.com", password_hash="hash")
    db_session.add(user)
    db_session.flush()
    
    st_tpl = StrategyTemplate(
        user_id=user.id,
        name="Trigger Test",
        engine_type="opensource",
        wizard_state={"symbol": "TEST"}
    )
    db_session.add(st_tpl)
    db_session.commit()
    
    response = client.post(f"/api/v1/strategies/{st_tpl.id}/run", headers=HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Backtest triggered successfully."
    assert "simulation_id" in data
    assert data["status"] == "pending"
    
    # Verify result endpoint
    sim_id = data["simulation_id"]
    res_response = client.get(f"/api/v1/results/{sim_id}", headers=HEADERS)
    assert res_response.status_code == 200
    res_data = res_response.json()
    assert res_data["id"] == sim_id
    assert res_data["symbol"] == "TEST"
