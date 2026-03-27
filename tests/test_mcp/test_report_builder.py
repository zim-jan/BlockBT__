"""
Tests for the MCP ReportBuilder and MCPPayload.
"""

from __future__ import annotations

import json
from typing import Any

import pandas as pd

from blockbt.mcp.protocol import MCPPayload
from blockbt.mcp.report_builder import ReportBuilder


def _make_result(n: int = 100) -> dict[str, Any]:
    import numpy as np

    dates = pd.date_range("2022-01-01", periods=n, freq="D")
    equity = pd.Series(
        10_000 * (1 + np.random.default_rng(7).normal(0.001, 0.01, n)).cumprod(),
        index=dates,
    )
    return dict(
        symbol="AAPL",
        timeframe="1d",
        engine_name="opensource",
        total_return_pct=12.34,
        sharpe_ratio=1.42,
        max_drawdown_pct=8.75,
        win_rate_pct=55.0,
        num_trades=23,
        initial_capital=10_000.0,
        final_capital=11_234.0,
        equity_curve=equity,
        raw={},
    )


class TestReportBuilder:
    def test_builds_payload(self):
        result = _make_result()
        payload = ReportBuilder.build(result, strategy_name="SMA Cross")
        assert isinstance(payload, MCPPayload)
        assert payload.context.symbol == "AAPL"
        assert payload.metrics.total_return_pct == 12.34

    def test_equity_curve_downsampled(self):
        result = _make_result(n=1000)
        payload = ReportBuilder.build(result, max_equity_points=200)
        assert len(payload.equity_curve_samples) <= 200

    def test_to_json_is_valid(self):
        result = _make_result()
        payload = ReportBuilder.build(result)
        json_str = payload.to_json()
        parsed = json.loads(json_str)
        assert "metrics" in parsed
        assert "context" in parsed

    def test_to_prompt_contains_key_info(self):
        result = _make_result()
        payload = ReportBuilder.build(result, strategy_name="My Strategy")
        prompt = payload.to_prompt()
        assert "AAPL" in prompt
        assert "12.34" in prompt
        assert "My Strategy" in prompt

    def test_period_extracted_from_equity_curve(self):
        result = _make_result(n=50)
        payload = ReportBuilder.build(result)
        assert payload.context.period.start == "2022-01-01"
        assert payload.context.period.end != "unknown"
