from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ParameterBounds(BaseModel):
    min: float | int
    max: float | int
    step: float | int | None = None
    type: str = "int"  # "int" or "float" or "categorical"
    choices: list[Any] | None = None


class OptimizationRequest(BaseModel):
    strategy_id: int
    symbol: str
    data_source: str = "yahoo"
    timeframe: str = "1d"
    start_date: str | None = None
    end_date: str | None = None
    initial_capital: float = 10000.0
    
    # Optimization specific
    metric: str = "Total Return [%]"
    n_trials: int = 20
    param_bounds: dict[str, ParameterBounds]
    
    parameters: dict[str, Any] | None = None


class WalkForwardRequest(BaseModel):
    strategy_id: int
    symbol: str
    data_source: str = "yahoo"
    timeframe: str = "1d"
    start_date: str | None = None
    end_date: str | None = None
    initial_capital: float = 10000.0
    
    window_size: str = "365d"
    step_size: str = "90d"
    parameters: dict[str, Any] | None = None


class OptimizationJobResponse(BaseModel):
    id: int
    job_id: int
    strategy_id: int
    status: str
    symbol: str
    initial_capital: float
    created_at: datetime
    
    best_parameters: dict[str, Any] | None = None
    best_value: float | None = None
    trials_data: dict[str, Any] | None = None
    
    error_message: str | None = None
    completed_at: datetime | None = None
