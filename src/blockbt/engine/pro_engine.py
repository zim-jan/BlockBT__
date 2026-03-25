"""
ProEngine — BYOL (Bring Your Own License) engine backed by vectorbtpro.

The library is NEVER imported at module level.  All imports are lazy and
guarded, so this file can always be imported safely regardless of whether
the user has supplied a vectorbtpro installation.

BYOL loading order:
  1. Check ``settings.effective_vbtpro_path()`` (env override or sibling dir)
  2. Add the path to ``sys.path``
  3. Attempt ``import vectorbtpro``
  4. If import succeeds   → delegate to vbtpro
  5. If import fails      → fall back to built-in mock stubs (clearly logged)
"""

from __future__ import annotations

import sys
from typing import Any

import pandas as pd
from loguru import logger

from blockbt.config import settings
from blockbt.engine.base import BacktestResult, BaseStrategyEngine


class ProEngine(BaseStrategyEngine):
    """Engine that wraps vectorbtpro via BYOL dynamic import.

    When the user has NOT supplied a vbtpro installation the engine still
    works — it runs a stub simulation so the application never hard-crashes.
    All stub outputs are clearly labelled ``engine_name="pro_mock"``.
    """

    ENGINE_NAME = "pro"

    def __init__(self) -> None:
        self._vbtpro: Any | None = None
        self._mock_mode: bool = False
        self._load_library()

    # ------------------------------------------------------------------
    # Library loading (BYOL)
    # ------------------------------------------------------------------

    def _load_library(self) -> None:
        """Attempt to import vectorbtpro.  Sets ``_mock_mode`` on failure."""
        pro_path = settings.effective_vbtpro_path()
        if pro_path and str(pro_path) not in sys.path:
            sys.path.insert(0, str(pro_path))
            logger.debug("ProEngine: added {} to sys.path", pro_path)

        try:
            import vectorbtpro as vbtpro  # type: ignore[import]

            self._vbtpro = vbtpro
            self._mock_mode = False
            logger.info(
                "ProEngine: vectorbtpro {} loaded successfully.",
                getattr(vbtpro, "__version__", "?"),
            )
        except ImportError:
            self._vbtpro = None
            self._mock_mode = True
            logger.warning(
                "ProEngine: vectorbtpro not importable — running in MOCK mode. "
                "Supply your licensed copy at: {}",
                settings.effective_vbtpro_path() or "<not configured>",
            )

    # ------------------------------------------------------------------
    # BaseStrategyEngine interface
    # ------------------------------------------------------------------

    def is_available(self) -> bool:
        return not self._mock_mode

    @property
    def ENGINE_VERSION(self) -> str:  # type: ignore[override]
        if self._vbtpro:
            return str(getattr(self._vbtpro, "__version__", "unknown"))
        return "mock"

    def run_backtest(
        self,
        data: pd.DataFrame,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        if self._mock_mode:
            return self._run_mock_backtest(data, params)
        return self._run_pro_backtest(data, params)

    def get_engine_info(self) -> dict[str, str]:
        return {
            "name": self.ENGINE_NAME,
            "version": self.ENGINE_VERSION,
            "mode": "mock" if self._mock_mode else "live",
            "library": "vectorbtpro (BYOL)" if not self._mock_mode else "vectorbtpro (BYOL — not loaded)",
            "vbtpro_path": str(settings.effective_vbtpro_path() or "not-configured"),
        }

    # ------------------------------------------------------------------
    # Live PRO path (delegated to vbtpro once unlocked)
    # ------------------------------------------------------------------

    def _run_pro_backtest(
        self,
        data: pd.DataFrame,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """Delegate backtest to the real vectorbtpro API.

        This method intentionally uses the same high-level pattern as
        OpenSourceEngine so the diff between OSS and PRO paths is minimal.
        vbtpro-specific features (e.g. Numba JIT, SuperFast Portfolio) can be
        enabled here without touching anything else.
        """
        vbt = self._vbtpro
        symbol = params.get("symbol", "UNKNOWN")
        timeframe = params.get("timeframe", "1d")
        initial_capital = float(params.get("initial_capital", 10_000.0))
        fees = float(params.get("fees", {}).get("commission_pct", 0.001))

        close = data["close"]

        # vbtpro uses the same from_signals API as the OSS version,
        # but with access to Numba JIT, parallel execution, etc.
        fast_ma = vbt.MA.run(close, window=20).ma
        slow_ma = vbt.MA.run(close, window=50).ma

        portfolio = vbt.Portfolio.from_signals(
            close,
            entries=fast_ma.vbt.crossed_above(slow_ma),
            exits=fast_ma.vbt.crossed_below(slow_ma),
            init_cash=initial_capital,
            fees=fees,
            freq="D",
        )

        stats = portfolio.stats()
        equity = portfolio.value()

        return dict(
            symbol=symbol,
            timeframe=timeframe,
            engine_name=self.ENGINE_NAME,
            total_return_pct=self._scalar(stats, "Total Return [%]"),
            sharpe_ratio=self._scalar(stats, "Sharpe Ratio"),
            max_drawdown_pct=self._scalar(stats, "Max Drawdown [%]"),
            win_rate_pct=self._scalar(stats, "Win Rate [%]"),
            num_trades=self._scalar_int(stats, "Total Trades"),
            initial_capital=initial_capital,
            final_capital=self._scalar(stats, "End Value"),
            equity_curve=equity,
            raw=stats.to_dict() if hasattr(stats, "to_dict") else dict(stats),
        )

    # ------------------------------------------------------------------
    # Mock path (vbtpro not available)
    # ------------------------------------------------------------------

    def _run_mock_backtest(
        self,
        data: pd.DataFrame,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """Return a clearly-labelled stub result when vbtpro is absent.

        Mock values are deterministic (fixed seed random walk on equity curve)
        so unit tests can assert on them without needing a vbtpro license.
        """
        import numpy as np

        logger.warning("ProEngine: returning MOCK backtest result — no real computation.")

        symbol = params.get("symbol", "UNKNOWN")
        timeframe = params.get("timeframe", "1d")
        initial_capital = float(params.get("initial_capital", 10_000.0))

        rng = np.random.default_rng(seed=42)
        n = len(data)
        returns = rng.normal(loc=0.0005, scale=0.01, size=n)
        equity = pd.Series(
            initial_capital * (1 + returns).cumprod(),
            index=data.index,
            name="equity",
        )

        total_return = float((equity.iloc[-1] / initial_capital - 1) * 100)

        return dict(
            symbol=symbol,
            timeframe=timeframe,
            engine_name="pro_mock",  # clearly indicates mock mode
            total_return_pct=round(total_return, 4),
            sharpe_ratio=round(float(rng.normal(1.2, 0.2)), 4),
            max_drawdown_pct=round(float(abs(rng.normal(15.0, 5.0))), 4),
            win_rate_pct=round(float(rng.uniform(45.0, 65.0)), 4),
            num_trades=int(rng.integers(10, 80)),
            initial_capital=initial_capital,
            final_capital=round(float(equity.iloc[-1]), 2),
            equity_curve=equity,
            raw={"mock": True, "note": "vectorbtpro not installed — BYOL required"},
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _scalar(stats: Any, key: str) -> float | None:
        import math

        try:
            v = float(stats[key])
            return None if math.isnan(v) else v
        except (KeyError, TypeError, ValueError):
            return None

    @staticmethod
    def _scalar_int(stats: Any, key: str) -> int | None:
        try:
            return int(stats[key])
        except (KeyError, TypeError, ValueError):
            return None
