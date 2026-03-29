from datetime import datetime
from typing import Any

from pydantic import BaseModel


class BacktestRequest(BaseModel):
    strategy_id: str
    symbol: str
    timeframe: str
    start_date: str
    end_date: str
    initial_capital: float = 10000.0
    parameters: dict[str, Any] | None = None

class BacktestJobResponse(BaseModel):
    id: str
    strategy_id: str
    status: str
    symbol: str
    timeframe: str
    start_date: str
    end_date: str
    initial_capital: float
    created_at: datetime
    updated_at: datetime
    metrics: dict[str, Any] | None = None
    parameters: dict[str, Any] | None = None
    error_message: str | None = None
