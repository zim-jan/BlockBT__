from datetime import datetime
from typing import Any

from pydantic import BaseModel


class WorkflowNode(BaseModel):
    id: str
    type: str
    position: dict[str, float]
    data: dict[str, Any]


class WorkflowEdge(BaseModel):
    id: str
    source: str
    target: str


class WorkflowCreate(BaseModel):
    name: str
    description: str | None = None
    nodes: list[WorkflowNode]
    edges: list[WorkflowEdge]


class WorkflowResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    nodes: list[WorkflowNode]
    edges: list[WorkflowEdge]
    created_at: datetime
    updated_at: datetime
