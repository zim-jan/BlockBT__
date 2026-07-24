from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NoteBase(BaseModel):
    content: str
    is_pinned: bool = False


class NoteCreate(NoteBase):
    pass


class NoteUpdate(BaseModel):
    content: str | None = None
    is_pinned: bool | None = None


class NoteResponse(NoteBase):
    id: int
    strategy_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
