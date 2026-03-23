"""
BlockBT ORM models — SQLAlchemy 2.x declarative with type annotations.

Tables:
  - users
  - strategy_templates
  - simulation_results
"""

from __future__ import annotations

import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from blockbt.db.base import Base

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _utcnow() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------


class User(Base):
    """An authenticated identity that owns strategy templates.

    Notes
    -----
    - ``password_hash`` stores a bcrypt digest (60 chars).
    - ``api_keys_json`` holds a plaintext JSON dict in Phase 1.
      Phase 2 will encrypt this column with Fernet.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    api_keys_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, default=_utcnow, onupdate=_utcnow
    )

    # relationships
    strategy_templates: Mapped[list["StrategyTemplate"]] = relationship(
        "StrategyTemplate", back_populates="user", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username!r}>"


# ---------------------------------------------------------------------------
# StrategyTemplate
# ---------------------------------------------------------------------------


class StrategyTemplate(Base):
    """Saved wizard state owned by a User.

    The ``wizard_state`` column holds the complete form state as a JSON blob,
    making forward/backward compatibility easy — just bump ``schema_version``
    inside the blob when the wizard changes.
    """

    __tablename__ = "strategy_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    engine_type: Mapped[str] = mapped_column(
        String(32), nullable=False, default="opensource"
    )
    wizard_state: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, default=_utcnow, onupdate=_utcnow
    )

    # relationships
    user: Mapped["User"] = relationship("User", back_populates="strategy_templates")
    simulation_results: Mapped[list["SimulationResult"]] = relationship(
        "SimulationResult", back_populates="strategy_template", lazy="select"
    )

    __table_args__ = (
        Index("ix_strategy_templates_user_id", "user_id"),
        Index("ix_strategy_templates_user_archived", "user_id", "is_archived"),
    )

    def __repr__(self) -> str:
        return (
            f"<StrategyTemplate id={self.id} name={self.name!r} "
            f"engine={self.engine_type!r}>"
        )


# ---------------------------------------------------------------------------
# SimulationResult
# ---------------------------------------------------------------------------


class SimulationResult(Base):
    """Persisted output of a single backtest run.

    Key design choices:
    - Headline scalar metrics (sharpe, drawdown, …) stored as individual
      Float columns for fast SQL filtering / sorting.
    - ``full_metrics_json`` holds the complete engine output — no data lost.
    - ``equity_curve_json`` stores a downsampled series (≤500 pts) for UI.
    - ``mcp_payload_json`` caches the pre-formatted LLM context; regenerated
      on demand if missing.
    """

    __tablename__ = "simulation_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    strategy_template_id: Mapped[int] = mapped_column(
        ForeignKey("strategy_templates.id", ondelete="CASCADE"), nullable=False
    )

    # Simulation configuration snapshot
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    timeframe: Mapped[str] = mapped_column(String(16), nullable=False)
    period_start: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    period_end: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    engine_used: Mapped[str] = mapped_column(String(32), nullable=False)
    initial_capital: Mapped[float] = mapped_column(Float, nullable=False)

    # Headline metrics
    total_return_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    sharpe_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_drawdown_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    win_rate_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    num_trades: Mapped[int | None] = mapped_column(Integer, nullable=True)
    final_capital: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Rich JSON payloads
    full_metrics_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    equity_curve_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    mcp_payload_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Execution metadata
    run_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, default=_utcnow
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="pending"
    )  # pending | running | completed | failed
    error_log: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_analysis_report: Mapped[str | None] = mapped_column(Text, nullable=True)

    # relationships
    strategy_template: Mapped["StrategyTemplate"] = relationship(
        "StrategyTemplate", back_populates="simulation_results"
    )

    __table_args__ = (
        Index("ix_simulation_results_template_id", "strategy_template_id"),
        Index("ix_simulation_results_symbol_run_at", "symbol", "run_at"),
        Index("ix_simulation_results_status", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<SimulationResult id={self.id} symbol={self.symbol!r} "
            f"status={self.status!r}>"
        )
