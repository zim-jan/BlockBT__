"""Testy migracji Alembic (P1-6).

Migracja 0001 musi być bezpieczna na trzech wariantach bazy: świeżej, zbudowanej
przez `create_all()` oraz sprzed Fazy 16 (bez tabeli `users` i kolumn `user_id`).
"""

from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config

_REPO_ROOT = Path(__file__).resolve().parents[3]

_SCOPED_TABLES = ("strategies", "backtest_jobs", "optimization_jobs", "notes")


def _alembic_config() -> Config:
    config = Config(str(_REPO_ROOT / "alembic.ini"))
    # Ścieżka w alembic.ini jest względna wobec cwd — w testach wymuszamy absolutną.
    config.set_main_option("script_location", str(_REPO_ROOT / "backend" / "alembic"))
    return config


@pytest.fixture
def db_url(tmp_path, monkeypatch) -> str:
    url = f"sqlite:///{tmp_path}/migration_test.db"
    monkeypatch.delenv("BLOCKBT_DB_PATH", raising=False)
    monkeypatch.setenv("BLOCKBT_DB_URL", url)
    monkeypatch.setenv("DATABASE_URL", url)
    return url


def _columns(engine: sa.Engine, table: str) -> set[str]:
    return {c["name"] for c in sa.inspect(engine).get_columns(table)}


def test_upgrade_on_empty_database_is_idempotent(db_url):
    """Dwa przebiegi `upgrade head` na tej samej bazie nie mogą się wywalić."""
    config = _alembic_config()
    command.upgrade(config, "head")
    command.upgrade(config, "head")  # drugi przebieg = no-op na stemplu rewizji

    engine = sa.create_engine(db_url)
    tables = set(sa.inspect(engine).get_table_names())
    assert "users" in tables
    assert "alembic_version" in tables


def test_upgrade_on_legacy_database_adds_columns_and_backfills(db_url):
    """Baza sprzed Fazy 16: brak user_id → migracja dokłada kolumny i backfilluje."""
    engine = sa.create_engine(db_url)

    with engine.begin() as conn:
        # Schemat sprzed Fazy 16 — strategies bez user_id, ale users już istnieje
        # z adminem (inaczej backfill nie miałby do czego przypisać wierszy).
        conn.execute(sa.text("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(128) NOT NULL,
                password_hash VARCHAR(256) NOT NULL,
                role VARCHAR(16) NOT NULL,
                is_active BOOLEAN NOT NULL,
                created_at DATETIME NOT NULL
            )
        """))
        conn.execute(sa.text("""
            CREATE TABLE strategies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(128) NOT NULL,
                description TEXT NOT NULL,
                code_content TEXT NOT NULL,
                parameters JSON NOT NULL,
                created_at DATETIME NOT NULL
            )
        """))
        conn.execute(sa.text(
            "INSERT INTO users (username, password_hash, role, is_active, created_at) "
            "VALUES ('legacy_admin', 'x', 'admin', 1, '2026-01-01 00:00:00')"
        ))
        conn.execute(sa.text(
            "INSERT INTO strategies (name, description, code_content, parameters, created_at) "
            "VALUES ('Pre-Faza-16', '', '', '{}', '2026-01-01 00:00:00')"
        ))

    command.upgrade(_alembic_config(), "head")

    assert "user_id" in _columns(engine, "strategies")

    with engine.connect() as conn:
        admin_id = conn.execute(
            sa.text("SELECT id FROM users WHERE role = 'admin'")
        ).scalar()
        owner = conn.execute(sa.text("SELECT user_id FROM strategies")).scalar()
    assert owner == admin_id, "osierocony wiersz nie został przypisany adminowi"


@pytest.fixture
def isolated_engine(tmp_path, monkeypatch):
    """Przestaw `app.db.session` na własną bazę i posprzątaj po teście.

    `init_or_migrate_db()` czyta silnik przez `db_session.get_engine()`, więc
    samo podmienienie zmiennych środowiskowych nie wystarczy — moduł trzeba
    przeładować, a po teście przywrócić, żeby nie zatruć bazy sesyjnej.
    """
    from importlib import reload

    import app.db.session as session_module

    url = f"sqlite:///{tmp_path}/startup.db"
    monkeypatch.delenv("BLOCKBT_DB_PATH", raising=False)
    monkeypatch.setenv("BLOCKBT_DB_URL", url)
    monkeypatch.setenv("DATABASE_URL", url)
    reload(session_module)

    yield url

    monkeypatch.undo()
    reload(session_module)


def _alembic_revision(engine: sa.Engine) -> str | None:
    with engine.connect() as conn:
        if "alembic_version" not in sa.inspect(engine).get_table_names():
            return None
        return conn.execute(sa.text("SELECT version_num FROM alembic_version")).scalar()


def test_startup_on_fresh_database_creates_and_stamps(isolated_engine):
    """Świeża baza: schemat z create_all(), rewizja ostemplowana — bez odtwarzania historii."""
    from app.db.migrations import init_or_migrate_db

    init_or_migrate_db()

    engine = sa.create_engine(isolated_engine)
    tables = set(sa.inspect(engine).get_table_names())
    assert "users" in tables
    assert "strategies" in tables
    assert _alembic_revision(engine) == "0001", "brak stempla — kolejna migracja ruszy od zera"

    # Powtórny start nie może niczego zepsuć.
    init_or_migrate_db()
    assert _alembic_revision(engine) == "0001"


def test_startup_on_legacy_database_runs_migration(isolated_engine):
    """Baza sprzed Fazy 16 dostaje user_id bez ręcznego `make migrate`."""
    from app.db.migrations import init_or_migrate_db

    engine = sa.create_engine(isolated_engine)
    with engine.begin() as conn:
        conn.execute(sa.text("""
            CREATE TABLE strategies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(128) NOT NULL,
                description TEXT NOT NULL,
                code_content TEXT NOT NULL,
                parameters JSON NOT NULL,
                created_at DATETIME NOT NULL
            )
        """))
        conn.execute(sa.text(
            "INSERT INTO strategies (name, description, code_content, parameters, created_at) "
            "VALUES ('Pre-Faza-16', '', '', '{}', '2026-01-01 00:00:00')"
        ))

    init_or_migrate_db()

    assert "user_id" in _columns(engine, "strategies")
    assert _alembic_revision(engine) == "0001"


def test_upgrade_on_create_all_database_is_noop(db_url):
    """Baza z `create_all()` po Fazie 16 ma już wszystko — migracja nie psuje jej."""
    import app.models.user  # noqa: F401 — rejestruje tabelę users
    from app.models.orm import Base

    engine = sa.create_engine(db_url)
    Base.metadata.create_all(bind=engine)

    before = {t: _columns(engine, t) for t in _SCOPED_TABLES}
    command.upgrade(_alembic_config(), "head")
    after = {t: _columns(engine, t) for t in _SCOPED_TABLES}

    assert before == after
    for table in _SCOPED_TABLES:
        assert "user_id" in after[table]
