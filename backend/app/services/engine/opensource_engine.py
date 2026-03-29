from __future__ import annotations

"""
OpenSourceEngine — BackBT engine backed by the public vectorbt library.

The vendored ``vectorbt/`` directory is added to sys.path at load time so no
system-wide installation is required.
"""


import sys
from typing import Any

import numpy as np
import pandas as pd
from loguru import logger

from app.core.config import settings
from app.services.engine.base import BaseStrategyEngine
from app.services.engine.indicators import IndicatorService

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
    - Full portfolio stats stored in ``raw``.

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

    def _build_entries_exits(
        self,
        close: pd.Series,
        params: dict[str, Any],
        vbt: Any,
    ) -> tuple[pd.Series, pd.Series]:
        """Translate wizard_state parameters into boolean signal series.
        
        Supports Phase 5: MACD strategy via vectorbt.
        Falls back to Phase 1 SMA Crossover via vectorbt.
        """
        strategy_type = params.get("strategy_type", "sma_crossover")

        if strategy_type == "visual_ast":
            ast = params.get("ast", {})
            nodes = {n.get("id"): n for n in ast.get("nodes", [])}
            # Przykładowy parser prototypowy szukający bloków domyślnego przykładu 
            # w pełnej wersji wykorzystywalibyśmy dynamiczne węzły i parser grafowy
            
            fast_ma = vbt.MA.run(close, window=10).ma
            slow_ma = vbt.MA.run(close, window=50).ma
            logger.info("OpenSourceEngine: parsed Graph AST with nodes: {}", list(nodes.keys()))
            
            entries = fast_ma.vbt.crossed_above(slow_ma)
            exits = fast_ma.vbt.crossed_below(slow_ma)
            return entries, exits

        if strategy_type == "macd":
            fast = params.get("macd_fast", 12)
            slow = params.get("macd_slow", 26)
            signal = params.get("macd_signal", 9)

            # Calculate MACD directly on the Series using vectorbt
            macd = vbt.MACD.run(close, fast_window=fast, slow_window=slow, signal_window=signal)
            
            macd_line = macd.macd
            sig_line = macd.signal
            
            # Crossover logic:
            # Entry: MACD crosses ABOVE Signal
            entries = macd_line.vbt.crossed_above(sig_line)
            # Exit: MACD crosses BELOW Signal
            exits = macd_line.vbt.crossed_below(sig_line)
            
            return entries, exits

        # -------------------------------------------------------------
        # Fallback: Default SMA Crossover
        # -------------------------------------------------------------
        fast_w = params.get("sma_fast", 10)
        slow_w = params.get("sma_slow", 30)

        fast_ma = vbt.MA.run(close, window=fast_w).ma
        slow_ma = vbt.MA.run(close, window=slow_w).ma

        entries = fast_ma.vbt.crossed_above(slow_ma)
        exits = fast_ma.vbt.crossed_below(slow_ma)

        return entries, exits

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
