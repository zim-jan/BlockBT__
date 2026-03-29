import re

with open("backend/app/schemas/results.py", "r") as f:
    content = f.read()

pattern = r"class AIAnalysisResponse\(BaseModel\):\n    summary: str\n    strengths: list\[str\]\n    weaknesses: list\[str\]\n    recommendations: list\[str\]\n"
replacement = "class AIAnalysisResponse(BaseModel):\n    prompt: str | None = None\n    report: str\n"

content = re.sub(pattern, replacement, content)

with open("backend/app/schemas/results.py", "w") as f:
    f.write(content)
