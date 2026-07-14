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
            "raises ValueError('Unsafe code detected: ...'). No external deps (Air-Gapped)."
        ),
        "api_layer": (
            "Domain: API Layer\n"
            "Location: /backend/app/api/\n"
            "Guidelines:\n"
            "- Framework: FastAPI (async request handling).\n"
            "- Response Format: `{\"success\": bool, \"data\": dict|list, \"error\": str|null}`.\n"
            "- Schemas: Pydantic 2.x in `/backend/app/schemas/`.\n"
            "- Endpoints must bind to localhost (127.0.0.1:8000) exclusively."
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