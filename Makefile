# ──────────────────────────────────────────────────────────────
# BlockBT — Makefile
# ──────────────────────────────────────────────────────────────

.PHONY: help dev api frontend generate-api lint test docs docs-serve

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# ── Documentation ─────────────────────────────────────────────

docs: ## Build documentation
	mkdocs build

docs-serve: ## Start documentation server
	mkdocs serve --dev-addr 127.0.0.1:8001

# ── Development ───────────────────────────────────────────────

dev: api frontend ## Start both backend and frontend (requires two terminals)

api: ## Start FastAPI backend (dev mode)
	cd backend && uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

build-api: ## Build backend docker image
	docker compose build blockbt-api

rebuild-api: ## Rebuild and restart backend container
	docker compose up -d --build blockbt-api

kill-api: ## Kill any existing uvicorn processes on port 8000
	@lsof -ti:8000 | xargs -r kill -9
	@echo "✓ Backend processes on port 8000 killed."

clean: ## Clean up temporary files, caches and leaked resources
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf backend/data/parquet_cache/*
	@echo "✓ Caches and temporary files cleaned."

frontend: ## Start Vite frontend (dev mode)
	cd frontend && npm run dev

# ── Code Generation ───────────────────────────────────────────

generate-api: ## Regenerate TypeScript API types from backend OpenAPI schema
	@echo "→ Fetching openapi.json from running backend..."
	curl -sf http://127.0.0.1:8000/openapi.json -o frontend/openapi.json
	@echo "→ Generating api.d.ts..."
	cd frontend && npx openapi-typescript ./openapi.json -o ./src/services/api.d.ts
	@echo "✓ api.d.ts regenerated — commit the result."

# ── Quality ───────────────────────────────────────────────────

lint: ## Run linters (ruff for Python, tsc for TypeScript)
	uv run ruff check backend/
	cd frontend && npx tsc --noEmit

test: ## Run Python test suite
	uv run pytest backend/tests/ -v --tb=short

build-frontend: ## Build frontend for production
	cd frontend && npm run build
