"""
BlockBT FastAPI Entrypoint — Phase 2 MVP.

Air-Gapped architecture: strictly local, no authorization, local logic only.
DB tables are created at startup via the lifespan context manager.
"""

import sys
from pathlib import Path

# Prepend the vendored vectorbt path before importing local modules that might import vectorbt.
# This prevents vectorbt from being mistakenly loaded as a namespace package 
# if the process is launched from the repository root.
_vbt_path = Path(__file__).resolve().parents[3] / "vectorbt"
if _vbt_path.exists() and str(_vbt_path) not in sys.path:
    sys.path.insert(0, str(_vbt_path))

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api import backtest, results, settings, strategies, workflows
from app.db.session import get_session, init_db
from app.models.orm import SystemPrompt
from app.services.mcp.llm_client import _SYSTEM_PROMPT

# ---------------------------------------------------------------------------
# Lifespan — runs init_db() once at startup
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("BlockBT API starting — initialising database…")
    init_db()
    
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
    logger.info("BlockBT API shutting down.")


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

# CORS — strictly allow only the local frontend dev server
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
app.include_router(settings.router, prefix="/api/settings", tags=["Settings"])


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@app.get("/api/health", tags=["Health"])
def health_check() -> dict:
    """Liveness probe."""
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
