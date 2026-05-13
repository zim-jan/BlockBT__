import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter

from app.schemas.base import ApiResponse
from app.schemas.workflows import WorkflowCreate

router = APIRouter()

# ---------------------------------------------------------------------------
# In-memory store (Phase 1 MVP — will migrate to SQLite in Phase 4)
# ---------------------------------------------------------------------------
_WORKFLOWS: list[dict] = []

# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


@router.get("/", response_model=ApiResponse[list[dict]])
def list_workflows() -> ApiResponse[list[dict]]:
    """Return all saved workflow definitions."""
    return ApiResponse(success=True, data=_WORKFLOWS)


@router.get("/{workflow_id}", response_model=ApiResponse[dict])
def get_workflow(workflow_id: str) -> ApiResponse[dict]:
    """Return a single workflow by ID."""
    for wf in _WORKFLOWS:
        if wf["id"] == workflow_id:
            return ApiResponse(success=True, data=wf)
    return ApiResponse(success=False, error="Workflow not found")


@router.post("/", response_model=ApiResponse[dict], status_code=201)
def save_workflow(payload: WorkflowCreate) -> ApiResponse[dict]:
    """Save a new React Flow workflow definition."""
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
    return ApiResponse(success=True, data=new_wf)
