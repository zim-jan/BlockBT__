
from datetime import UTC, datetime
from typing import Any

from app.core.config import settings

# from app.services.engine.base import dict[str, Any]
from app.services.mcp.protocol import (
    MCPContext,
    MCPMetrics,
    MCPPayload,
    MCPPeriod,
)

"""
ReportBuilder — converts a dict[str, Any] into a ready-to-send MCPPayload.

Handles:
- Equity curve downsampling (configurable max points)
- Metric normalisation and null-safety
- Timestamp generation

Usage:
    from app.services.mcp.report_builder import ReportBuilder
    from typing import Any
# from app.services.engine.base import dict[str, Any]

    payload = ReportBuilder.build(result, strategy_name="My SMA Strategy")
    print(payload.to_prompt())          # send to LLM as user message
    print(payload.to_json())            # store in DB as mcp_payload_json
"""




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
            generated_at=datetime.now(UTC).isoformat(),
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
        equity_curve = result.get("equity_curve")
        if equity_curve is not None and len(equity_curve) > 0:
            if (
                isinstance(equity_curve, list)
                and isinstance(equity_curve[0], dict)
                and "date" in equity_curve[0]
            ):
                return str(equity_curve[0]["date"]), str(equity_curve[-1]["date"])
            elif isinstance(equity_curve, dict) and "index" in equity_curve:
                # Handle dict serialized from pandas DataFrame
                idx = equity_curve["index"]
                if len(idx) > 0:
                    return str(idx[0]), str(idx[-1])
            elif hasattr(equity_curve, "index"):
                # Handle raw pandas Series gracefully if passed directly
                idx = equity_curve.index
                if len(idx) > 0:
                    start = str(idx[0].date() if hasattr(idx[0], "date") else idx[0])
                    end = str(idx[-1].date() if hasattr(idx[-1], "date") else idx[-1])
                    return start, end
        return "unknown", "unknown"

    @staticmethod
    def _sample_equity_curve(
        equity: list | dict | Any | None,
        max_points: int,
    ) -> list[dict[str, Any]]:
        """Downsample the equity curve to at most ``max_points`` entries.

        Returns a list of ``{"date": "...", "value": ...}`` dicts for JSON.
        """
        if equity is None or len(equity) == 0:
            return []

        # Faza 10: multi-symbol equity_curve = {symbol: [punkty...]} — raportowanie multi
        # odroczone; pomijamy bez błędu (early-return), by nie wywrócić budowania raportu.
        if isinstance(equity, dict) and equity and all(
            isinstance(v, list) for v in equity.values()
        ):
            return []

        # If it's a list of dicts or list of floats
        if isinstance(equity, list):
            n = len(equity)
            step = 1 if n <= max_points else n // max_points
            sampled = equity[::step]

            result_list = []
            for i, item in enumerate(sampled):
                if isinstance(item, dict) and "value" in item:
                    # List of dicts
                    date_val = str(item.get("date", f"step_{i}"))
                    result_list.append({"date": date_val, "value": round(float(item["value"]), 2)})
                else:
                    # List of floats (or other scalar types)
                    result_list.append({"date": f"step_{i * step}", "value": round(float(item), 2)})
            return result_list

        # If it's a dict (e.g., serialized from pandas Series)
        if isinstance(equity, dict) and "data" in equity and "index" in equity:
            data = equity["data"]
            idx = equity["index"]
            n = len(data)
            step = 1 if n <= max_points else n // max_points

            sampled_data = data[::step]
            sampled_idx = idx[::step]

            return [
                {"date": str(d), "value": round(float(v), 2)}
                for d, v in zip(sampled_idx, sampled_data, strict=False)
            ]

        # Handle raw pandas Series if passed directly by tests
        if hasattr(equity, "iloc") and hasattr(equity, "items"):
            n = len(equity)
            if n > max_points:
                step = n // max_points
                equity = equity.iloc[::step]

            return [
                {
                    "date": str(ts.date() if hasattr(ts, "date") else ts),
                    "value": round(float(val), 2),
                }
                for ts, val in equity.items()
            ]

        # Fallback if structure is unknown but evaluates to True
        return []
