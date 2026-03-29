"""
Workflows routes — Phase 1 MVP (mock, in-memory store).

Workflows represent React Flow graph definitions saved by the frontend.
"""

import uuid
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class WorkflowNode(BaseModel):
    id: str
    type: str
    position: dict[str, float]
    data: dict[str, Any] = {}


class WorkflowEdge(BaseModel):
    id: str
    source: str
    target: str
    type: str = "default"


class WorkflowCreate(BaseModel):
    name: str
    description: str = ""
    nodes: list[WorkflowNode] = []
    edges: list[WorkflowEdge] = []


class WorkflowResponse(BaseModel):
    id: str
    name: str
    description: str
    nodes: list[WorkflowNode]
    edges: list[WorkflowEdge]
    created_at: str
    updated_at: str


# ---------------------------------------------------------------------------
# In-memory store (mock)
# ---------------------------------------------------------------------------
_WORKFLOWS: list[dict[str, Any]] = [
    {
        "id": "mock-wf-001",
        "name": "SMA Crossover Flow (Demo)",
        "description": "Example React Flow workflow for SMA crossover strategy.",
        "nodes": [
            {"id": "node-1", "type": "dataSource", "position": {"x": 50, "y": 100}, "data": {"label": "Data Source", "symbol": "AAPL"}},
            {"id": "node-2", "type": "indicator", "position": {"x": 300, "y": 100}, "data": {"label": "SMA Fast", "period": 10}},
            {"id": "node-3", "type": "indicator", "position": {"x": 300, "y": 250}, "data": {"label": "SMA Slow", "period": 30}},
            {"id": "node-4", "type": "signal", "position": {"x": 550, "y": 175}, "data": {"label": "Crossover Signal"}},
            {"id": "node-5", "type": "output", "position": {"x": 800, "y": 175}, "data": {"label": "Backtest Result"}},
        ],
        "edges": [
            {"id": "e1-2", "source": "node-1", "target": "node-2", "type": "default"},
            {"id": "e1-3", "source": "node-1", "target": "node-3", "type": "default"},
            {"id": "e2-4", "source": "node-2", "target": "node-4", "type": "default"},
            {"id": "e3-4", "source": "node-3", "target": "node-4", "type": "default"},
            {"id": "e4-5", "source": "node-4", "target": "node-5", "type": "default"},
        ],
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
    }
]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/", response_model=dict)
def list_workflows() -> dict[str, Any]:
    """Return all saved workflow definitions."""
    return {"success": True, "data": _WORKFLOWS, "error": None}


@router.get("/{workflow_id}", response_model=dict)
def get_workflow(workflow_id: str) -> dict[str, Any]:
    """Return a single workflow by ID."""
    for wf in _WORKFLOWS:
        if wf["id"] == workflow_id:
            return {"success": True, "data": wf, "error": None}
    return {"success": False, "data": None, "error": "Workflow not found"}


@router.post("/", response_model=dict, status_code=201)
def save_workflow(payload: WorkflowCreate) -> dict[str, Any]:
    """Save a new React Flow workflow definition."""
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).isoformat()
    new_wf: dict[str, Any] = {
        "id": str(uuid.uuid4()),
        "name": payload.name,
        "description": payload.description,
        "nodes": [n.model_dump() for n in payload.nodes],
        "edges": [e.model_dump() for e in payload.edges],
        "created_at": now,
        "updated_at": now,
    }
    _WORKFLOWS.append(new_wf)
    return {"success": True, "data": new_wf, "error": None}
