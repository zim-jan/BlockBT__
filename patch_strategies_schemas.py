import re
with open("backend/app/api/strategies.py", "r") as f:
    content = f.read()

# Remove old models
content = re.sub(r'class StrategyCreate\(BaseModel\):\n\s+name: str\n\s+description: str \| None = None\n\s+parameters_schema: dict\[str, Any\] \| None = None\n\s+code_content: str\n\n', '', content)
content = re.sub(r'class StrategyResponse\(BaseModel\):\n\s+id: str\n\s+name: str\n\s+description: str \| None = None\n\s+parameters_schema: dict\[str, Any\] \| None = None\n\s+created_at: datetime\n\s+updated_at: datetime\n\n', '', content)

# Add import
import_stmt = "from app.schemas.strategies import StrategyCreate, StrategyResponse\n"
content = import_stmt + content

with open("backend/app/api/strategies.py", "w") as f:
    f.write(content)
