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


def test_get_registry_nodes():
    """GET /api/v1/registry/nodes zwraca niepusty katalog kategorii węzłów DAG."""
    response = client.get("/api/v1/registry/nodes")
    assert response.status_code == 200
    data = response.json()

    assert len(data) > 0
    assert "DataIngestion" in data
    assert "Indicators" in data
    assert "Execution" in data


def test_get_registry_snapshot():
    """GET /api/v1/registry/ zwraca pełny zrzut: wskaźniki + kategorie + macierz kompatybilności."""
    response = client.get("/api/v1/registry/", follow_redirects=True)
    assert response.status_code == 200
    data = response.json()

    assert "indicators" in data
    assert "node_categories" in data
    assert "compatibility_matrix" in data

    assert "SMA" in data["indicators"]
    assert len(data["node_categories"]) > 0
    assert len(data["compatibility_matrix"]) > 0
