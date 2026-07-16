import datetime
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from blockbt.api.dependencies import get_api_key
from blockbt.connectors.registry import ConnectorRegistry
from blockbt.db.models import SimulationResult, StrategyTemplate
from blockbt.db.session import get_session
from blockbt.engine.loader import EngineLoader

router = APIRouter(dependencies=[Depends(get_api_key)])

@router.get("/")
def list_strategies() -> dict[str, Any]:
    """Retrieve all available Strategy Templates."""
    with get_session() as db:
        templates = db.query(StrategyTemplate).all()
        return {
            "count": len(templates),
            "strategies": [
                {
                    "id": t.id,
                    "name": t.name,
                    "engine_type": t.engine_type,
                    "created_at": t.created_at.isoformat(),
                } for t in templates
            ]
        }

@router.get("/{strategy_id}")
def get_strategy(strategy_id: int) -> dict[str, Any]:
    """Retrieve a specific Strategy Template by ID."""
    with get_session() as db:
        template = db.get(StrategyTemplate, strategy_id)
        if not template:
            raise HTTPException(status_code=404, detail="Strategy not found")
        return {
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "wizard_state": template.wizard_state,
        }

def run_backtest_task(sim_id: int, template_id: int):
    """Background task to run the engine and persist results."""
    with get_session() as db:
        sim = db.get(SimulationResult, sim_id)
        template = db.get(StrategyTemplate, template_id)
        
        if not sim or not template:
            return
        
        try:
            sim.status = "running"
            db.commit()
            
            ws = template.wizard_state
            
            # Fetch data
            connector = ConnectorRegistry.get(ws.get("connector", "yahoo"))
            ohlcv = connector.fetch(
                symbol=ws["symbol"],
                start=ws["start_date"],
                end=ws["end_date"],
                timeframe=ws.get("timeframe", "1d"),
            )
            
            # Run engine
            engine = EngineLoader.load()
            params = {
                "initial_capital": float(ws.get("initial_capital", 10000)),
                "sma_fast": int(ws.get("sma_fast", 10)),
                "sma_slow": int(ws.get("sma_slow", 30)),
            }
            # Catch advanced params
            if "strategy_type" in ws:
                params["strategy_type"] = ws["strategy_type"]
            for key in ["macd_fast", "macd_slow", "macd_signal"]:
                if key in ws:
                    params[key] = int(ws[key])
            
            result = engine.run_backtest(ohlcv, params)
            
            # Save results
            sim.engine_used = result.get("engine_name", "opensource")
            sim.total_return_pct = result.get("total_return_pct")
            sim.sharpe_ratio = result.get("sharpe_ratio")
            sim.max_drawdown_pct = result.get("max_drawdown_pct")
            sim.win_rate_pct = result.get("win_rate_pct")
            sim.num_trades = result.get("num_trades")
            sim.final_capital = result.get("final_capital")
            
            sim.full_metrics_json = {
                "total_return_pct": result.get("total_return_pct"),
                "sharpe_ratio": result.get("sharpe_ratio"),
            }
            
            equity_samples = []
            if result.get("equity_curve") is not None:
                eq = result.get("equity_curve").reset_index()
                eq.columns = ["date", "value"]
                eq["date"] = eq["date"].astype(str)
                equity_samples = eq.to_dict(orient="records")
            sim.equity_curve_json = equity_samples
            
            sim.status = "completed"
            db.commit()
            
        except Exception as e:
            sim.status = "failed"
            sim.error_log = str(e)
            db.commit()

@router.post("/{strategy_id}/run")
def trigger_backtest(strategy_id: int, background_tasks: BackgroundTasks) -> dict[str, Any]:
    """Trigger a backtest run for the given Strategy ID as a background task."""
    with get_session() as db:
        template = db.get(StrategyTemplate, strategy_id)
        if not template:
            raise HTTPException(status_code=404, detail="Strategy not found")
        
        ws = template.wizard_state
        
        try:
            period_start = datetime.datetime.strptime(ws["start_date"], "%Y-%m-%d")
            period_end   = datetime.datetime.strptime(ws["end_date"],   "%Y-%m-%d")
        except (KeyError, ValueError):
            period_start = period_end = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
            
        sim = SimulationResult(
            strategy_template_id=template.id,
            symbol=ws.get("symbol", "UNKNOWN"),
            timeframe=ws.get("timeframe", "1d"),
            period_start=period_start,
            period_end=period_end,
            engine_used="pending",
            initial_capital=float(ws.get("initial_capital", 10000)),
            status="pending"
        )
        db.add(sim)
        db.commit()
        db.refresh(sim)
        
        background_tasks.add_task(run_backtest_task, sim.id, template.id)
        
        return {
            "message": "Backtest triggered successfully.",
            "simulation_id": sim.id,
            "status": sim.status
        }
