from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str

class ChatMessageResponse(BaseModel):
    role: str
    content: str
    timestamp: str

class AIAnalysisResponse(BaseModel):
    prompt: str | None = None
    report: str
