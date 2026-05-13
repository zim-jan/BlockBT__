from __future__ import annotations

import os
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.models.orm import Base

"""
Database session for Phase 2 REST API models.

Uses a separate SQLAlchemy engine/session to avoid dependency on


Database path resolves in priority order:
  1. BLOCKBT_DB_PATH env var  (set in docker-compose volumes)
  2. BLOCKBT_DB_URL   env var  (full SQLAlchemy URL)
  3. Dev fallback: <project_root>/local_data/db/blockbt.db
"""




def _resolve_db_url() -> str:
    # Priority 1: explicit file path (set by docker-compose volume mount)
    db_path = os.environ.get("BLOCKBT_DB_PATH")
    if db_path:
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{db_path}"

    # Priority 2: full SQLAlchemy URL
    db_url = os.environ.get("BLOCKBT_DB_URL")
    if db_url:
        return db_url

    # Priority 3: local dev default
    # Path(__file__) is src/blockbt/models/session.py
    # .parents[0] is models
    # .parents[1] is blockbt
    # .parents[2] is src
    # .parents[3] is project root
    fallback = Path(__file__).resolve().parents[3] / "backend" / "data" / "db" / "blockbt.db"
    fallback.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{fallback}"


_DB_URL = _resolve_db_url()

_engine = create_engine(
    _DB_URL,
    connect_args={"check_same_thread": False} if "sqlite" in _DB_URL else {},
    echo=os.environ.get("DEBUG", "false").lower() == "true",
    future=True,
)


@event.listens_for(_engine, "connect")
def _set_sqlite_pragmas(dbapi_connection, connection_record):  # type: ignore[no-untyped-def]
    if "sqlite" in _DB_URL:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


_SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False,
                             future=True, expire_on_commit=False)


def init_db() -> None:
    """Create all Phase 2 tables (idempotent — safe to call on every startup)."""
    Base.metadata.create_all(bind=_engine)


@contextmanager
def get_session() -> Generator[Session]:
    """Provide a transactional session scope."""
    session: Session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def drop_db() -> None:
    """Drop all Phase 2 tables."""
    Base.metadata.drop_all(bind=_engine)
