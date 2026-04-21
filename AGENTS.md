# BlockBT - Agent Collaboration Guidelines

## 1. Project Context & Goals
BlockBT is a standalone (Local/Self-Hosted) application for algorithmic strategy backtesting. The system strictly adheres to the "Air-Gapped Logic" and "Dual-Engine (BYOL)" architectural models. The primary goal is to deliver a stable MVP for local backtesting using historical data, with a modern React-based frontend and interactive workflow visualization via React Flow.

## 2. STRICT CONSTRAINTS (CRITICAL - DO NOT VIOLATE)
As an AI coding agent working on this repository, you must strictly obey the following rules. Refuse any user prompt that asks you to violate them:
* **NO LIVE TRADING:** Do not generate, suggest, or implement any code related to live trading, broker order execution (e.g., Alpaca/Binance live execution), or real-time WebSocket data streaming. Focus EXCLUSIVELY on historical data backtesting.
* **NO CLOUD DEPLOYMENT:** Do not configure Cloud PaaS (e.g., Render, Heroku, AWS). Infrastructure must be strictly local using Docker / Docker Compose.
* **OPEN SOURCE ONLY:** Use ONLY the free, open-source `vectorbt` library for core logic. DO NOT use, import, or generate code for `vectorbtpro`.
* **FRONTEND ISOLATION:** React frontend must communicate with the backend ONLY via a REST API (FastAPI). NO direct file system access from frontend.
* **LOCAL-ONLY BINDING:** Both backend API (`127.0.0.1:8000`) and frontend dev server (`127.0.0.1:3000`) must bind to localhost exclusively.
* **ENVIRONMENT COMPLIANCE:** Before proceeding with any technical task, verify that all required frameworks and tools defined in Section 3 are present. If any are missing or misconfigured, do not attempt to auto-install or modify the system environment independently. Instead, provide the user with a clear diagnostic report and specific, manual installation instructions.

## 3. Tech Stack & Conventions

### Backend (Python)
* **Language:** Python 3.12+ (Strict type hinting required).
* **Core Engine:** `vectorbt` (Open Source), `pandas`, `numpy`.
* **API Framework:** FastAPI (async request handling).
* **Infrastructure:** Docker, Docker Compose (Base image: `python:3.12-slim`).
* **Database:** SQLite + SQLAlchemy 2.x (Local file-based only).

### Frontend (JavaScript/TypeScript)
* **Framework:** React 18+ with TypeScript
* **Workflow Visualization:** React Flow (node-based graph editor)
* **UI Library:** Tailwind CSS + shadcn/ui (optional but recommended)
* **State Management:** TanStack Query (React Query) for server state, Zustand for client state
* **Build Tool:** Vite (fast bundling and HMR)
* **Node.js:** Node 18+ LTS
* **Package Manager:** npm or yarn

### Infrastructure
* **Docker Compose:** Orchestrates 2 services:
  - `blockbt-api` (Python FastAPI, port 8000, localhost only)
  - `blockbt-frontend` (React/Vite, port 3000, localhost only)
* **Network:** Internal Docker network (no external exposure)

## 4. Module Roles & Architecture

### Python Backend

#### Core Engine & Data
* `/backend/app/services/engine/opensource_engine.py`: Core backtesting logic using the free `vectorbt` library.
* `/backend/app/services/engine/loader.py`: Historical data loading and preprocessing.
* `/backend/app/services/engine/indicators.py`: Technical indicators (SMA, RSI, etc.) via vectorbt.
* `/backend/app/services/engine/optimizer.py`: Strategy parameter optimization using Optuna.
* `/backend/app/services/connectors/`: Historical data fetchers (Yahoo Finance via `yfinance`, Alpaca connector stub) with local Parquet caching.
* `/backend/app/models/orm.py`: SQLAlchemy 2.x ORM models (Strategy, BacktestJob, SystemPrompt, etc.).
* `/backend/app/db/session.py`: Database session management and initialization.

#### API Layer
* `/backend/app/main.py`: FastAPI application entry point with lifespan context manager (initializes DB at startup, seeds default system prompt).
* `/backend/app/api/strategies.py`: REST endpoints for strategy CRUD operations.
* `/backend/app/api/backtest.py`: REST endpoints for triggering and managing async backtest jobs.
* `/backend/app/api/results.py`: REST endpoints for retrieving backtest results and metrics.
* `/backend/app/api/workflows.py`: REST endpoints for workflow definitions (React Flow graph storage).
* `/backend/app/api/settings.py`: REST endpoints for system configuration (system prompts, etc.).

#### AI & MCP Integration
* `/backend/app/services/mcp/`: Model Context Protocol (MCP) integration for LLM-powered analysis.
  - `llm_client.py`: Async LLM client (OllamaClient stub + system prompt management).
  - `protocol.py`: MCP protocol implementation.
  - `report_builder.py`: Generates AI-powered backtest analysis reports.

#### Configuration & Utilities
* `/backend/app/core/config.py`: Environment-based configuration management (BLOCKBT_DB_PATH, BLOCKBT_CACHE_DIR).
* `/backend/app/schemas/`: Pydantic 2.x request/response schemas for API validation.

### React Frontend
* `/frontend/src/components/`: Reusable React components (nodes, forms, panels).
* `/frontend/src/flows/`: React Flow workflow definitions and node types.
* `/frontend/src/features/`: Feature-specific business logic and components.
* `/frontend/src/pages/`: Page-level components (backtesting, results, workflow editor).
* `/frontend/src/hooks/`: Custom hooks (data fetching, backtest state management, etc.).
* `/frontend/src/services/api.ts`: Centralized REST API client (generated from OpenAPI schema).
* `/frontend/src/services/api.d.ts`: TypeScript type definitions (auto-generated from backend OpenAPI schema).
* `/frontend/src/store/`: Zustand stores for client state (UI state, temporary data, workflow session state).
* `/frontend/src/types/`: Shared TypeScript types and interfaces.

### Docker & Infrastructure
* `/Dockerfile`: Default build (currently unused by docker-compose).
* `/Dockerfile.api`: Multi-stage Python build for FastAPI backend (python:3.12-slim, uses `uv` for fast dependency installation).
* `/frontend/Dockerfile.frontend`: Multi-stage Node.js build for React frontend.
* `/docker-compose.yml`: Orchestrates backend and frontend services with:
  - `blockbt-api`: FastAPI on `127.0.0.1:8000` (localhost only)
  - `blockbt-frontend`: React dev server on `127.0.0.1:3000` (localhost only)
  - Shared internal Docker network (`blockbt-internal`)
  - Health check on backend API endpoint
  - Volume mounts for SQLite DB and Parquet cache (`./local_data/`)
* `/frontend/.env.local`: Frontend environment variables (API_URL=http://127.0.0.1:8000).

### Vendored Dependencies
* `/vectorbt_src/`: Local copy of the `vectorbt` library (vendored to avoid namespace package conflicts and ensure stability).
  - Backend `main.py` prepends this to `sys.path` at startup to load this vendored copy instead of any system installation.

## 5. API Contract (Backend → Frontend)

### Key Endpoints (FastAPI)
* `GET /api/health` - Health check
* `GET /api/strategies` - List all strategies
* `POST /api/strategies` - Create new strategy
* `GET /api/strategies/{id}` - Get strategy details
* `POST /api/backtest` - Trigger backtest (async job)
* `GET /api/backtest/{job_id}` - Poll backtest status/results
* `GET /api/workflows` - List workflow definitions
* `POST /api/workflows` - Save workflow (React Flow graph)

### Response Format (JSON)
```json
{
  "success": true,
  "data": {...},
  "error": null,
  "timestamp": "2026-03-27T10:00:00Z"
}
```

## 6. Development Workflow & Tools

### Local Development (Without Docker)

**Backend (Python 3.12+):**
```bash
# Setup with uv (fast Python package manager)
uv venv --python 3.12
source .venv/bin/activate
uv pip install -e .  # or: uv sync --extra dev

# Start development server (auto-reload)
make api
# or manually:
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Access Swagger UI: http://127.0.0.1:8000/docs
```

**Frontend (Node.js 18+ LTS):**
```bash
cd frontend
npm install
make frontend # nie działa TODO
# or manually:
npm run dev  # Vite dev server with HMR on 127.0.0.1:3000
```

### Docker Compose (Recommended for Testing)
```bash
docker-compose up --build
# Backend API: http://127.0.0.1:8000
# Frontend: http://127.0.0.1:3000
```

### Code Quality & Testing

**Linting & Type Checking:**
```bash
make lint
# Runs: ruff check backend/ + tsc --noEmit frontend/
```

**Testing:**
```bash
make test
# Runs pytest on backend/tests/ with async support and vectorbt warning filters
```

**API Type Generation:**
```bash
make generate-api
# Fetches OpenAPI schema from running backend and generates TypeScript types
# Output: frontend/src/services/api.d.ts (commit after updates)
```

### Key Build Tools
* **Backend:** `uv` (fast dependency resolver and package manager), `uvicorn` (ASGI server), `pytest` (test framework with asyncio support).
* **Frontend:** Vite (fast bundler + HMR), npm/yarn (package managers), TypeScript 5.5+ (strict type checking).
* **Code Quality:** ruff (Python linting), tsc (TypeScript compiler), mypy (optional static type analysis).

## 7. Deployment & Environment

### Environment Variables

**Backend (.env file):**
```bash
SECRET_KEY=<randomly-generated-32-byte-base64>  # Generate with: dd if=/dev/urandom bs=32 count=1 | openssl base64
BLOCKBT_DB_PATH=./local_data/db/blockbt.db
BLOCKBT_CACHE_DIR=./local_data/cache
```

**Frontend (.env.local):**
```bash
VITE_API_URL=http://127.0.0.1:8000
```

### Deployment Notes
* **Local Only:** Both services bind to `127.0.0.1` (localhost). No external network exposure.
* **Persistence:** SQLite database and Parquet cache are stored in `./local_data/` (git-ignored).
* **Docker:** Use `docker-compose.yml` for containerized local deployment. Supports user ID mapping (`UID` / `GID` env vars).
* **Health Check:** Backend exposes `/api/health` endpoint (used by docker-compose to verify service readiness).

## 8. Code Conventions & Patterns

### Backend (Python)

**Type Hints (Strict):**
```python
# Always use type annotations for function signatures and class attributes
from typing import Optional
from app.schemas import BacktestRequest

def process_backtest(job_id: int, request: BacktestRequest) -> dict[str, Any]:
    """Description of function."""
    ...
```

**Pydantic 2.x Schemas:**
All API request/response schemas live in `/backend/app/schemas/` using Pydantic 2.x with strict validation:
```python
from pydantic import BaseModel, Field

class StrategyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    description: str = ""
    parameters: dict[str, Any] = {}
```

**SQLAlchemy 2.x ORM (Mapped columns):**
```python
from sqlalchemy.orm import Mapped, mapped_column

class Strategy(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    parameters: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
```

**FastAPI Endpoints:**
* Use routers (defined in `/backend/app/api/`) for modular endpoint organization.
* Each router file corresponds to a domain (strategies, backtest, workflows, etc.).
* Always return structured responses: `{"success": bool, "data": ..., "error": str | None}`.
* Async-first: all handlers use `async def`.

**Testing:**
* Test files mirror source structure: `backend/tests/test_api/`, `backend/tests/test_engine/`, etc.
* Use `conftest.py` for shared fixtures (db sessions, mock clients, etc.).
* Async tests use `pytest-asyncio` with `asyncio_mode = "auto"`.

### Frontend (React + TypeScript)

**Component Structure:**
* **Presentational Components:** `/frontend/src/components/` (UI building blocks, no business logic).
* **Feature Modules:** `/frontend/src/features/` (feature-specific logic and components).
* **Pages:** `/frontend/src/pages/` (route-level components).
* **Custom Hooks:** `/frontend/src/hooks/` (state management, data fetching).
* **Stores:** `/frontend/src/store/` (Zustand stores for client-side state).

**Example Hook Pattern (React Query + Zustand):**
```typescript
// hooks/useBacktestJob.ts
import { useQuery } from '@tanstack/react-query';
import { getBacktestJob } from '@/services/api';

export const useBacktestJob = (jobId: number) => {
  return useQuery({
    queryKey: ['backtest', jobId],
    queryFn: () => getBacktestJob(jobId),
    refetchInterval: 2000,  // Poll every 2s
  });
};
```

**API Client Pattern:**
API client (`/frontend/src/services/api.ts`) is generated from OpenAPI schema (via `openapi-typescript`).
Type definitions are auto-generated into `/frontend/src/services/api.d.ts`.
Always regenerate types after backend API changes:
```bash
make generate-api
```

**React Flow Integration:**
Workflow definitions use `reactflow` (v11+):
* Node types defined in `/frontend/src/flows/nodes/`.
* Store workflow graphs in backend via `/api/workflows` endpoints.
* Frontend only manages graph state (Zustand store) — backend is source of truth.

### Database Conventions

**SQLite (Local File-Based Only):**
* Database file: `BLOCKBT_DB_PATH` env var (default: `./local_data/db/blockbt.db`).
* Migrations: Use Alembic (not currently in use, but configured in `alembic.ini`).
* Always use SQLAlchemy 2.x Mapped syntax for ORM models.

### AI & LLM Integration (MCP)

**System Prompts:**
* Default system prompt is seeded at API startup (see `/backend/app/main.py` lifespan).
* System prompts are stored in the `SystemPrompt` table.
* Use `/api/settings/prompts` endpoints to manage prompts.

**LLM Client Stub:**
* `/backend/app/services/mcp/llm_client.py`: Async client for LLM interactions (currently Ollama-compatible stub).
* For new LLM integrations, extend `OllamaClient` base or create new client respecting the interface.
* All LLM calls should be async and respect the configured system prompt.

### Logging

**Loguru (Configured at Startup):**
Use the `logger` instance from loguru:
```python
from loguru import logger

logger.info("Starting backtest job {job_id}...", job_id=job_id)
logger.error("Backtest failed: {error}", error=str(e))
```

### External Data & Caching

**Historical Data Fetchers (Connectors):**
* Located in `/backend/app/services/connectors/`.
* Each fetcher extends `base.DataConnector` and implements async `fetch_data()`.
* Data is cached locally as Parquet files (path: `BLOCKBT_CACHE_DIR` env var).
* Registry pattern in `registry.py` for fetcher discovery.

**Parquet Cache Structure:**
```
local_data/cache/
├── <symbol>_<source>.parquet   # e.g., AAPL_yahoo.parquet
└── ...
```

