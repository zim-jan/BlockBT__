"""
OpenSourceEngine — BackBT engine backed by the public vectorbt library.

The vendored ``vectorbt/`` directory is added to sys.path at load time so no
pip installation is strictly required if the folder exists.
"""

from __future__ import annotations

import sys
from typing import Any
from pathlib import Path

import numpy as np
import pandas as pd
from loguru import logger

from app.core.config import settings
from app.services.engine.base import BaseStrategyEngine
from app.services.engine.indicators import IndicatorService

# Make vendored vectorbt importable before anything else touches it.
_VENDORED_VBT = settings.PROJECT_ROOT / "vectorbt_src"
if _VENDORED_VBT.exists() and str(_VENDORED_VBT) not in sys.path:
    sys.path.insert(0, str(_VENDORED_VBT))


class OpenSourceEngine(BaseStrategyEngine):
    """Backtest engine using the public open-source ``vectorbt`` library.

    It supports fully vectorized execution, but lacks multi-threaded Numba parallel
    execution and advanced metrics found in vectorbtpro.
    """

    def __init__(self) -> None:
        """Initialize the OpenSource engine, verifying dependencies are present."""
        super().__init__()
        self._ensure_vectorbt()

    def _ensure_vectorbt(self) -> None:
        """Check if vectorbt can be imported."""
        try:
            import vectorbt as vbt  # type: ignore[import]

            self.vbt = vbt
            logger.debug(
                "OpenSourceEngine: vectorbt {} loaded successfully.",
                getattr(vbt, "__version__", "unknown"),
            )
        except ImportError as exc:
            logger.error("OpenSourceEngine: vectorbt could not be loaded: {}", exc)
            raise RuntimeError("vectorbt library missing. Ensure vendored path is correct.") from exc

    def get_engine_info(self) -> dict[str, str]:
        """Return metadata about this engine installation."""
        try:
            import vectorbt as vbt
            version = getattr(vbt, "__version__", "unknown")
        except ImportError:
            version = "missing"

        return {
            "name": self.ENGINE_NAME,
            "version": version,
            "mode": "live",
            "library": "vectorbt (open-source)",
            "vbt_path": str(_VENDORED_VBT) if _VENDORED_VBT.exists() else "not found",
        }

    def run_backtest(self, parameters: dict[str, Any], data: pd.DataFrame) -> dict[str, Any]:
        """Run a vectorbt-powered backtest.

        Returns
        -------
        A flat dictionary mapping string metrics to scalar values.
        """
        try:
            import vectorbt as vbt  # type: ignore[import]
        except ImportError as exc:
            raise RuntimeError(
                "vectorbt is not importable. Ensure the vendored copy is intact "
                f"at {_VENDORED_VBT}."
            ) from exc

        # Ensure datetime index
        if not isinstance(data.index, pd.DatetimeIndex):
            data.index = pd.to_datetime(data.index)

        # Build entries / exits
        entries, exits = self._build_entries_exits(parameters, data, vbt)

        # Simulate
        initial_capital = float(parameters.get("initial_capital", 10000.0))
        fees = float(parameters.get("fees", 0.001))

        logger.info(
            "Executing vectorbt portfolio... (shape={}, capital={})",
            data.shape,
            initial_capital,
        )

        portfolio = vbt.Portfolio.from_signals(
            data["close"],
            entries,
            exits,
            init_cash=initial_capital,
            fees=fees,
            freq="D",  # vectorbt needs frequency for annualisation
        )

        # Extract standard metrics (avoid vbt object to make JSON serialization easy)
        metrics = {
            "Total Return [%]": float(portfolio.total_return() * 100),
            "Benchmark Return [%]": float((data["close"].iloc[-1] / data["close"].iloc[0] - 1) * 100) if len(data) > 0 else 0.0,
            "Max Drawdown [%]": float(portfolio.max_drawdown() * 100),
            "Sharpe Ratio": float(portfolio.sharpe_ratio()),
            "Win Rate [%]": float(portfolio.win_rate() * 100),
            "Total Trades": int(portfolio.trades.count()),
            "Final Value": float(portfolio.value()[-1] if len(portfolio.value()) > 0 else initial_capital),
        }

        logger.info("vectorbt backtest completed. Return: {:.2f}%", metrics["Total Return [%]"])

        return {
            "status": "COMPLETED",
            "engine": "vectorbt-opensource",
            "library": "vectorbt (open-source)",
            "vbt_version": getattr(vbt, "__version__", "unknown"),
            "vbt_path": str(_VENDORED_VBT),
            "metrics": metrics,
        }

    def _build_entries_exits(
        self, parameters: dict[str, Any], df: pd.DataFrame, vbt: Any
    ) -> tuple[pd.Series, pd.Series]:
        """Generate boolean entry/exit signals from parameters.

        Supported strategies:
        - `sma_crossover`: standard Phase 1 default.
        - `macd`: Phase 5 technical indicators via fully vectorized vectorbt native tools.

        Returns
        -------
        Tuple of (entries, exits) Series.
        """
        strategy = parameters.get("strategy_type", "sma_crossover").lower()

        if strategy == "macd":
            logger.debug("Generating MACD signals (vectorbt native)")
            fast = int(parameters.get("sma_fast", 12))
            slow = int(parameters.get("sma_slow", 26))
            signal = int(parameters.get("macd_signal", 9))

            # Calculate MACD directly on the Series using vectorbt
            macd = vbt.MACD.run(
                df["close"],
                fast_window=fast,
                slow_window=slow,
                signal_window=signal,
            )

            macd_line = macd.macd
            sig_line = macd.signal

            entries = macd_line.vbt.crossed_above(sig_line)
            exits = macd_line.vbt.crossed_below(sig_line)

            return entries, exits

        else:
            # Fallback to standard SMA
            logger.debug("Generating SMA Crossover signals")
            fast = int(parameters.get("sma_fast", 10))
            slow = int(parameters.get("sma_slow", 30))

            return IndicatorService.generate_sma_crossover(df["close"], fast, slow, vbt)
