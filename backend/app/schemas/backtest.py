from datetime import datetime
from typing import Any

from pydantic import BaseModel


class BacktestRequest(BaseModel):
    strategy_id: int
    symbol: str | list[str]
    data_source: str = "synthetic"
    timeframe: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    initial_capital: float = 10000.0
    sma_fast: int | None = None
    sma_slow: int | None = None
    strategy_type: str | None = None
    macd_fast: int | None = None
    macd_slow: int | None = None
    macd_signal: int | None = None
    parameters: dict[str, Any] | None = None


class BacktestJobResponse(BaseModel):
    id: int
    job_id: int
    strategy_id: int
    status: str
    symbol: str
    timeframe: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    initial_capital: float
    created_at: datetime
    metrics: dict[str, Any] | None = None
    parameters: dict[str, Any] | None = None
    total_return_pct: float | None = None
    sharpe_ratio: float | None = None
    max_drawdown_pct: float | None = None
    num_trades: int | None = None
    final_capital: float | None = None
    equity_curve: list[dict[str, Any]] | None = None
    error_message: str | None = None
