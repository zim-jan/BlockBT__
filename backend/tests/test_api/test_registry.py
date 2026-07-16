import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_registry_indicators():
    # Ten endpoint jeszcze nie istnieje - spodziewany 404 (RED phase)
    response = client.get("/api/v1/registry/indicators")
    assert response.status_code == 200
    data = response.json()
    
    # Sprawdzamy czy zwraca dynamiczne klasy z vectorbt (wymaga implementacji)
    assert "SMA" in data
    assert "MACD" in data
    assert "fast_window" in data["SMA"]["parameters"]
