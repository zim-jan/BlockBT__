"""
Testy endpointu /api/settings/ollama/status oraz dynamicznego rozwiązywania ustawień OllamaClient.
"""

from fastapi.testclient import TestClient

from app.db.session import get_session
from app.main import app
from app.models.orm import AppSetting
from app.services.mcp.llm_client import OllamaClient

client = TestClient(app)


def test_ollama_status_endpoint_online(monkeypatch):
    """Test endpointu statusu, gdy Ollama jest dostępna."""
    async def fake_get_status(self):
        return {
            "available": True,
            "base_url": "http://localhost:11434",
            "model": "llama3",
            "installed_models": ["llama3:latest", "nomic-embed-text:latest"],
            "model_installed": True,
            "error": None,
        }

    monkeypatch.setattr(OllamaClient, "get_status", fake_get_status)

    resp = client.get("/api/settings/ollama/status")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["available"] is True
    assert data["model"] == "llama3"
    assert data["model_installed"] is True
    assert "llama3:latest" in data["installed_models"]


def test_ollama_status_endpoint_offline(monkeypatch):
    """Test endpointu statusu, gdy Ollama jest niedostępna."""
    async def fake_get_status(self):
        return {
            "available": False,
            "base_url": "http://localhost:11434",
            "model": "llama3",
            "installed_models": [],
            "model_installed": False,
            "error": "ConnectError",
        }

    monkeypatch.setattr(OllamaClient, "get_status", fake_get_status)

    resp = client.get("/api/settings/ollama/status")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["available"] is False
    assert data["error"] == "ConnectError"


def test_ollama_client_dynamic_db_settings(db_session):
    """Weryfikacja dynamicznego pobierania URL i modelu z tabeli AppSetting."""
    with get_session() as db:
        db.add(AppSetting(key="ollama_base_url", value="http://192.168.1.100:11434"))
        db.add(AppSetting(key="ollama_model", value="mistral"))
        db.commit()

    ollama = OllamaClient()
    assert ollama.base_url == "http://192.168.1.100:11434"
    assert ollama.model == "mistral"


def test_create_system_prompt_serialization(db_session):
    """Weryfikacja rzetelnej serializacji SystemPromptResponse (w tym updated_at)."""
    resp = client.post(
        "/api/settings/prompts",
        json={"name": "Test Role", "content": "You are a test quant."},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["name"] == "Test Role"
    assert data["content"] == "You are a test quant."
    assert "created_at" in data
    assert "updated_at" in data

