"""user scoping — tabela users, kolumny user_id, backfill do pierwszego admina

Revision ID: 0001
Revises:
Create Date: 2026-07-25

Migracja jest **idempotentna**: każdy krok sprawdza przez ``sa.inspect()``, czy
obiekt już istnieje. Musi być bezpieczna na trzech wariantach bazy:

  * świeża baza (pusta),
  * baza utworzona przez ``Base.metadata.create_all()`` po Fazie 16 (wszystko
    już jest — migracja nie robi nic poza stemplem rewizji),
  * baza sprzed Fazy 16 (brak ``users`` i kolumn ``user_id``).

Uwaga projektowa: ``user_id`` dodajemy zwykłym ``ADD COLUMN`` **bez** FK.
SQLite nie potrafi dodać ograniczenia FK do istniejącej tabeli inaczej niż
przez przepisanie jej w trybie batch, a przepisywanie ``strategies`` przy
włączonym ``PRAGMA foreign_keys`` psuje FK w tabelach potomnych (``notes``,
``backtest_jobs``). Świeże instalacje nadal dostają pełny FK z ``create_all()``.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Tabele objęte scopingiem per-użytkownik. `chat_messages`, `system_prompts`
# i `app_settings` świadomie nie mają `user_id` (są globalne / podpięte pod job).
_SCOPED_TABLES: tuple[str, ...] = (
    "strategies",
    "backtest_jobs",
    "optimization_jobs",
    "notes",
)


def _has_table(inspector: sa.Inspector, table: str) -> bool:
    return table in inspector.get_table_names()


def _has_column(inspector: sa.Inspector, table: str, column: str) -> bool:
    return column in {c["name"] for c in inspector.get_columns(table)}


def _has_index(inspector: sa.Inspector, table: str, index: str) -> bool:
    return index in {i["name"] for i in inspector.get_indexes(table)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # ------------------------------------------------------------------
    # 1. Tabela users (odpowiada app/models/user.py)
    # ------------------------------------------------------------------
    if not _has_table(inspector, "users"):
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("username", sa.String(length=128), nullable=False),
            sa.Column("password_hash", sa.String(length=256), nullable=False),
            sa.Column("role", sa.String(length=16), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )
        op.create_index("ix_users_username", "users", ["username"], unique=True)
        inspector = sa.inspect(bind)

    # ------------------------------------------------------------------
    # 2. Kolumny user_id + indeksy
    # ------------------------------------------------------------------
    for table in _SCOPED_TABLES:
        if not _has_table(inspector, table):
            # Tabela pojawi się dopiero przy create_all() — nic do migrowania.
            continue
        if not _has_column(inspector, table, "user_id"):
            op.add_column(table, sa.Column("user_id", sa.Integer(), nullable=True))
        index_name = f"ix_{table}_user_id"
        if not _has_index(sa.inspect(bind), table, index_name):
            op.create_index(index_name, table, ["user_id"])

    # ------------------------------------------------------------------
    # 3. Backfill — osierocone wiersze przypisz pierwszemu adminowi
    # ------------------------------------------------------------------
    inspector = sa.inspect(bind)
    if not _has_table(inspector, "users"):
        return

    admin_id = bind.execute(
        sa.text("SELECT id FROM users WHERE role = 'admin' ORDER BY id LIMIT 1")
    ).scalar()
    if admin_id is None:
        # Brak admina — zostawiamy user_id IS NULL. Po naprawie P0-3 takie
        # wiersze widzi wyłącznie admin, więc nie ma wycieku danych.
        return

    for table in _SCOPED_TABLES:
        if not _has_table(inspector, table):
            continue
        bind.execute(
            sa.text(f"UPDATE {table} SET user_id = :admin_id WHERE user_id IS NULL"),  # noqa: S608
            {"admin_id": admin_id},
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    for table in _SCOPED_TABLES:
        if not _has_table(inspector, table):
            continue
        index_name = f"ix_{table}_user_id"
        if _has_index(inspector, table, index_name):
            op.drop_index(index_name, table_name=table)
        if _has_column(inspector, table, "user_id"):
            op.drop_column(table, "user_id")

    if _has_table(inspector, "users"):
        op.drop_index("ix_users_username", table_name="users")
        op.drop_table("users")
