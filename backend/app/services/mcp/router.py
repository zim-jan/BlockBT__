from pathlib import Path

from mcp.server.fastmcp import FastMCP

# Initialize the MCP Server
mcp = FastMCP("BlockBT-Architectural-Router")


@mcp.tool()
def read_safe_file(file_path: str) -> str:
    """
    Reads the content of a file safely.
    Strictly blocks any access to paths containing 'vectorbtpro' to enforce BYOL/Air-Gapped policy.
    """
    try:
        path = Path(file_path).resolve()

        # Security Check: Enforce Air-Gapped policy for vectorbtpro
        if "vectorbtpro" in str(path).lower():
            return "SECURITY VIOLATION: Access to 'vectorbtpro' is strictly forbidden (Air-Gapped / BYOL policy)."

        if not path.exists():
            return f"ERROR: File not found at {path}"

        if not path.is_file():
            return f"ERROR: Path is not a file: {path}"

        return path.read_text(encoding="utf-8")

    except Exception as e:
        return f"ERROR: Failed to read file. Details: {str(e)}"


@mcp.tool()
def get_domain_context(domain: str) -> str:
    """
    Returns architectural guidelines and constraints for a specific BlockBT domain.
    Available domains: data_connector, core_engine, api_layer, frontend, mcp_integration, database.
    """
    domain_key = domain.strip().lower()

    contexts = {
        "data_connector": (
            "Domain: Data Connectors\n"
            "Location: /backend/app/services/connectors/\n"
            "Guidelines:\n"
            "- Must extend base class `base.DataConnector`.\n"
            "- Implement `async def fetch_data()`.\n"
            "- Data must be cached locally as Parquet files in `BLOCKBT_CACHE_DIR`.\n"
            "- Use registry pattern in `registry.py` for discovery.\n"
            "- Faza 10: `fetch(symbol: str | list[str])` — a list fetches each symbol (cache stays per ticker) "
            "and returns LONG format via `pd.concat(..., keys=symbols, names=['symbol']).sort_index()`. "
            "Deliberately NOT `vbt.YFData(list)` (column layout is version-dependent)."
        ),
        "core_engine": (
            "Domain: Core Engine & Data\n"
            "Location: /backend/app/services/engine/\n"
            "Guidelines:\n"
            "- STRICT RULE: Use ONLY the free, open-source `vectorbt` library.\n"
            "- STRICT RULE: DO NOT use, import, or generate code for `vectorbtpro`.\n"
            "- Key files: `opensource_engine.py` (logic), `loader.py` (data), `indicators.py`, `optimizer.py`.\n"
            "- Faza 10 (multi-symbol): `_prepare_close` pivots row MultiIndex [symbol, date] (LONG) into a WIDE "
            "DataFrame (columns=symbols); the whole pipeline broadcasts over columns with NO python loops.\n"
            "- Multi-symbol metrics come from vectorbt column Series (total_return/sharpe/max_drawdown/trades) "
            "guarded with np.isfinite -> 0.0; result carries `is_multi_symbol`, `symbols`, per-ticker `metrics` "
            "and `equity_curve`. Single-symbol output stays flat (backward compatible).\n"
            "- `IndicatorService._align_to_symbols` strips the `ma_window` column level vbt adds; combining a "
            "parameter list with multiple symbols raises ValueError (out of scope).\n"
            "- Faza 11 (custom indicators): `IndicatorService.compile_custom_indicator(code)` validates code via "
            "`_validate_code_safety` (AST allowlist deny-by-default), execs in a closed namespace, njit-compiles "
            "the 1D core (contract: 1D np.ndarray -> 1D np.ndarray, lazy compile on first `.run()`), and wraps it "
            "in `vbt.IndicatorFactory`. `generate_custom` (DAG `indicatorType=='custom'`) is hardened the same way "
            "(AST validation + closed `__builtins__`); user code defines `entries`/`exits`. Sandbox blocks "
            "imports/eval/exec/getattr/os/sys, dunder + frame attrs, and file-write attrs (to_csv/tofile/...) -> "
            "raises ValueError('Unsafe code detected: ...'). No external deps (Air-Gapped).\n"
            "- Faza 12 (risk management): `ExecutionParams` (schemas/dag.py) adds `sl_stop`/`tp_stop` (0..1), "
            "`sl_trail` (bool), `size` (>0), `size_type` (amount|value|percent). `execute_dag_portfolio` passes "
            "them to `vbt.Portfolio.from_signals` ONLY when set (no regression on DAGs without risk params); "
            "`size_type` accepted as a plain string (vbt 1.0.0). `run_dag_backtest` requires an Indicators node "
            "-> raises `GraphValidationError` if missing (SL/TP need a signal source to act on). vbt does not "
            "expose SL/TP exit counts in `stats()`/a stable enum, so `_count_stop_exits` reconstructs them by "
            "classifying closed trades: exit price vs entry*(1+/-stop) with eps=1e-3, long/short symmetric; "
            "surfaced in `result['raw']` only when the given stop is set. Multi-symbol per-ticker SL/TP counts "
            "are out of scope (Faza 10 branch executes SL/TP correctly but doesn't surface counts).\n"
            "- Faza 13 (analytics): `QSAdapterService.generate_tearsheet(pf)` (`qsadapter.py`, staticmethod) "
            "builds a self-contained air-gapped HTML tearsheet from `pf.stats()` ONLY (normalizes Series/dict, "
            "html.escape, try/except + logger.warning). Deliberately NOT `qs.reports.html` (returns None, needs a "
            "returns series + display backend). `generate_full_tearsheet` (matplotlib Agg) is an out-of-MVP "
            "extension.\n"
            "- Faza 14 (introspection): `introspection.py` `build_indicator_catalog(vbt=None)` returns a curated "
            "catalog sourced from `schemas/dag.py` (SMA/MACD/RSI -> fast_window/slow_window/signal_window/window), "
            "optionally enriched with live vbt introspection under `vbt_*` keys in try/except. `build_node_catalog` "
            "adds DAG categories + `GraphParser.COMPATIBILITY_MATRIX`. Curated (not a `get_all()` proxy) -> "
            "deterministic and BYOL-safe; `indicator_registry.py` stays untouched."
        ),
        "api_layer": (
            "Domain: API Layer\n"
            "Location: /backend/app/api/\n"
            "Guidelines:\n"
            "- Framework: FastAPI (async request handling).\n"
            "- Response Format: `{\"success\": bool, \"data\": dict|list, \"error\": str|null}`.\n"
            "- Schemas: Pydantic 2.x in `/backend/app/schemas/`.\n"
            "- Endpoints must bind to localhost (127.0.0.1:8000) exclusively.\n"
            "- Faza 13 (analytics): `GET /api/results/{job_id}/tearsheet` -> `ApiResponse[TearsheetResponse]` "
            "(`api/results.py`); 404 (no job), 400 (status != COMPLETED), 200 (OK). Reuses `results.router` "
            "(main.py untouched); builds a `stats()` adapter from stored `BacktestJob` metrics (numpy scalars -> "
            "float, None skipped), not a live vbt Portfolio.\n"
            "- Faza 14 (introspection): `GET /api/v1/registry/*` (`api/registry.py`, first `/api/v1/` prefix). "
            "`/indicators` returns a RAW `dict[str, IndicatorSpec]` (NOT the `ApiResponse` envelope — deliberate, "
            "per test contract, documented in ADR-0005); also `/nodes` and `/` (RegistrySnapshot). Catalog built "
            "lazily in-handler, guarded against `vbt is None` (`_get_vbt` lazy import + logger.debug)."
        ),
        "frontend": (
            "Domain: React Frontend\n"
            "Location: /frontend/src/\n"
            "Guidelines:\n"
            "- Stack: React 18+, TypeScript, Vite.\n"
            "- State: TanStack Query (server state), Zustand (client state).\n"
            "- Workflows: React Flow (node-based graph editor).\n"
            "- STRICT RULE: Frontend communicates with backend ONLY via REST API. NO direct file system access."
        ),
        "mcp_integration": (
            "Domain: AI & MCP Integration\n"
            "Location: /backend/app/services/mcp/\n"
            "Guidelines:\n"
            "- `llm_client.py`: Async LLM client (OllamaClient stub).\n"
            "- `protocol.py`: MCP protocol implementation.\n"
            "- `report_builder.py`: Generates AI-powered backtest analysis reports."
        ),
        "database": (
            "Domain: Database & ORM\n"
            "Location: /backend/app/models/orm.py\n"
            "Guidelines:\n"
            "- Engine: SQLite (Local file-based only).\n"
            "- ORM: SQLAlchemy 2.x using `Mapped` and `mapped_column` syntax.\n"
            "- Path: Configured via `BLOCKBT_DB_PATH` env var."
        )
    }

    if domain_key not in contexts:
        available = ", ".join(contexts.keys())
        return f"ERROR: Unknown domain '{domain}'. Available domains: {available}"

    return contexts[domain_key]


if __name__ == "__main__":
    # Run the MCP server using standard stdio transport
    mcp.run()