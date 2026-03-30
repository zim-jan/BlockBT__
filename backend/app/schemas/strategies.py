from datetime import datetime
from typing import Any

from pydantic import BaseModel


class StrategyCreate(BaseModel):
    name: str
    description: str | None = None
    parameters: dict[str, Any] | None = None
    code_content: str = ""

class StrategyResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    parameters: dict[str, Any] | None = None
    created_at: datetime
