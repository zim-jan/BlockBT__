from fastapi import APIRouter, Depends, HTTPException
from typing import Any

from blockbt.db.session import get_session
from blockbt.db.models import SimulationResult
from blockbt.api.dependencies import get_api_key

router = APIRouter(dependencies=[Depends(get_api_key)])

@router.get("/{sim_id}")
def get_simulation_result(sim_id: int) -> dict[str, Any]:
    """Retrieve the status and metrics of a backtest run by its Simulation ID."""
    with get_session() as db:
        sim = db.get(SimulationResult, sim_id)
        if not sim:
            raise HTTPException(status_code=404, detail="Simulation Result not found")
            
        return {
            "id": sim.id,
            "strategy_template_id": sim.strategy_template_id,
            "symbol": sim.symbol,
            "timeframe": sim.timeframe,
            "status": sim.status,
            "engine_used": sim.engine_used,
            "metrics": {
                "total_return_pct": sim.total_return_pct,
                "sharpe_ratio": sim.sharpe_ratio,
                "max_drawdown_pct": sim.max_drawdown_pct,
                "win_rate_pct": sim.win_rate_pct,
            },
            "ai_analysis_report": sim.ai_analysis_report,
            "error_log": sim.error_log,
        }
