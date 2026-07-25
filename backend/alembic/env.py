"""Środowisko Alembic dla BlockBT.

URL bazy rozwiązywany jest **dokładnie tak samo** jak w ``app/db/session.py``:
  1. ``BLOCKBT_DB_PATH``  — ścieżka do pliku (docker-compose volume)
  2. ``BLOCKBT_DB_URL`` / ``DATABASE_URL`` — pełny URL SQLAlchemy
  3. fallback: ``backend/data/db/blockbt.db``

Dzięki temu ``alembic upgrade head`` trafia w tę samą bazę co uruchomione API.
"""

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# Repo root: backend/alembic/env.py → parents[2]
_REPO_ROOT = Path(__file__).resolve().parents[2]
_BACKEND = _REPO_ROOT / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

import app.models.user  # noqa: E402,F401 — rejestruje tabelę users w metadanych
from app.models.orm import Base  # noqa: E402

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _resolve_db_url() -> str:
    """Powiel logikę ``app.db.session._resolve_db_url`` (bez importu silnika)."""
    db_path = os.environ.get("BLOCKBT_DB_PATH")
    if db_path:
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{db_path}"

    db_url = os.environ.get("BLOCKBT_DB_URL") or os.environ.get("DATABASE_URL")
    if db_url:
        return db_url

    fallback = _REPO_ROOT / "backend" / "data" / "db" / "blockbt.db"
    fallback.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{fallback}"


def run_migrations_offline() -> None:
    """Tryb offline — generuje SQL bez łączenia się z bazą."""
    context.configure(
        url=_resolve_db_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Tryb online — wykonuje migracje na żywym połączeniu."""
    section = config.get_section(config.config_ini_section, {})
    section["sqlalchemy.url"] = _resolve_db_url()

    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # SQLite nie ma pełnego ALTER TABLE — batch mode przepisuje tabelę.
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
