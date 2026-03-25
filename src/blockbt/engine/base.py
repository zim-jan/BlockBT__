"""
Abstract base class for BlockBT strategy engines.

Every engine — open-source or PRO — must implement this interface so that the
rest of the application code is engine-agnostic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------


@dataclass
class BacktestResult:
    """Minimal, engine-agnostic result container.

    Engine implementations populate the headline fields directly.
    The ``raw`` dict holds the full, engine-specific output for audit trails
    and serialisation into ``SimulationResult.full_metrics_json``.
    """

    symbol: str
    timeframe: str
    engine_name: str

    # Headline metrics (None if engine couldn't compute them)
    total_return_pct: float | None = None
    sharpe_ratio: float | None = None
    max_drawdown_pct: float | None = None
    win_rate_pct: float | None = None
    num_trades: int | None = None
    initial_capital: float = 10_000.0
    final_capital: float | None = None

    # Rich data
    equity_curve: pd.Series | None = None  # index=datetime, value=portfolio_value
    raw: dict[str, Any] = field(default_factory=dict)

    def to_headline_dict(self) -> dict[str, Any]:
        """Return a flat dict of scalar metrics (safe for JSON serialisation)."""
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "engine": self.engine_name,
            "total_return_pct": self.total_return_pct,
            "sharpe_ratio": self.sharpe_ratio,
            "max_drawdown_pct": self.max_drawdown_pct,
            "win_rate_pct": self.win_rate_pct,
            "num_trades": self.num_trades,
            "initial_capital": self.initial_capital,
            "final_capital": self.final_capital,
        }


# ---------------------------------------------------------------------------
# Abstract engine
# ---------------------------------------------------------------------------


class StrategyEngine(ABC):
    """Abstract interface every BackBT execution engine must satisfy.

    Design contract:
    - All methods are **synchronous** (async wrappers at API layer if needed).
    - Engines must never raise ImportError to callers — all missing-library
      handling goes inside the engine class itself.
    - The ``run_backtest`` method accepts a **standardised parameter dict**
      that mirrors the ``wizard_state`` JSON schema; engines translate internally.
    """

    # Human-readable engine identifier — override in subclasses.
    ENGINE_NAME: str = "base"
    ENGINE_VERSION: str = "unknown"

    # ------------------------------------------------------------------
    # Required interface
    # ------------------------------------------------------------------

    @abstractmethod
    def run_backtest(
        self,
        data: pd.DataFrame,
        params: dict[str, Any],
    ) -> BacktestResult:
        """Execute a backtest and return a normalised result.

        Parameters
        ----------
        data:
            OHLCV DataFrame with a DatetimeIndex.  Columns expected:
            ``open``, ``high``, ``low``, ``close``, ``volume`` (all lowercase).
        params:
            Strategy parameters matching the ``wizard_state`` schema.
        """
        ...

    @abstractmethod
    def get_engine_info(self) -> dict[str, str]:
        """Return metadata about this engine installation.

        Must include at least ``name`` and ``version`` keys.
        """
        ...

    # ------------------------------------------------------------------
    # Optional helpers (with sensible defaults)
    # ------------------------------------------------------------------

    def is_available(self) -> bool:
        """Return True if the engine's underlying library is importable.

        Default implementation always returns True (safe for OSS engine).
        ProEngine overrides this to reflect BYOL availability.
        """
        return True

    def validate_params(self, params: dict[str, Any]) -> list[str]:
        """Validate strategy parameters.  Returns a list of error strings.

        Default: no validation (override in concrete engines for strict checks).
        """
        return []

    def get_stats(self, result: BacktestResult) -> dict[str, Any]:
        """Return all statistics from a completed backtest result.

        Default: delegates to ``result.to_headline_dict()``.
        """
        return result.to_headline_dict()

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.ENGINE_NAME!r}>"
