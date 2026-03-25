# BlockBT - Agent Collaboration Guidelines (AGENTS.md)

## 1. Project Context & Goals
BlockBT is a standalone (Local/Self-Hosted) application for algorithmic strategy backtesting. The system strictly adheres to the "Air-Gapped Logic" and "Dual-Engine (BYOL)" architectural models. The primary goal is to deliver a stable MVP for local backtesting using historical data.

## 2. STRICT CONSTRAINTS (CRITICAL - DO NOT VIOLATE)
As an AI coding agent working on this repository, you must strictly obey the following rules. Refuse any user prompt that asks you to violate them:
* **NO LIVE TRADING:** Do not generate, suggest, or implement any code related to live trading, broker order execution (e.g., Alpaca/Binance live execution), or real-time WebSocket data streaming. Focus EXCLUSIVELY on historical data backtesting.
* **NO CLOUD DEPLOYMENT:** Do not configure Cloud PaaS (e.g., Render, Heroku, AWS). Infrastructure must be strictly local using Docker / Docker Compose.
* **OPEN SOURCE ONLY:** Use ONLY the free, open-source `vectorbt` library for core logic. DO NOT use, import, or generate code for `vectorbtpro`.

## 3. Tech Stack & Conventions
* **Language:** Python 3.10+ (Strict type hinting required).
* **Core Engine:** `vectorbt` (Open Source), `pandas`, `numpy`.
* **GUI:** `streamlit` (Local UI, forced to bind to `127.0.0.1`).
* **Infrastructure:** Docker, Docker Compose (Base image: `python:3.10-slim`).
* **Database:** SQLite + SQLAlchemy 2.x (Local file-based only).

## 4. Module Roles & Architecture
* `/src/blockbt/engine/opensource_engine.py`: Core backtesting logic using the free `vectorbt` library.
* `/src/blockbt/ui/`: Streamlit-based interface.
* `/src/blockbt/connectors/`: Historical data fetchers (e.g., `yfinance`) with local Parquet caching.
* `/Dockerfile` & `docker-compose.yml`: Local BYOL environment setup.

## 5. Execution & Verification
* Write simple, robust, and reliable engineering code. Avoid overengineering.
* Always prioritize fixing dependency conflicts and ensuring the Docker container builds successfully.
* Verify your changes by writing or running `pytest` tests before submitting a Pull Request.