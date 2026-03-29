"""
BlockBT Phase 2 ORM models — Strategy & BacktestJob.

These are the lightweight models used by the REST API layer.


"""

from __future__ import annotations

import datetime
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import JSON


def _utcnow() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    """Dedicated base for Phase 2 REST API models."""
    pass


# ---------------------------------------------------------------------------
# Strategy
# ---------------------------------------------------------------------------


class Strategy(Base):
    """A user-defined trading strategy configuration.

    Parameters are stored as a JSON blob for schema-flexibility.
    Key fields (symbol, sma_fast, sma_slow, initial_capital, …) live
    inside `parameters` — the engine reads them at runtime.
    """

    __tablename__ = "strategies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    parameters: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, default=_utcnow
    )

    # relationships
    backtest_jobs: Mapped[list[BacktestJob]] = relationship(
        "BacktestJob", back_populates="strategy", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Strategy id={self.id} name={self.name!r}>"


# ---------------------------------------------------------------------------
# BacktestJob
# ---------------------------------------------------------------------------

class JobStatus:
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class BacktestJob(Base):
    """A single backtest execution record.

    Lifecycle: PENDING → RUNNING → COMPLETED | FAILED
    Metrics (Sharpe, MaxDD, TotalReturn …) are stored in `metrics` JSON
    for maximum flexibility. Headline scalars are also broken out as
    individual Float columns for fast SQL queries.
    """

    __tablename__ = "backtest_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    strategy_id: Mapped[int] = mapped_column(
        ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False
    )

    # Execution state
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default=JobStatus.PENDING
    )  # PENDING | RUNNING | COMPLETED | FAILED

    # Payload passed to the engine (snapshot of strategy params at job start)
    parameters_snapshot: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default=dict
    )

    # Results
    metrics: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    total_return_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    sharpe_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_drawdown_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    num_trades: Mapped[int | None] = mapped_column(Integer, nullable=True)
    final_capital: Mapped[float | None] = mapped_column(Float, nullable=True)

    ai_analysis_report: Mapped[str | None] = mapped_column(Text, nullable=True)

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, default=_utcnow
    )
    completed_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)

    # relationships
    strategy: Mapped[Strategy] = relationship("Strategy", back_populates="backtest_jobs")

    def __repr__(self) -> str:
        return f"<BacktestJob id={self.id} status={self.status!r}>"
