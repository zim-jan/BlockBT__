"""
ReportBuilder — converts a dict[str, Any] into a ready-to-send MCPPayload.

Handles:
- Equity curve downsampling (configurable max points)
- Metric normalisation and null-safety
- Timestamp generation

Usage:
    from blockbt.mcp.report_builder import ReportBuilder
    from typing import Any
# from blockbt.engine.base import dict[str, Any]

    payload = ReportBuilder.build(result, strategy_name="My SMA Strategy")
    print(payload.to_prompt())          # send to LLM as user message
    print(payload.to_json())            # store in DB as mcp_payload_json
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pandas as pd

from blockbt.config import settings
from typing import Any
# from blockbt.engine.base import dict[str, Any]
from blockbt.mcp.protocol import (
    MCPContext,
    MCPMetrics,
    MCPPayload,
    MCPPeriod,
)


class ReportBuilder:
    """Transforms a dict[str, Any] into a structured MCPPayload."""

    @classmethod
    def build(
        cls,
        result: dict[str, Any],
        strategy_name: str = "Unnamed Strategy",
        raw_params: dict[str, Any] | None = None,
        max_equity_points: int | None = None,
    ) -> MCPPayload:
        """Build an MCPPayload from a completed backtest result.

        Parameters
        ----------
        result:           Completed dict[str, Any] from any engine.
        strategy_name:    Human name of the strategy (from wizard_state).
        raw_params:       Original wizard_state params for reference.
        max_equity_points:
            Max equity curve samples to embed. Defaults to settings value.
        """
        max_pts = max_equity_points or settings.MCP_EQUITY_CURVE_MAX_POINTS

        # Determine period from equity curve or result metadata
        period_start, period_end = cls._extract_period(result)

        context = MCPContext(
            strategy_name=strategy_name,
            symbol=result.get("symbol", "UNKNOWN"),
            timeframe=result.get("timeframe", "1d"),
            period=MCPPeriod(start=period_start, end=period_end),
            engine=result.get("engine_name", "base"),
            initial_capital=result.get("initial_capital", 10000.0),
        )

        metrics = MCPMetrics(
            total_return_pct=result.get("total_return_pct", 0.0),
            sharpe_ratio=result.get("sharpe_ratio", 0.0),
            max_drawdown_pct=result.get("max_drawdown_pct", 0.0),
            win_rate_pct=result.get("win_rate_pct", 0.0),
            num_trades=result.get("num_trades", 0),
            final_capital=result.get("final_capital", 0.0),
        )

        equity_samples = cls._sample_equity_curve(result.get("equity_curve"), max_pts)

        return MCPPayload(
            schema_version="1.0",
            generated_at=datetime.now(timezone.utc).isoformat(),
            context=context,
            metrics=metrics,
            equity_curve_samples=equity_samples,
            raw_params=raw_params or {},
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_period(result: dict[str, Any]) -> tuple[str, str]:
        """Extract ISO date strings for the simulation period."""
        if result.get("equity_curve") is not None and not result.get("equity_curve").empty:
            idx = result.get("equity_curve").index
            return str(idx[0].date()), str(idx[-1].date())
        return "unknown", "unknown"

    @staticmethod
    def _sample_equity_curve(
        equity: pd.Series | None,
        max_points: int,
    ) -> list[dict[str, Any]]:
        """Downsample the equity curve to at most ``max_points`` entries.

        Returns a list of ``{"date": "...", "value": ...}`` dicts for JSON.
        """
        if equity is None or equity.empty:
            return []

        n = len(equity)
        if n > max_points:
            step = n // max_points
            equity = equity.iloc[::step]

        return [
            {"date": str(ts.date() if hasattr(ts, "date") else ts), "value": round(float(val), 2)}
            for ts, val in equity.items()
        ]
