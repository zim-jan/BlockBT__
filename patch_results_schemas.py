import sys
import re

filename = "src/blockbt/api/routes/results.py"
with open(filename, "r") as f:
    content = f.read()

new_schemas = """
import datetime

class ChatRequest(BaseModel):
    content: str

class ChatMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime.datetime

class AIAnalysisResponse(BaseModel):
"""

content = content.replace("class AIAnalysisResponse(BaseModel):", new_schemas)

with open(filename, "w") as f:
    f.write(content)

print("Added schemas to results.py")
