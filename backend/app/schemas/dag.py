from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field


class BaseNode(BaseModel):
    id: str
    type: str
    category: str
    position: dict[str, float] = Field(default_factory=lambda: {"x": 0.0, "y": 0.0})


class DataIngestionParams(BaseModel):
    symbol: str
    timeframe: str
    # Prewencja Survivorship Bias
    point_in_time_enforcement: bool = Field(default=True, description="Wymusza dane Point-in-Time")
    dataSource: str | None = None
    startDate: str | None = None
    endDate: str | None = None


class DataIngestionNode(BaseNode):
    category: Literal["DataIngestion"] = "DataIngestion"
    params: DataIngestionParams


class IndicatorsParams(BaseModel):
    indicatorType: str = "sma_crossover"
    smaFast: int | None = None
    smaSlow: int | None = None
    initialCapital: float | None = None
    macdFast: int | None = None
    macdSlow: int | None = None
    macdSignal: int | None = None
    codeContent: str | None = None
    windows: list[int] = Field(default_factory=lambda: [14])


class IndicatorsNode(BaseNode):
    category: Literal["Indicators"] = "Indicators"
    params: IndicatorsParams = Field(default_factory=IndicatorsParams)


class LogicOperatorsParams(BaseModel):
    signalType: str
    # Rozszerzenie dla TimeShift, TypingCast i CrossValidation
    operator_type: Literal["crossover", "crossunder", "time_shift", "typing_cast", "cross_validation"] = "crossover"
    shift_periods: int = Field(default=1, ge=1, description="Dla TimeShiftNode")
    cast_type: str = Field(default="float64", description="Dla TypingCastNode")

class LogicOperatorsNode(BaseNode):
    category: Literal["LogicOperators"] = "LogicOperators"
    params: LogicOperatorsParams


class ExecutionParams(BaseModel):
    initialCapital: float = 10000.0
    init_cash: float = 10000.0
    fees: float = Field(..., gt=0.0, description="Prowizja transakcyjna")
    slippage: float = Field(..., gt=0.0, description="Poślizg cenowy")


class ExecutionNode(BaseNode):
    category: Literal["Execution"] = "Execution"
    params: ExecutionParams = Field(default_factory=ExecutionParams)


class MetaNode(BaseNode):
    category: Literal["Meta"] = "Meta"
    target_nodes: list[str]
    params: dict[str, Any] = Field(default_factory=dict)


AnyNode = Annotated[
    DataIngestionNode | IndicatorsNode | LogicOperatorsNode | ExecutionNode | MetaNode,
    Field(discriminator="category")
]


class DAGEdge(BaseModel):
    id: str
    source: str
    target: str
    sourceHandle: str | None = None
    targetHandle: str | None = None


class DAGGraph(BaseModel):
    nodes: list[AnyNode]
    edges: list[DAGEdge]
    meta_nodes: list[MetaNode] = Field(default_factory=list)


# Temporary compatibility schemas to replace `workflows.py` logic
class WorkflowCreate(BaseModel):
    name: str
    description: str | None = None
    nodes: list[AnyNode]
    edges: list[DAGEdge]
    meta_nodes: list[MetaNode] = Field(default_factory=list)


class WorkflowResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    nodes: list[AnyNode]
    edges: list[DAGEdge]
    meta_nodes: list[MetaNode] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
