--- src/blockbt/api/main.py
+++ src/blockbt/api/main.py
@@ -10,7 +10,7 @@
 from fastapi.middleware.cors import CORSMiddleware
 from loguru import logger

-from blockbt.api.routes import backtest, strategies, workflows
+from blockbt.api.routes import backtest, strategies, workflows, results
 from blockbt.models.session import init_db

 # ---------------------------------------------------------------------------
@@ -49,6 +49,7 @@
 app.include_router(strategies.router, prefix="/api/strategies", tags=["Strategies"])
 app.include_router(backtest.router, prefix="/api/backtest", tags=["Backtest"])
 app.include_router(workflows.router, prefix="/api/workflows", tags=["Workflows"])
+app.include_router(results.router, prefix="/api/results", tags=["Results"])


 # ---------------------------------------------------------------------------
