import re
import os

files = {
    "backend/app/api/backtest.py": [
        r'class BacktestRequest\(BaseModel\):[\s\S]*?(?=class BacktestJobResponse|@router)',
        r'class BacktestJobResponse\(BaseModel\):[\s\S]*?(?=@router)'
    ],
    "backend/app/api/strategies.py": [
        r'class StrategyCreate\(BaseModel\):[\s\S]*?(?=class StrategyResponse|@router)',
        r'class StrategyResponse\(BaseModel\):[\s\S]*?(?=@router)'
    ],
    "backend/app/api/results.py": [
        r'class ChatRequest\(BaseModel\):[\s\S]*?(?=class ChatMessageResponse|@router)',
        r'class ChatMessageResponse\(BaseModel\):[\s\S]*?(?=class AIAnalysisResponse|@router)',
        r'class AIAnalysisResponse\(BaseModel\):[\s\S]*?(?=@router)'
    ],
    "backend/app/api/workflows.py": [
        r'class WorkflowNode\(BaseModel\):[\s\S]*?(?=class WorkflowEdge|@router)',
        r'class WorkflowEdge\(BaseModel\):[\s\S]*?(?=class WorkflowCreate|@router)',
        r'class WorkflowCreate\(BaseModel\):[\s\S]*?(?=class WorkflowResponse|@router)',
        r'class WorkflowResponse\(BaseModel\):[\s\S]*?(?=@router)'
    ]
}

for file_path, patterns in files.items():
    with open(file_path, "r") as f:
        content = f.read()
    for pattern in patterns:
        content = re.sub(pattern, '', content)
    with open(file_path, "w") as f:
        f.write(content)
