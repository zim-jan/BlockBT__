"""
Tests for database schema creation and basic CRUD.
"""

from __future__ import annotations

import pytest

from blockbt.db.models import SimulationResult, StrategyTemplate, User


class TestDatabaseSchema:
    """Verify that all ORM tables are created correctly."""

    def test_init_db_creates_tables(self, tmp_path, monkeypatch):
        """init_db() should create all three tables without errors."""
        db_url = f"sqlite:///{tmp_path}/test.db"
        monkeypatch.setenv("DATABASE_URL", db_url)
        from importlib import reload

        monkeypatch.setenv("SECRET_KEY", "yNmj9oJp0YJXY7vWvJ0M2bI-W3k6U_X1qR5u7M_fA-Q=")
        import blockbt.config as cfg_mod
        import blockbt.db.session as s_mod

        reload(cfg_mod)
        reload(s_mod)
        from blockbt.db.session import drop_db

        init_db()
        drop_db()  # cleanup


class TestUserModel:
    def test_create_user(self, db_session):
        user = User(
            username="alice",
            email="alice@example.com",
            password_hash="$2b$12$fakehashvalue",
        )
        db_session.add(user)
        db_session.flush()
        assert user.id is not None
        assert user.is_active is True

    def test_username_uniqueness(self, db_session):
        from sqlalchemy.exc import IntegrityError

        db_session.add(User(username="bob", email="bob@a.com", password_hash="x"))
        db_session.flush()
        with pytest.raises(IntegrityError):
            db_session.add(User(username="bob", email="bob2@a.com", password_hash="x"))
            db_session.flush()

    def test_encrypted_api_keys(self, db_session):
        """Verify that api_keys_json is encrypted in the DB and decrypted on read."""
        user = User(
            username="crypto",
            email="crypto@example.com",
            password_hash="x",
            api_keys_json='{"binance": "secret123"}',
        )
        db_session.add(user)
        db_session.flush()

        # Access via ORM - should be decrypted
        assert user.api_keys_json == '{"binance": "secret123"}'

        # Access via raw SQL - should be encrypted
        from sqlalchemy import text

        result = db_session.execute(
            text("SELECT api_keys_json FROM users WHERE username = 'crypto'")
        ).scalar()

        # The raw DB value should not be the plaintext string
        assert result != '{"binance": "secret123"}'
        # Fernet tokens usually start with 'gAAAAA'
        assert result.startswith("gAAAAA")


class TestStrategyTemplateModel:
    def _make_user(self, session) -> User:
        u = User(username="testuser", email="t@t.com", password_hash="h")
        session.add(u)
        session.flush()
        return u

    def test_create_template(self, db_session):
        user = self._make_user(db_session)
        tpl = StrategyTemplate(
            user_id=user.id,
            name="SMA Crossover",
            engine_type="opensource",
            wizard_state={"schema_version": "1.0", "symbol": "AAPL"},
        )
        db_session.add(tpl)
        db_session.flush()
        assert tpl.id is not None
        assert tpl.is_archived is False

    def test_wizard_state_round_trip(self, db_session):
        """wizard_state JSON is preserved exactly."""
        user = self._make_user(db_session)
        state = {"schema_version": "1.0", "symbol": "MSFT", "initial_capital": 5000.0}
        tpl = StrategyTemplate(
            user_id=user.id,
            name="Test",
            engine_type="opensource",
            wizard_state=state,
        )
        db_session.add(tpl)
        db_session.flush()
        db_session.expire(tpl)
        loaded = db_session.get(StrategyTemplate, tpl.id)
        assert loaded.wizard_state == state


class TestSimulationResultModel:
    def test_create_result(self, db_session):
        from datetime import datetime

        user = User(username="u", email="u@u.com", password_hash="h")
        db_session.add(user)
        db_session.flush()
        tpl = StrategyTemplate(
            user_id=user.id,
            name="T",
            engine_type="opensource",
            wizard_state={},
        )
        db_session.add(tpl)
        db_session.flush()

        result = SimulationResult(
            strategy_template_id=tpl.id,
            symbol="AAPL",
            timeframe="1d",
            period_start=datetime(2022, 1, 1),
            period_end=datetime(2022, 12, 31),
            engine_used="opensource",
            initial_capital=10_000.0,
            total_return_pct=12.5,
            status="completed",
        )
        db_session.add(result)
        db_session.flush()
        assert result.id is not None
        assert result.status == "completed"
