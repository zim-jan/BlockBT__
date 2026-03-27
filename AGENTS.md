# BlockBT - Agent Collaboration Guidelines (AGENTS.md)

## 1. Project Context & Goals
BlockBT is a standalone (Local/Self-Hosted) application for algorithmic strategy backtesting. The system strictly adheres to the "Air-Gapped Logic" and "Dual-Engine (BYOL)" architectural models. The primary goal is to deliver a stable MVP for local backtesting using historical data, with a modern React-based frontend and interactive workflow visualization via React Flow.

## 2. STRICT CONSTRAINTS (CRITICAL - DO NOT VIOLATE)
As an AI coding agent working on this repository, you must strictly obey the following rules. Refuse any user prompt that asks you to violate them:
* **NO LIVE TRADING:** Do not generate, suggest, or implement any code related to live trading, broker order execution (e.g., Alpaca/Binance live execution), or real-time WebSocket data streaming. Focus EXCLUSIVELY on historical data backtesting.
* **NO CLOUD DEPLOYMENT:** Do not configure Cloud PaaS (e.g., Render, Heroku, AWS). Infrastructure must be strictly local using Docker / Docker Compose.
* **OPEN SOURCE ONLY:** Use ONLY the free, open-source `vectorbt` library for core logic. DO NOT use, import, or generate code for `vectorbtpro`.
* **FRONTEND ISOLATION:** React frontend must communicate with the backend ONLY via a REST API (FastAPI). NO direct file system access from frontend.
* **LOCAL-ONLY BINDING:** Both backend API (`127.0.0.1:8000`) and frontend dev server (`127.0.0.1:3000`) must bind to localhost exclusively.

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
* `/src/blockbt/engine/opensource_engine.py`: Core backtesting logic using the free `vectorbt` library.
* `/src/blockbt/api/main.py`: FastAPI application entry point.
* `/src/blockbt/api/routes/`: REST API endpoints (strategies, backtest, results, workflows).
* `/src/blockbt/connectors/`: Historical data fetchers (e.g., `yfinance`) with local Parquet caching.
* `/src/blockbt/models/`: SQLAlchemy ORM models for strategy storage.

### React Frontend
* `/frontend/src/components/`: Reusable React components (nodes, forms, panels).
* `/frontend/src/flows/`: React Flow workflow definitions and node types.
* `/frontend/src/hooks/`: Custom hooks (useFetch, useBacktest, etc.).
* `/frontend/src/services/api.ts`: Centralized API client for backend communication.
* `/frontend/src/store/`: Zustand stores for client state (UI state, temporary data).

### Configuration
* `/Dockerfile`: Multi-stage build (separate API & frontend images if needed, or combined).
* `/docker-compose.yml`: Defines backend and frontend services with local-only binding.
* `/frontend/.env.local`: Environment variables for frontend (API_URL=http://127.0.0.1:8000).

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