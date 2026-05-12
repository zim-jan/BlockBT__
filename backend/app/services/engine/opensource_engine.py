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

    ENGINE_NAME = "opensource"

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

    def run_backtest(self, data: pd.DataFrame, params: dict[str, Any]) -> dict[str, Any]:
        """Run a vectorbt-powered backtest.
        Supports both single-run and vectorized (multi-parameter) execution.
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

        # Build entries / exits using consolidated IndicatorService
        entries, exits = IndicatorService.generate_signals(data["close"], params, vbt)

        # Simulate
        initial_capital = float(params.get("initial_capital", 10000.0))
        fees = float(params.get("fees", {}).get("commission_pct", 0.001)) if isinstance(params.get("fees"), dict) else float(params.get("fees", 0.001))

        is_vectorized = isinstance(entries, pd.DataFrame)
        logger.info(
            "Executing vectorbt portfolio... (shape={}, capital={}, vectorized={})",
            data.shape,
            initial_capital,
            is_vectorized,
        )

        portfolio = vbt.Portfolio.from_signals(
            data["close"],
            entries,
            exits,
            init_cash=initial_capital,
            fees=fees,
            freq="D",  # vectorbt needs frequency for annualisation
        )

        symbol = params.get("symbol", "UNKNOWN")
        timeframe = params.get("timeframe", "1d")

        if not is_vectorized:
            # Standard single result
            stats = portfolio.stats()
            
            total_return = float(portfolio.total_return() * 100)
            sharpe = float(portfolio.sharpe_ratio())
            drawdown = float(portfolio.max_drawdown() * 100)
            win_rate = float(portfolio.trades.win_rate() * 100) if portfolio.trades.count() > 0 else 0.0
            trades_count = int(portfolio.trades.count())
            final_val = float(portfolio.value().iloc[-1] if len(portfolio.value()) > 0 else initial_capital)

            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "engine_name": self.ENGINE_NAME,
                "status": "COMPLETED",
                "total_return_pct": total_return,
                "sharpe_ratio": sharpe,
                "max_drawdown_pct": drawdown,
                "win_rate_pct": win_rate,
                "num_trades": trades_count,
                "initial_capital": initial_capital,
                "final_capital": final_val,
                "equity_curve": portfolio.value(),
                "metrics": {
                    "Total Return [%]": total_return,
                    "Sharpe Ratio": sharpe,
                    "Max Drawdown [%]": drawdown,
                    "Total Trades": trades_count,
                    "Final Value": final_val,
                    "Win Rate [%]": win_rate,
                },
                "raw": stats.to_dict() if hasattr(stats, "to_dict") else dict(stats),
            }
        else:
            # Vectorized multi-result
            total_return = portfolio.total_return() * 100
            sharpe = portfolio.sharpe_ratio()
            drawdown = portfolio.max_drawdown() * 100
            trades_count = portfolio.trades.count()
            final_value = portfolio.value().iloc[-1]
            win_rate = portfolio.trades.win_rate() * 100

            # Convert MultiIndex to list of dictionaries
            results_list = []
            for i in range(len(total_return)):
                results_list.append({
                    "metrics": {
                        "Total Return [%]": float(total_return.iloc[i]),
                        "Sharpe Ratio": float(sharpe.iloc[i]) if not np.isnan(sharpe.iloc[i]) else 0.0,
                        "Max Drawdown [%]": float(drawdown.iloc[i]),
                        "Total Trades": int(trades_count.iloc[i]),
                        "Final Value": float(final_value.iloc[i]),
                        "Win Rate [%]": float(win_rate.iloc[i]) if not np.isnan(win_rate.iloc[i]) else 0.0,
                    }
                })

            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "engine_name": self.ENGINE_NAME,
                "status": "COMPLETED",
                "is_vectorized": True,
                "vectorized_results": results_list,
            }
