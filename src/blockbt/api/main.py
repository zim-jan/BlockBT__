"""
BlockBT FastAPI Entrypoint.
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from blockbt.api.routes import strategies, results

app = FastAPI(
    title="BlockBT REST API",
    description="Synchronous/Asynchronous Quant Backtesting API",
    version="1.0.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(strategies.router, prefix="/api/v1/strategies", tags=["Strategies"])
app.include_router(results.router, prefix="/api/v1/results", tags=["Results"])

@app.get("/api/v1/health")
def health_check():
    return {"status": "ok"}

# For direct execution
if __name__ == "__main__":
    uvicorn.run("blockbt.api.main:app", host="127.0.0.1", port=8000, reload=True)
