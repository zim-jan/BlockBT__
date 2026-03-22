"""
ReportBuilder — converts a BacktestResult into a ready-to-send MCPPayload.

Handles:
- Equity curve downsampling (configurable max points)
- Metric normalisation and null-safety
- Timestamp generation

Usage:
    from blockbt.mcp.report_builder import ReportBuilder
    from blockbt.engine.base import BacktestResult

    payload = ReportBuilder.build(result, strategy_name="My SMA Strategy")
    print(payload.to_prompt())          # send to LLM as user message
    print(payload.to_json())            # store in DB as mcp_payload_json
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pandas as pd

from blockbt.config import settings
from blockbt.engine.base import BacktestResult
from blockbt.mcp.protocol import (
    MCPContext,
    MCPMetrics,
    MCPPayload,
    MCPPeriod,
)


class ReportBuilder:
    """Transforms a BacktestResult into a structured MCPPayload."""

    @classmethod
    def build(
        cls,
        result: BacktestResult,
        strategy_name: str = "Unnamed Strategy",
        raw_params: dict[str, Any] | None = None,
        max_equity_points: int | None = None,
    ) -> MCPPayload:
        """Build an MCPPayload from a completed backtest result.

        Parameters
        ----------
        result:           Completed BacktestResult from any engine.
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
            symbol=result.symbol,
            timeframe=result.timeframe,
            period=MCPPeriod(start=period_start, end=period_end),
            engine=result.engine_name,
            initial_capital=result.initial_capital,
        )

        metrics = MCPMetrics(
            total_return_pct=result.total_return_pct,
            sharpe_ratio=result.sharpe_ratio,
            max_drawdown_pct=result.max_drawdown_pct,
            win_rate_pct=result.win_rate_pct,
            num_trades=result.num_trades,
            final_capital=result.final_capital,
        )

        equity_samples = cls._sample_equity_curve(result.equity_curve, max_pts)

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
    def _extract_period(result: BacktestResult) -> tuple[str, str]:
        """Extract ISO date strings for the simulation period."""
        if result.equity_curve is not None and not result.equity_curve.empty:
            idx = result.equity_curve.index
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
