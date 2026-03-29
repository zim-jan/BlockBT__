import re
with open("backend/app/api/workflows.py", "r") as f:
    content = f.read()

# Remove old models
content = re.sub(r'class WorkflowNode\(BaseModel\):\n\s+id: str\n\s+type: str\n\s+position: dict\[str, float\]\n\s+data: dict\[str, Any\]\n\n', '', content)
content = re.sub(r'class WorkflowEdge\(BaseModel\):\n\s+id: str\n\s+source: str\n\s+target: str\n\n', '', content)
content = re.sub(r'class WorkflowCreate\(BaseModel\):\n\s+name: str\n\s+description: str \| None = None\n\s+nodes: list\[WorkflowNode\]\n\s+edges: list\[WorkflowEdge\]\n\n', '', content)
content = re.sub(r'class WorkflowResponse\(BaseModel\):\n\s+id: str\n\s+name: str\n\s+description: str \| None = None\n\s+nodes: list\[WorkflowNode\]\n\s+edges: list\[WorkflowEdge\]\n\s+created_at: datetime\n\s+updated_at: datetime\n\n', '', content)

# Add import
import_stmt = "from app.schemas.workflows import WorkflowNode, WorkflowEdge, WorkflowCreate, WorkflowResponse\n"
content = import_stmt + content

with open("backend/app/api/workflows.py", "w") as f:
    f.write(content)
