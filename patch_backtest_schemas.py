import re
with open("backend/app/api/backtest.py", "r") as f:
    content = f.read()

# Remove old models
content = re.sub(r'class BacktestRequest\(BaseModel\):\n\s+strategy_id: str\n\s+symbol: str\n\s+timeframe: str\n\s+start_date: str\n\s+end_date: str\n\s+initial_capital: float = 10000\.0\n\s+parameters: dict\[str, Any\] \| None = None\n\n', '', content)
content = re.sub(r'class BacktestJobResponse\(BaseModel\):\n\s+id: str\n\s+strategy_id: str\n\s+status: str\n\s+symbol: str\n\s+timeframe: str\n\s+start_date: str\n\s+end_date: str\n\s+initial_capital: float\n\s+created_at: datetime\n\s+updated_at: datetime\n\s+metrics: dict\[str, Any\] \| None = None\n\s+parameters: dict\[str, Any\] \| None = None\n\s+error_message: str \| None = None\n\n', '', content)

# Add import
import_stmt = "from app.schemas.backtest import BacktestRequest, BacktestJobResponse\n"
content = import_stmt + content

with open("backend/app/api/backtest.py", "w") as f:
    f.write(content)
