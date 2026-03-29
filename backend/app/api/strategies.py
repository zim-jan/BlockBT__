from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app.db.session import get_session
from app.models.orm import Strategy
from app.schemas.strategies import StrategyCreate

"""
Strategies routes — Phase 2: SQLite persistence via SQLAlchemy.
"""

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _strategy_to_dict(strategy: Strategy) -> dict[str, Any]:
    """Convert Strategy ORM model to dictionary."""
    return {
        "id": str(strategy.id),
        "name": strategy.name,
        "description": strategy.description,
        "parameters": strategy.parameters,
        "created_at": strategy.created_at,
    }

# ---------------------------------------------------------------------------
# Pydantic schemas
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
            parameters=payload.parameters if payload.parameters is not None else {},
        )
        db.add(new_strat)
        db.flush()  # get auto-generated id before commit
        result = _strategy_to_dict(new_strat)
    return {"success": True, "data": result, "error": None}
