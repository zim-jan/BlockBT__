"""
OpenSourceEngine — BackBT engine backed by the public vectorbt library.

The vendored ``vectorbt/`` directory is added to sys.path at load time so no
system-wide installation is required.
"""

from __future__ import annotations

import sys
from typing import Any

import numpy as np
import pandas as pd
from loguru import logger

from blockbt.config import settings
from blockbt.engine.base import BacktestResult, BaseStrategyEngine
from blockbt.engine.indicators import IndicatorService

# ---------------------------------------------------------------------------
# Make vendored vectorbt importable before anything else touches it.
# ---------------------------------------------------------------------------
_VENDORED_VBT = settings.PROJECT_ROOT / "vectorbt"
if _VENDORED_VBT.exists() and str(_VENDORED_VBT) not in sys.path:
    sys.path.insert(0, str(_VENDORED_VBT))


class OpenSourceEngine(BaseStrategyEngine):
    """Backtest engine using the public open-source ``vectorbt`` library.

    Capabilities (Phase 1 MVP):
    - Simple SMA crossover strategy as a proof-of-concept runner.
    - Computes headline metrics: total return, Sharpe, max drawdown, win rate.
    - Full portfolio stats stored in ``BacktestResult.raw``.

    Extension points:
    - Override ``_build_entries_exits`` to plug in richer indicator logic.
    - The ``params`` dict keys mirror the ``wizard_state`` JSON schema.
    """

    ENGINE_NAME = "opensource"

    @property
    def ENGINE_VERSION(self) -> str:  # type: ignore[override]
        try:
            import vectorbt as vbt  # type: ignore[import]

            return str(getattr(vbt, "__version__", "unknown"))
        except ImportError:
            return "not-installed"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_backtest(
        self,
        data: pd.DataFrame,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """Run a vectorbt-powered backtest.

        Parameters
        ----------
        data:   OHLCV DataFrame (DatetimeIndex, lowercase column names).
        params: Strategy parameters from ``wizard_state``.
        """
        try:
            import vectorbt as vbt  # type: ignore[import]
        except ImportError as exc:
            raise RuntimeError(
                "vectorbt is not importable. Ensure the vendored copy is intact "
                f"at {_VENDORED_VBT}."
            ) from exc

        symbol = params.get("symbol", "UNKNOWN")
        timeframe = params.get("timeframe", "1d")
        initial_capital = float(params.get("initial_capital", 10_000.0))
        fees = float(params.get("fees", {}).get("commission_pct", 0.001))

        close = data["close"]

        # ------------------------------------------------------------------
        # Generowanie sygnałów wejścia / wyjścia z użyciem IndicatorService
        # ------------------------------------------------------------------
        indicator_service = IndicatorService()
        entries, exits = indicator_service.generate_signals(close, params, vbt)

        # ------------------------------------------------------------------
        # Run portfolio simulation
        # ------------------------------------------------------------------
        portfolio = vbt.Portfolio.from_signals(
            close,
            entries=entries,
            exits=exits,
            init_cash=initial_capital,
            fees=fees,
            freq="D",  # vectorbt needs frequency for annualisation
        )

        stats = portfolio.stats()
        equity = portfolio.value()

        logger.debug(
            "OpenSourceEngine backtest completed | symbol={} trades={}",
            symbol,
            stats.get("Total Trades", "N/A"),
        )

        # Return dictionary instead of BacktestResult to meet the strict requirement
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "engine_name": self.ENGINE_NAME,
            "total_return_pct": self._safe_float(stats.get("Total Return [%]")),
            "sharpe_ratio": self._safe_float(stats.get("Sharpe Ratio")),
            "max_drawdown_pct": self._safe_float(stats.get("Max Drawdown [%]")),
            "win_rate_pct": self._safe_float(stats.get("Win Rate [%]")),
            "num_trades": self._safe_int(stats.get("Total Trades")),
            "initial_capital": initial_capital,
            "final_capital": self._safe_float(stats.get("End Value")),
            "equity_curve": equity,
            "raw": stats.to_dict() if hasattr(stats, "to_dict") else dict(stats),
        }

    def get_engine_info(self) -> dict[str, str]:
        return {
            "name": self.ENGINE_NAME,
            "version": self.ENGINE_VERSION,
            "library": "vectorbt (open-source)",
            "vbt_path": str(_VENDORED_VBT),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _safe_float(value: Any) -> float | None:
        try:
            f = float(value)
            return None if np.isnan(f) else f
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _safe_int(value: Any) -> int | None:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
