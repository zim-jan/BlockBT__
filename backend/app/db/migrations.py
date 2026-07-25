"""Uruchamianie migracji Alembic przy starcie aplikacji.

Problem, który to rozwiązuje: `Base.metadata.create_all()` tworzy brakujące
tabele, ale **nie robi `ALTER TABLE`**. Instalacja z bazą sprzed Fazy 16
dostawała `no such column: strategies.user_id` i wymagała ręcznego
`make migrate`, o którym nikt nie wiedział.

Wzorzec „stamp albo upgrade":

* **baza pusta** → `create_all()` + `alembic stamp head`. Schemat jest z modeli,
  a stempel mówi Alembicowi, że historia jest już zastosowana. Bez stempla
  kolejna migracja (0002) próbowałaby odtworzyć całą historię na bazie, która
  ma już wszystko — i każda przyszła migracja musiałaby być idempotentna.
* **baza istniejąca** → `alembic upgrade head`, a potem `create_all()` dla tabel
  dodanych w modelach, których nie objęła jeszcze żadna migracja.

Błąd migracji celowo przerywa start aplikacji: lepiej nie wstać niż działać na
rozjechanym schemacie. Wyjątkiem jest brak samego `alembic.ini` (uruchomienie
spoza repozytorium) — wtedy schodzimy do samego `create_all()`.
"""

from pathlib import Path

import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from loguru import logger

import app.db.session as db_session

# backend/app/db/migrations.py → parents[3] to katalog główny repozytorium
_REPO_ROOT = Path(__file__).resolve().parents[3]
_ALEMBIC_INI = _REPO_ROOT / "alembic.ini"
_ALEMBIC_DIR = _REPO_ROOT / "backend" / "alembic"


def _alembic_config() -> Config:
    config = Config(str(_ALEMBIC_INI))
    # `script_location` w alembic.ini jest względne wobec cwd — przy starcie
    # przez uvicorn cwd bywa katalogiem `backend/`, więc wymuszamy absolutną.
    config.set_main_option("script_location", str(_ALEMBIC_DIR))
    return config


def _is_fresh_database(engine: sa.Engine) -> bool:
    """True, gdy w bazie nie ma jeszcze żadnej tabeli domenowej."""
    tables = set(sa.inspect(engine).get_table_names())
    return not (tables - {"alembic_version"})


def init_or_migrate_db() -> None:
    """Doprowadź schemat bazy do stanu zgodnego z modelami i migracjami."""
    if not _ALEMBIC_INI.exists() or not _ALEMBIC_DIR.exists():
        logger.warning(
            f"Nie znaleziono konfiguracji Alembica ({_ALEMBIC_INI}) — "
            "schemat zostanie utworzony wyłącznie przez create_all(), bez migracji."
        )
        db_session.init_db()
        return

    engine = db_session.get_engine()

    if _is_fresh_database(engine):
        db_session.init_db()
        command.stamp(_alembic_config(), "head")
        logger.info("Świeża baza — schemat z create_all(), rewizja ostemplowana na head.")
        return

    command.upgrade(_alembic_config(), "head")
    db_session.init_db()
    logger.info("Istniejąca baza — zastosowano migracje (alembic upgrade head).")
