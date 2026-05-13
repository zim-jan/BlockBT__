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


class DataIngestionNode(BaseNode):
    category: Literal["DataIngestion"] = "DataIngestion"
    params: DataIngestionParams


class IndicatorsParams(BaseModel):
    windows: list[int] = Field(default_factory=lambda: [14])


class IndicatorsNode(BaseNode):
    category: Literal["Indicators"] = "Indicators"
    params: IndicatorsParams = Field(default_factory=IndicatorsParams)


class LogicOperatorsParams(BaseModel):
    condition: str


class LogicOperatorsNode(BaseNode):
    category: Literal["LogicOperators"] = "LogicOperators"
    params: LogicOperatorsParams


class ExecutionParams(BaseModel):
    init_cash: float = 10000.0


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
