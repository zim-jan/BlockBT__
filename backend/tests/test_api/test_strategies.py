from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_create_strategy_success(db_session):
    payload = {
        "name": "Test Strategy",
        "description": "Desc",
        "parameters": {"symbol": "BTC", "sma_fast": 10},
        "code_content": ""
    }

    response = client.post("/api/strategies/", json=payload)

    assert response.status_code == 201

    data = response.json()
    assert data["success"] is True
    assert data["data"]["name"] == "Test Strategy"
    assert data["data"]["description"] == "Desc"
    assert data["data"]["parameters"] == {"symbol": "BTC", "sma_fast": 10}
    assert "id" in data["data"]

    strategy_id = data["data"]["id"]

    # Test GET strategy to ensure it was saved correctly
    get_response = client.get(f"/api/strategies/{strategy_id}")
    assert get_response.status_code == 200
    get_data = get_response.json()

    assert get_data["success"] is True
    assert get_data["data"]["id"] == strategy_id
    assert get_data["data"]["name"] == "Test Strategy"
    assert get_data["data"]["parameters"] == {"symbol": "BTC", "sma_fast": 10}

def test_get_all_strategies(db_session):
    response = client.get("/api/strategies/")
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)
