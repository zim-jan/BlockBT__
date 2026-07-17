import json
import sys
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

# Prepend the vendored vectorbt path before importing local modules that might import vectorbt.
# This prevents vectorbt from being mistakenly loaded as a namespace package
# if the process is launched from the repository root.
_vbt_path = Path(__file__).resolve().parents[2] / "vectorbt_src"
if _vbt_path.exists() and str(_vbt_path) not in sys.path:
    sys.path.insert(0, str(_vbt_path))

from app.api import (
    backtest,
    indicators,
    optimizer,
    registry,
    results,
    settings,
    strategies,
    workflows,
)
from app.db.session import get_session, init_db
from app.models.orm import SystemPrompt
from app.services.mcp.llm_client import _SYSTEM_PROMPT

"""Główny punkt wejścia aplikacji FastAPI BlockBT — MVP Fazy 2.

Architektura typu Air-Gapped: ścisłe środowisko lokalne, brak systemu autoryzacji,
wyłącznie lokalna logika wykonawcza. Tabele bazy danych tworzone są automatycznie
podczas startu przy pomocy menedżera kontekstu (lifespan).
"""


# ---------------------------------------------------------------------------
# Lifespan — runs init_db() once at startup
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Zarządza cyklem życia aplikacji (startup/shutdown), w tym bazą danych."""
    logger.info("Start API BlockBT — inicjalizacja bazy danych…")
    init_db()
    logger.info("Baza danych gotowa.")

    # Seed default system prompt if empty
    with get_session() as db:
        if db.query(SystemPrompt).count() == 0:
            logger.info("Seeding default system prompt...")
            default_prompt = SystemPrompt(
                name="Default Quant Analyst",
                content=_SYSTEM_PROMPT,
                is_default=True
            )
            db.add(default_prompt)
            db.commit()

    logger.info("Database ready.")
    yield
    logger.info("Zamykanie API BlockBT. Czyszczenie zasobów...")

    # Clean up joblib/loky executors to avoid leaked semaphores and child processes
    try:
        from joblib.externals.loky import get_reusable_executor
        executor = get_reusable_executor()
        executor.shutdown(wait=True)
        logger.info("Loky executor shut down pomyślnie.")
    except Exception as e:  # noqa: BLE001 — cleanup best-effort przy shutdownie
        logger.debug(f"Pominięto czyszczenie loky: {e}")

    logger.info("API BlockBT zostało zamknięte.")


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="BlockBT REST API",
    description="Local-only algorithmic backtesting API (Air-Gapped, BYOL).",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS — ścisłe zezwolenie tylko na dostęp dla lokalnego serwera dev Vite/React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:3000", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware do logowania zapytań HTTP oraz ich struktury (body/query)."""
    start_time = time.time()
    
    # Przechwytywanie body requestu
    body = await request.body()
    try:
        body_json = json.loads(body) if body else None
    except json.JSONDecodeError:
        body_json = body.decode("utf-8") if body else None
    
    # Odtworzenie strumienia body, aby mogło zostać przetworzone przez endpoint
    async def receive():
        return {"type": "http.request", "body": body}
    request._receive = receive

    response = await call_next(request)
    process_time = time.time() - start_time
    
    # Pomiń logowanie dla /api/health żeby nie śmiecić logów
    if request.url.path != "/api/health":
        # Audyt 2026-07-17: cap na logowane body — pełne DAG-i/krzywe potrafią
        # mieć megabajty i zaśmiecały logi oraz pamięć
        _BODY_LOG_LIMIT = 2000
        body_repr = body_json
        if body_repr is not None:
            body_text = (
                body_repr
                if isinstance(body_repr, str)
                else json.dumps(body_repr, ensure_ascii=False)
            )
            if len(body_text) > _BODY_LOG_LIMIT:
                body_repr = f"{body_text[:_BODY_LOG_LIMIT]}… [truncated, {len(body_text)} chars]"
        log_data = {
            "method": request.method,
            "url": str(request.url),
            "client_ip": request.client.host if request.client else None,
            "status_code": response.status_code,
            "process_time_ms": round(process_time * 1000, 2),
            "query_params": dict(request.query_params),
            "body": body_repr
        }
        logger.info(f"API Request: {request.method} {request.url.path} - "
                    f"{response.status_code}\nData: "
                    f"{json.dumps(log_data, indent=2, ensure_ascii=False)}")
        
    return response

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(strategies.router, prefix="/api/strategies", tags=["Strategies"])
app.include_router(indicators.router, prefix="/api/indicators", tags=["Indicators"])
app.include_router(backtest.router, prefix="/api/backtest", tags=["Backtest"])
app.include_router(optimizer.router, prefix="/api/optimizer", tags=["Optimizer"])
app.include_router(workflows.router, prefix="/api/workflows", tags=["Workflows"])
app.include_router(results.router, prefix="/api/results", tags=["Results"])
app.include_router(settings.router, prefix="/api/settings", tags=["Settings"])
# Faza 14: Dynamic Introspection Engine — pierwszy prefiks /api/v1/ w repo.
app.include_router(registry.router, prefix="/api/v1/registry", tags=["Registry"])


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@app.get("/api/health", tags=["Health"])
def health_check() -> dict:
    """Sonda sprawdzająca stan życia usługi (Liveness probe)."""
    return {"status": "ok", "version": "2.0.0"}


# ---------------------------------------------------------------------------
# Direct execution entry-point (development only)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
