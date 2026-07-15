import datetime
from typing import Literal

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


class TearsheetResponse(BaseModel):
    """Faza 13: odpowiedź z wygenerowanym tearsheetem HTML dla danego joba."""

    job_id: int
    html: str
    format: Literal["html"] = "html"
    generated_at: datetime.datetime
