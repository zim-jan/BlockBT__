from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any

"""
MCP Protocol — Model Context Protocol data structures for BlockBT.

Defines the standard ``MCPPayload`` that wraps a backtest result into a
structured, LLM-ready context object.  This is the "envelope" — a versioned
JSON schema that any LLM adapter can consume without knowing BlockBT internals.
"""




@dataclass
class MCPPeriod:
    start: str
    end: str


@dataclass
class MCPContext:
    strategy_name: str
    symbol: str
    timeframe: str
    period: MCPPeriod
    engine: str
    initial_capital: float


@dataclass
class MCPMetrics:
    total_return_pct: float | None
    sharpe_ratio: float | None
    max_drawdown_pct: float | None
    win_rate_pct: float | None
    num_trades: int | None
    final_capital: float | None


@dataclass
class MCPPayload:
    """Versioned, serialisable context payload for LLM analysis.

    Schema is intentionally flat so any LLM can parse it without
    needing knowledge of BlockBT's internal data structures.
    """

    schema_version: str
    generated_at: str
    context: MCPContext
    metrics: MCPMetrics
    equity_curve_samples: list[dict[str, Any]]
    raw_params: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable dict representation."""
        return {
            "schema_version": self.schema_version,
            "generated_at": self.generated_at,
            "context": asdict(self.context),
            "metrics": asdict(self.metrics),
            "equity_curve_samples": self.equity_curve_samples,
            "raw_params": self.raw_params,
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialise to pretty-printed JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    def to_prompt(self) -> str:
        """Return a human-readable prompt prefix for LLM consumption."""
        m = self.metrics
        c = self.context
        tr = f"{m.total_return_pct:.2f}%" if m.total_return_pct is not None else "N/A"
        dd = f"{m.max_drawdown_pct:.2f}%" if m.max_drawdown_pct is not None else "N/A"
        wr = f"{m.win_rate_pct:.2f}%" if m.win_rate_pct is not None else "N/A"
        fc = f"${m.final_capital:,.2f}" if m.final_capital is not None else "N/A"
        return (
            f"You are a senior quantitative analyst. Analyse the following "
            f"backtesting results and provide a concise, professional report "
            f"covering: performance summary, risk assessment, and actionable "
            f"improvement recommendations.\n\n"
            f"Strategy: {c.strategy_name}\n"
            f"Symbol: {c.symbol} | Timeframe: {c.timeframe}\n"
            f"Period: {c.period.start} \u2192 {c.period.end}\n"
            f"Engine: {c.engine}\n\n"
            f"--- KEY METRICS ---\n"
            f"Total Return:  {tr}\n"
            f"Sharpe Ratio:  {m.sharpe_ratio}\n"
            f"Max Drawdown:  {dd}\n"
            f"Win Rate:      {wr}\n"
            f"Total Trades:  {m.num_trades}\n"
            f"Final Capital: {fc} (started ${c.initial_capital:,.2f})\n\n"
            f"Equity curve data ({len(self.equity_curve_samples)} samples) "
            f"is attached in the JSON payload below.\n\n"
            f"Full JSON payload:\n{self.to_json()}"
        )
