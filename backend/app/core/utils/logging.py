from __future__ import annotations

"""
Structured logging configuration for BlockBT.

Uses loguru for rich, structured output with:
- Human-readable console output (colour when TTY)
- JSON log rotation to data/logs/ for persistence

Call ``setup_logging()`` once at app startup.
"""


import sys

from loguru import logger

from app.core.config import settings


def setup_logging(level: str | None = None) -> None:
    """Configure loguru sinks for the BlockBT application.

    Parameters
    ----------
    level: Override log level. Defaults to DEBUG when settings.DEBUG=True, else INFO.
    """
    settings.ensure_dirs()
    effective_level = level or ("DEBUG" if settings.DEBUG else "INFO")

    # Remove default loguru handler
    logger.remove()

    # Console — human-readable
    logger.add(
        sys.stderr,
        level=effective_level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> — "
            "<level>{message}</level>"
        ),
        colorize=True,
        backtrace=True,
        diagnose=settings.DEBUG,
    )

    # Rotating file — JSON for structured querying
    logger.add(
        str(settings.LOG_DIR / "blockbt.log"),
        level="DEBUG",
        rotation="10 MB",
        retention="30 days",
        compression="gz",
        serialize=True,          # JSON output
        enqueue=True,            # thread-safe async writes
        backtrace=False,
    )

    logger.debug("Logging initialised at level={}", effective_level)
