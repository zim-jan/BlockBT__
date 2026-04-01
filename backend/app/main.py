"""Główny punkt wejścia aplikacji FastAPI BlockBT — MVP Fazy 2.

Architektura typu Air-Gapped: ścisłe środowisko lokalne, brak systemu autoryzacji,
wyłącznie lokalna logika wykonawcza. Tabele bazy danych tworzone są automatycznie
podczas startu przy pomocy menedżera kontekstu (lifespan).
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api import backtest, results, strategies, workflows
from app.db.session import init_db

# ---------------------------------------------------------------------------
# Lifespan — runs init_db() once at startup
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Zarządza cyklem życia aplikacji (startup/shutdown), w tym bazą danych."""
    logger.info("Start API BlockBT — inicjalizacja bazy danych…")
    init_db()
    logger.info("Baza danych gotowa.")
    yield
    logger.info("Zamykanie API BlockBT.")


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

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(strategies.router, prefix="/api/strategies", tags=["Strategies"])
app.include_router(backtest.router, prefix="/api/backtest", tags=["Backtest"])
app.include_router(workflows.router, prefix="/api/workflows", tags=["Workflows"])
app.include_router(results.router, prefix="/api/results", tags=["Results"])


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
        "blockbt.api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
