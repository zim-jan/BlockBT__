import re
with open("backend/app/api/results.py", "r") as f:
    content = f.read()

# Remove old models
content = re.sub(r'class ChatRequest\(BaseModel\):\n\s+message: str\n\n', '', content)
content = re.sub(r'class ChatMessageResponse\(BaseModel\):\n\s+role: str\n\s+content: str\n\s+timestamp: str\n\n', '', content)
content = re.sub(r'class AIAnalysisResponse\(BaseModel\):\n\s+summary: str\n\s+strengths: list\[str\]\n\s+weaknesses: list\[str\]\n\s+recommendations: list\[str\]\n\n', '', content)

# Add import
import_stmt = "from app.schemas.results import ChatRequest, ChatMessageResponse, AIAnalysisResponse\n"
content = import_stmt + content

with open("backend/app/api/results.py", "w") as f:
    f.write(content)
