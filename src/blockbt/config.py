"""
BlockBT application configuration.
Sources (in priority order): environment variables → .env file → defaults.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root is three levels up from this file: src/blockbt/config.py
_PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Central configuration object. Override any value via environment variable."""

    model_config = SettingsConfigDict(
        env_file=_PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # App
    # ------------------------------------------------------------------
    APP_NAME: str = "BlockBT"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Security
    SECRET_KEY: str = Field(
        description="A URL-safe base64-encoded 32-byte key for Fernet encryption. Generate with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
    )

    # ------------------------------------------------------------------
    # Paths
    # ------------------------------------------------------------------
    PROJECT_ROOT: Path = _PROJECT_ROOT
    DATA_DIR: Path = _PROJECT_ROOT / "data"
    PARQUET_DIR: Path = _PROJECT_ROOT / "data" / "parquet"
    LOG_DIR: Path = _PROJECT_ROOT / "data" / "logs"

    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------
    DATABASE_URL: str = Field(
        default_factory=lambda: f"sqlite:///{_PROJECT_ROOT / 'data' / 'blockbt.db'}",
        description="SQLAlchemy connection string. Defaults to local SQLite.",
    )

    # ------------------------------------------------------------------
    # Engine
    # ------------------------------------------------------------------
    # If vectorbtpro directory exists in the project root, mark as BYOL-available.
    VBTPRO_PATH: Path | None = _PROJECT_ROOT / "vectorbt.pro-main" # explicit override via env
    PREFER_PRO_ENGINE: bool = False # set True to force ProEngine even without full vbtpro

    # ------------------------------------------------------------------
    # Data Connectors
    # ------------------------------------------------------------------
    DATA_CONNECTOR: str = "yahoo"  # fallback connector key
    PARQUET_CACHE_TTL_HOURS: int = 24  # re-download after this many hours

    # Alpaca (optional BYOK)
    ALPACA_API_KEY: str | None = None
    ALPACA_SECRET_KEY: str | None = None
    ALPACA_BASE_URL: str = "https://paper-api.alpaca.markets"

    # ------------------------------------------------------------------
    # MCP / AI
    # ------------------------------------------------------------------
    MCP_EQUITY_CURVE_MAX_POINTS: int = 500
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    OLLAMA_BASE_URL: str = "http://192.168.19.31:11434"  # Ollama server
    OLLAMA_MODEL: str = "llama3"  # default model tag

    def effective_vbtpro_path(self) -> Path | None:
        """Return the resolved vectorbtpro path, checking the well-known sibling dir."""
        vbtpro = self.VBTPRO_PATH
        if vbtpro is not None and vbtpro.exists():
            return vbtpro
        candidate = self.PROJECT_ROOT / "vectorbt.pro-main"
        if candidate.exists():
            return candidate
        return None

    def ensure_dirs(self) -> None:
        """Create runtime directories if they don't exist."""
        for d in (self.DATA_DIR, self.PARQUET_DIR, self.LOG_DIR):
            d.mkdir(parents=True, exist_ok=True)


# Module-level singleton — import this everywhere.
settings = Settings()
