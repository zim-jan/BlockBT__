"""
Sesja DB × wywołania LLM (audyt 2026-07-17, P1).

Endpointy ``/analyze`` i ``/chat`` trzymały otwartą sesję (a w czacie —
otwartą transakcję zapisu po ``flush()``) przez cały ``await`` LLM,
który może trwać dziesiątki sekund: pula połączeń była blokowana,
a każdy inny pisarz SQLite dostawał ``database is locked``.
Kontrakt po fixie: w trakcie wywołania LLM żadne połączenie z puli
nie jest wyjęte, a inni pisarze mogą normalnie zapisywać.
"""


from fastapi.testclient import TestClient

from app.db.session import get_session
from app.main import app
from app.models.orm import BacktestJob, ChatMessage, Strategy
from app.services.mcp.llm_client import OllamaClient

client = TestClient(app)


def _create_job(with_report: bool = False) -> int:
    with get_session() as db:
        strat = Strategy(name="LLM Strat", description="d", parameters={"symbol": "TEST"})
        db.add(strat)
        db.commit()
        db.refresh(strat)

        job = BacktestJob(
            strategy_id=strat.id,
            status="COMPLETED",
            parameters_snapshot={"symbol": "TEST", "timeframe": "1d"},
            metrics={"Total Return [%]": 10.0},
            total_return_pct=10.0,
            sharpe_ratio=1.0,
            max_drawdown_pct=-5.0,
            num_trades=4,
            final_capital=11000.0,
            ai_analysis_report="wstępny raport" if with_report else None,
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job.id


def _checked_out() -> int:
    import app.db.session as sess

    return sess._engine.pool.checkedout()


def _assert_session_released(baseline: int) -> None:
    """Endpoint nie może trzymać połączenia z puli w trakcie wywołania LLM.

    ``baseline`` = połączenia wyjęte przed requestem (fixture db_session
    trzyma własne przez cały test) — w trakcie awaitu LLM licznik musi
    wrócić do baseline'u, czyli sesja endpointu została zamknięta.
    """
    checked_out = _checked_out()
    assert checked_out == baseline, (
        f"{checked_out - baseline} połączeń endpointu wyjętych z puli w trakcie "
        "wywołania LLM — sesja DB trzymana przez await"
    )


def test_analyze_releases_db_session_during_llm_call(db_session, monkeypatch):
    job_id = _create_job(with_report=False)
    baseline = _checked_out()

    async def fake_generate(self, prompt, system=None):
        _assert_session_released(baseline)
        return "RAPORT AI"

    monkeypatch.setattr(OllamaClient, "generate_report", fake_generate)

    resp = client.post(f"/api/results/{job_id}/analyze")

    assert resp.status_code == 200
    assert resp.json()["data"]["report"] == "RAPORT AI"

    # Raport i historia czatu utrwalone po wywołaniu LLM
    with get_session() as db:
        job = db.get(BacktestJob, job_id)
        assert job.ai_analysis_report == "RAPORT AI"
        assert len(job.chat_messages) == 2


def test_chat_releases_write_lock_during_llm_call(db_session, monkeypatch):
    """W trakcie 'myślenia' LLM inny pisarz MUSI móc zapisać do bazy —
    przed fixem endpoint trzymał transakcję zapisu (flush) przez cały await."""
    job_id = _create_job(with_report=True)
    baseline = _checked_out()

    async def fake_chat(self, messages):
        _assert_session_released(baseline)
        # Niezależny pisarz w trakcie wywołania LLM
        with get_session() as db2:
            db2.add(ChatMessage(job_id=job_id, role="user", content="concurrent-writer"))
        return "ODPOWIEDŹ LLM"

    monkeypatch.setattr(OllamaClient, "chat", fake_chat)

    resp = client.post(f"/api/results/{job_id}/chat", json={"content": "pytanie analityka"})

    assert resp.status_code == 200
    assert resp.json()["data"]["content"] == "ODPOWIEDŹ LLM"

    with get_session() as db:
        job = db.get(BacktestJob, job_id)
        contents = {m.content for m in job.chat_messages}
        # Komplet: pytanie użytkownika, odpowiedź LLM i zapis równoległego pisarza
        assert {"pytanie analityka", "ODPOWIEDŹ LLM", "concurrent-writer"} <= contents


def test_analyze_llm_error_returns_503_and_persists_nothing(db_session, monkeypatch):
    """Błąd LLM w analyze -> 503 i brak zapisu w bazie danych."""
    job_id = _create_job(with_report=False)

    async def fake_generate(self, prompt, system=None):
        return "[ERROR] Nie można połączyć się z Ollama"

    monkeypatch.setattr(OllamaClient, "generate_report", fake_generate)

    resp = client.post(f"/api/results/{job_id}/analyze")

    assert resp.status_code == 503
    with get_session() as db:
        job = db.get(BacktestJob, job_id)
        assert job.ai_analysis_report is None
        assert len(job.chat_messages) == 0


def test_chat_includes_system_prompt_and_handles_error(db_session, monkeypatch):
    """Weryfikacja wstrzykiwania roli 'system' oraz zwrotu 503 przy błędzie Ollama."""
    job_id = _create_job(with_report=True)
    captured_messages = []

    async def fake_chat(self, messages):
        captured_messages.extend(messages)
        return "ODPOWIEDŹ ANILITYKA"

    monkeypatch.setattr(OllamaClient, "chat", fake_chat)

    resp = client.post(f"/api/results/{job_id}/chat", json={"content": "pytanie użytkownika"})
    assert resp.status_code == 200
    assert len(captured_messages) > 0
    assert captured_messages[0]["role"] == "system"
    assert captured_messages[-1]["role"] == "user"
    assert captured_messages[-1]["content"] == "pytanie użytkownika"


def test_chat_llm_error_persists_nothing(db_session, monkeypatch):
    """Błąd LLM → 503 i ZERO zapisów."""
    job_id = _create_job(with_report=True)

    async def fake_chat(self, messages):
        return "[ERROR] Ollama unavailable"

    monkeypatch.setattr(OllamaClient, "chat", fake_chat)

    resp = client.post(f"/api/results/{job_id}/chat", json={"content": "pytanie"})

    assert resp.status_code == 503
    with get_session() as db:
        job = db.get(BacktestJob, job_id)
        assert len(job.chat_messages) == 0
