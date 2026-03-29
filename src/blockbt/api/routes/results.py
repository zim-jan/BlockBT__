from typing import Any

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from blockbt.api.dependencies import get_api_key
from blockbt.mcp.llm_client import OllamaClient
from blockbt.mcp.report_builder import ReportBuilder
from blockbt.models.orm import BacktestJob
from blockbt.models.session import get_session

router = APIRouter(dependencies=[Depends(get_api_key)])




class AIAnalysisResponse(BaseModel):
    prompt: str | None
    report: str

@router.get("/{job_id}")
def get_simulation_result(job_id: int) -> dict[str, Any]:
    """Retrieve the status and metrics of a backtest run by its Simulation ID."""
    with get_session() as db:
        job = db.get(BacktestJob, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Simulation Result not found")
            
        return {
            "id": job.id,
            "strategy_id": job.strategy_id,
            "symbol": job.parameters_snapshot.get("symbol", "UNKNOWN"),
            "timeframe": job.parameters_snapshot.get("timeframe", "1d"),
            "status": job.status,
            "metrics": {
                "total_return_pct": job.total_return_pct,
                "sharpe_ratio": job.sharpe_ratio,
                "max_drawdown_pct": job.max_drawdown_pct,
                "win_rate_pct": job.metrics.get("win_rate_pct") if job.metrics else None,
            },
            "ai_analysis_report": job.ai_analysis_report,
            "error_log": job.error_message,
        }

@router.post("/{job_id}/analyze", response_model=AIAnalysisResponse)
def analyze_simulation_result(job_id: int) -> AIAnalysisResponse:
    """Generate an AI analysis report for a completed simulation."""
    with get_session() as db:
        job = db.get(BacktestJob, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Simulation Result not found")

        if job.status.upper() != "COMPLETED":
            raise HTTPException(
                status_code=400, detail="Cannot analyze a simulation that is not completed."
            )

        if job.ai_analysis_report:
            return AIAnalysisResponse(prompt=None, report=job.ai_analysis_report)

        result = job.metrics or {}
        result["symbol"] = job.parameters_snapshot.get("symbol", "UNKNOWN")
        result["timeframe"] = job.parameters_snapshot.get("timeframe", "1d")
        result["engine_name"] = job.parameters_snapshot.get("engine_name", "opensource")
        result["initial_capital"] = job.parameters_snapshot.get("initial_capital", 10000.0)
        result["total_return_pct"] = job.total_return_pct
        result["sharpe_ratio"] = job.sharpe_ratio
        result["max_drawdown_pct"] = job.max_drawdown_pct
        result["win_rate_pct"] = result.get("win_rate_pct")
        result["num_trades"] = job.num_trades
        result["final_capital"] = job.final_capital

        # Build equity curve if available in metrics
        if "equity_curve" not in result and "equity_curve_json" in result:
            curve = result["equity_curve_json"]
            dates = [x["date"] for x in curve]
            values = [x["value"] for x in curve]
            if dates:
                result["equity_curve"] = pd.Series(values, index=pd.to_datetime(dates))

        strategy_name = job.strategy.name if job.strategy else "Unknown Strategy"
        raw_params = job.parameters_snapshot

        payload = ReportBuilder.build(
            result=result,
            strategy_name=strategy_name,
            raw_params=raw_params
        )
        prompt = payload.to_prompt()
        job.ai_analysis_report = OllamaClient().generate_report(prompt)
        db.commit()
        return AIAnalysisResponse(prompt=prompt, report=job.ai_analysis_report)
