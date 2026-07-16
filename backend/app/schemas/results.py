import datetime

from pydantic import BaseModel


class ChatRequest(BaseModel):
    content: str


class ChatMessageResponse(BaseModel):
    id: int
    job_id: int
    role: str
    content: str
    created_at: datetime.datetime


class AIAnalysisResponse(BaseModel):
    prompt: str | None = None
    report: str
