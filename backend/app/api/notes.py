from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import select

from app.core.user_scope import get_user_id, scoped_query, verify_resource_access
from app.db.session import get_session
from app.models.orm import Note, Strategy
from app.schemas.base import ApiResponse
from app.schemas.notes import NoteCreate, NoteResponse, NoteUpdate

router = APIRouter()


@router.get("/strategy/{strategy_id}", summary="List notes for a strategy", response_model=ApiResponse[list[NoteResponse]])
def get_notes_for_strategy(strategy_id: int, request: Request) -> ApiResponse[list[NoteResponse]]:
    """Return all notes for a specific strategy, ordered by pinned first, then by creation date."""
    with get_session() as db:
        # Verify strategy exists and user has access
        strategy = db.get(Strategy, strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")
            
        verify_resource_access(strategy, request)

        stmt = (
            select(Note)
            .where(Note.strategy_id == strategy_id)
            .order_by(Note.is_pinned.desc(), Note.created_at.desc())
        )
        # Note: scoped_query is not strictly needed here since we filter by strategy_id 
        # and we verified the strategy, but it's good practice.
        stmt = scoped_query(stmt, Note, request)
        notes = db.scalars(stmt).all()
        
        data = [
            NoteResponse(
                id=n.id,
                strategy_id=n.strategy_id,
                content=n.content,
                is_pinned=n.is_pinned,
                created_at=n.created_at,
                updated_at=n.updated_at,
            )
            for n in notes
        ]
        return ApiResponse(success=True, data=data)


@router.post("/strategy/{strategy_id}", summary="Create a note", status_code=201, response_model=ApiResponse[NoteResponse])
def create_note(strategy_id: int, payload: NoteCreate, request: Request) -> ApiResponse[NoteResponse]:
    """Create a new note attached to a strategy."""
    with get_session() as db:
        strategy = db.get(Strategy, strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail="Strategy not found")
            
        verify_resource_access(strategy, request)

        user_id = get_user_id(request)
        new_note = Note(
            strategy_id=strategy_id,
            user_id=user_id,
            content=payload.content,
            is_pinned=payload.is_pinned,
        )
        db.add(new_note)
        db.flush()
        
        data = NoteResponse(
            id=new_note.id,
            strategy_id=new_note.strategy_id,
            content=new_note.content,
            is_pinned=new_note.is_pinned,
            created_at=new_note.created_at,
            updated_at=new_note.updated_at,
        )
        db.commit()
    return ApiResponse(success=True, data=data)


@router.put("/{note_id}", summary="Update a note", response_model=ApiResponse[NoteResponse])
def update_note(note_id: int, payload: NoteUpdate, request: Request) -> ApiResponse[NoteResponse]:
    """Update content or pin status of a note."""
    with get_session() as db:
        note = db.get(Note, note_id)
        if not note:
            raise HTTPException(status_code=404, detail="Note not found")
            
        user_id = get_user_id(request)
        if user_id is not None and note.user_id is not None and note.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
            
        if payload.content is not None:
            note.content = payload.content
        if payload.is_pinned is not None:
            note.is_pinned = payload.is_pinned
            
        db.flush()
        
        data = NoteResponse(
            id=note.id,
            strategy_id=note.strategy_id,
            content=note.content,
            is_pinned=note.is_pinned,
            created_at=note.created_at,
            updated_at=note.updated_at,
        )
        db.commit()
    return ApiResponse(success=True, data=data)


@router.delete("/{note_id}", summary="Delete a note", response_model=ApiResponse[dict[str, str]])
def delete_note(note_id: int, request: Request) -> ApiResponse[dict[str, str]]:
    """Remove a note."""
    with get_session() as db:
        note = db.get(Note, note_id)
        if not note:
            raise HTTPException(status_code=404, detail="Note not found")
            
        user_id = get_user_id(request)
        if user_id is not None and note.user_id is not None and note.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
            
        db.delete(note)
        db.commit()
        return ApiResponse(success=True, data={"id": str(note_id)})
