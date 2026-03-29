from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str

class ChatMessageResponse(BaseModel):
    role: str
    content: str
    timestamp: str

class AIAnalysisResponse(BaseModel):
    summary: str
    strengths: list[str]
    weaknesses: list[str]
    recommendations: list[str]
