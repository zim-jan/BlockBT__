with open("backend/app/main.py", "r") as f:
    content = f.read()

# Fix import routes
content = content.replace("from app.api.routes import backtest, results, strategies, workflows", "from app.api import backtest, results, strategies, workflows")

with open("backend/app/main.py", "w") as f:
    f.write(content)
