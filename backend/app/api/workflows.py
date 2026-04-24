import uuid
from datetime import UTC
from typing import Any

from fastapi import APIRouter

from app.schemas.workflows import WorkflowCreate

"""
Workflows routes — Phase 1 MVP (mock, in-memory store).

Workflows represent React Flow graph definitions saved by the frontend.
"""


router = APIRouter()

# ---------------------------------------------------------------------------
# In-memory store (Phase 1 MVP — will migrate to SQLite in Phase 4)
# ---------------------------------------------------------------------------
_WORKFLOWS: list[dict] = []

# ---------------------------------------------------------------------------
# Pydantic schemas
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
    from datetime import datetime

    now = datetime.now(UTC).isoformat()
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
