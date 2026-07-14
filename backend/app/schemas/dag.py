from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field


class BaseNode(BaseModel):
    id: str
    type: str
    category: str
    position: dict[str, float] = Field(default_factory=lambda: {"x": 0.0, "y": 0.0})


class DataIngestionParams(BaseModel):
    # Faza 10: pojedynczy ticker (str) lub lista tickerów do wektoryzacji broadcastingiem.
    symbol: str | list[str]
    timeframe: str
    dataSource: str | None = None
    startDate: str | None = None
    endDate: str | None = None
    point_in_time_enforcement: bool = True


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
    signalType: str | None = None  # Only used by SignalNode, not TimeShiftNode
    operator_type: Literal["crossover", "crossunder", "time_shift", "typing_cast", "cross_validation"] = "time_shift"
    shift_periods: int = 1
    cast_type: str = "float64"

class LogicOperatorsNode(BaseNode):
    category: Literal["LogicOperators"] = "LogicOperators"
    params: LogicOperatorsParams


class ExecutionParams(BaseModel):
    initialCapital: float = 10000.0
    init_cash: float = 10000.0
    fees: float = Field(default=0.001, gt=0.0)
    slippage: float = Field(default=0.001, gt=0.0)
    # Faza 12: zarządzanie ryzykiem (stop-loss / take-profit / trailing) i sizing pozycji.
    sl_stop: float | None = Field(default=None, ge=0.0, le=1.0)
    tp_stop: float | None = Field(default=None, ge=0.0, le=1.0)
    sl_trail: bool = False
    size: float | None = Field(default=None, gt=0.0)
    # Whitelist typów sizingu vectorbt: amount | value | percent.
    size_type: Literal["amount", "value", "percent"] = "amount"


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
