
from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import select

from app.core.user_scope import get_user_id, scoped_query
from app.db.session import get_session
from app.models.orm import Strategy
from app.schemas.base import ApiResponse
from app.schemas.strategies import StrategyCreate, StrategyResponse

"""
Strategies routes — Phase 2 & 16: SQLite persistence with User Scoping.
"""

router = APIRouter()


@router.get("/", summary="List all strategies", response_model=ApiResponse[list[StrategyResponse]])
def list_strategies(request: Request) -> ApiResponse[list[StrategyResponse]]:
    """Return all strategy records from SQLite (scoped to user when auth is enabled)."""
    with get_session() as db:
        stmt = scoped_query(select(Strategy).order_by(Strategy.created_at.desc()), Strategy, request)
        strategies = db.scalars(stmt).all()
        data = [
            StrategyResponse(
                id=str(s.id),
                name=s.name,
                description=s.description,
                code_content=s.code_content,
                parameters=s.parameters,
                created_at=s.created_at,
            )
            for s in strategies
        ]
        return ApiResponse(success=True, data=data)


@router.get("/{strategy_id}", summary="Get a strategy by ID", response_model=ApiResponse[StrategyResponse])
def get_strategy(strategy_id: int, request: Request) -> ApiResponse[StrategyResponse]:
    """Return a single strategy by primary key."""
    with get_session() as db:
        s = db.get(Strategy, strategy_id)
        if not s:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        user_id = get_user_id(request)
        if user_id is not None and s.user_id is not None and s.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        data = StrategyResponse(
            id=str(s.id),
            name=s.name,
            description=s.description,
            code_content=s.code_content,
            parameters=s.parameters,
            created_at=s.created_at,
        )
        return ApiResponse(success=True, data=data)


@router.post("/", summary="Create a new strategy", status_code=201, response_model=ApiResponse[StrategyResponse])
def create_strategy(payload: StrategyCreate, request: Request) -> ApiResponse[StrategyResponse]:
    """Persist a new strategy to SQLite and return the created record."""
    user_id = get_user_id(request)
    with get_session() as db:
        new_strat = Strategy(
            name=payload.name,
            description=payload.description if payload.description is not None else "",
            code_content=payload.code_content,
            parameters=payload.parameters if payload.parameters is not None else {},
            user_id=user_id,
        )
        db.add(new_strat)
        db.flush()  # get auto-generated id before commit
        
        data = StrategyResponse(
            id=str(new_strat.id),
            name=new_strat.name,
            description=new_strat.description,
            code_content=new_strat.code_content,
            parameters=new_strat.parameters,
            created_at=new_strat.created_at,
        )
    return ApiResponse(success=True, data=data)


@router.put("/{strategy_id}", summary="Update a strategy", response_model=ApiResponse[StrategyResponse])
def update_strategy(strategy_id: int, payload: StrategyCreate, request: Request) -> ApiResponse[StrategyResponse]:
    """Update an existing strategy in SQLite."""
    with get_session() as db:
        s = db.get(Strategy, strategy_id)
        if not s:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        user_id = get_user_id(request)
        if user_id is not None and s.user_id is not None and s.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        s.name = payload.name
        s.description = payload.description if payload.description is not None else s.description
        s.code_content = payload.code_content
        s.parameters = payload.parameters if payload.parameters is not None else s.parameters
        
        db.flush()
        
        data = StrategyResponse(
            id=str(s.id),
            name=s.name,
            description=s.description,
            code_content=s.code_content,
            parameters=s.parameters,
            created_at=s.created_at,
        )
    return ApiResponse(success=True, data=data)


@router.delete("/{strategy_id}", summary="Delete a strategy", response_model=ApiResponse[dict[str, str]])
def delete_strategy(strategy_id: int, request: Request) -> ApiResponse[dict[str, str]]:
    """Remove a strategy record from SQLite."""
    with get_session() as db:
        s = db.get(Strategy, strategy_id)
        if not s:
            raise HTTPException(status_code=404, detail="Strategy not found")
            
        user_id = get_user_id(request)
        if user_id is not None and s.user_id is not None and s.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
            
        db.delete(s)
        return ApiResponse(success=True, data={"id": str(strategy_id)})
