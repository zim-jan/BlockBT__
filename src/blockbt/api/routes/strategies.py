"""
Strategies routes — Phase 2: SQLite persistence via SQLAlchemy.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from blockbt.models.orm import Strategy
from blockbt.models.session import get_session

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class StrategyCreate(BaseModel):
    name: str
    description: str = ""
    parameters: dict[str, Any] = {}


class StrategyResponse(BaseModel):
    id: int
    name: str
    description: str
    parameters: dict[str, Any]
    created_at: str


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _strategy_to_dict(s: Strategy) -> dict[str, Any]:
    return {
        "id": s.id,
        "name": s.name,
        "description": s.description,
        "parameters": s.parameters,
        "created_at": s.created_at.isoformat() if s.created_at else None,
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/", summary="List all strategies")
def list_strategies() -> dict[str, Any]:
    """Return all strategy records from SQLite."""
    with get_session() as db:
        strategies = db.query(Strategy).order_by(Strategy.created_at.desc()).all()
        return {
            "success": True,
            "data": [_strategy_to_dict(s) for s in strategies],
            "error": None,
        }


@router.get("/{strategy_id}", summary="Get a strategy by ID")
def get_strategy(strategy_id: int) -> dict[str, Any]:
    """Return a single strategy by primary key."""
    with get_session() as db:
        s = db.get(Strategy, strategy_id)
        if not s:
            raise HTTPException(status_code=404, detail="Strategy not found")
        return {"success": True, "data": _strategy_to_dict(s), "error": None}


@router.post("/", summary="Create a new strategy", status_code=201)
def create_strategy(payload: StrategyCreate) -> dict[str, Any]:
    """Persist a new strategy to SQLite and return the created record."""
    with get_session() as db:
        new_strat = Strategy(
            name=payload.name,
            description=payload.description,
            parameters=payload.parameters,
        )
        db.add(new_strat)
        db.flush()  # get auto-generated id before commit
        result = _strategy_to_dict(new_strat)
    return {"success": True, "data": result, "error": None}
