"""
Database session management.

Usage:
    from blockbt.db.session import get_session, init_db

    # One-time setup at app startup:
    init_db()

    # In a request / job handler:
    with get_session() as session:
        user = session.get(User, 1)
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from blockbt.config import settings
from blockbt.db.base import Base

# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

_engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    echo=settings.DEBUG,
    future=True,
)

# Enable WAL journal mode for SQLite — dramatically improves concurrent reads.
@event.listens_for(_engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):  # type: ignore[no-untyped-def]
    if "sqlite" in settings.DATABASE_URL:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------

_SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations.

    Automatically commits on success, rolls back on any exception.

    Example::

        with get_session() as session:
            session.add(User(username="alice", ...))
    """
    session: Session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Schema management
# ---------------------------------------------------------------------------


def init_db() -> None:
    """Create all tables defined in ORM models (idempotent).

    Call once at application startup.  Alembic handles incremental migrations
    in production; this function is for dev / first-run convenience.
    """
    # Import models so SQLAlchemy metadata is populated before create_all.
    import blockbt.db.models  # noqa: F401  # side-effect import

    settings.ensure_dirs()
    Base.metadata.create_all(bind=_engine)


def drop_db() -> None:
    """Drop all tables (destructive — test environments only)."""
    import blockbt.db.models  # noqa: F401

    Base.metadata.drop_all(bind=_engine)
