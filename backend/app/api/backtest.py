
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from sqlalchemy import select

from app.core.user_scope import get_user_id, scoped_query
from app.core.utils.graph_parser import GraphParser, GraphValidationError
from app.db.session import get_session
from app.models.orm import BacktestJob, JobStatus, Strategy
from app.schemas.backtest import BacktestJobResponse, BacktestRequest, DAGBacktestRequest
from app.schemas.base import ApiResponse
from app.services.engine.runner import run_vectorbt_backtest

"""Trasy obsługujące backtestowanie — Faza 2.

Flow:
  POST /api/backtest/       → tworzy obiekt BacktestJob (PENDING), zwraca natychmiast job_id
  GET  /api/backtest/{id}   → służy do odpytywania statusu i metryk pracy zapisanej w SQLite.
"""

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _dag_view_params(params: dict[str, Any]) -> dict[str, Any]:
    """Uzupełnia płaskie metadane widoku dla jobów DAG (review 2026-07-16).

    Joby z POST /api/backtest/dag mają parameters_snapshot = {"dag": ...} —
    bez płaskich kluczy symbol/timeframe/dat odpowiedź GET zwracała puste
    stringi. Czytamy je z węzła DataIngestion, a kapitał z węzła Execution
    (klucze camelCase pochodzą z eksportu frontendowego kanwy).
    """
    dag = params.get("dag")
    if not isinstance(dag, dict):
        return params

    merged = dict(params)
    nodes = dag.get("nodes", [])

    data_node = next((n for n in nodes if n.get("category") == "DataIngestion"), None)
    if data_node:
        node_params = data_node.get("params", {})
        merged.setdefault("symbol", node_params.get("symbol", ""))
        merged.setdefault("data_source", node_params.get("dataSource", "yahoo"))
        merged.setdefault("timeframe", node_params.get("timeframe", ""))
        merged.setdefault("start_date", node_params.get("startDate", ""))
        merged.setdefault("end_date", node_params.get("endDate", ""))

    exec_node = next((n for n in nodes if n.get("category") == "Execution"), None)
    if exec_node:
        exec_params = exec_node.get("params", {})
        capital = exec_params.get("init_cash", exec_params.get("initialCapital"))
        if capital is not None:
            merged.setdefault("initial_capital", capital)

    return merged


def _job_to_schema(job: BacktestJob, include_curve: bool = True) -> BacktestJobResponse:
    """Konwertuje model ORM BacktestJob na schemat BacktestJobResponse.

    ``include_curve=False`` (lista jobów, audyt 2026-07-17): equity_curve to
    tysiące punktów per job — lista ma być lekka, pełna krzywa tylko w GET /{id}.
    """
    raw_metrics = job.metrics or {}
    params = _dag_view_params(job.parameters_snapshot or {})

    # Helper to find values in raw_metrics or job attributes
    def get_metric(json_key: str, db_attr: Any):
        val = raw_metrics.get(json_key)
        if val is None:
            return db_attr
        return val

    # Robust mapping for trades and capital - force types and handle None
    raw_trades = raw_metrics.get("Total Trades")
    if raw_trades is None:
        raw_trades = job.num_trades
    num_trades = int(raw_trades) if raw_trades is not None else 0

    raw_final = raw_metrics.get("Final Value")
    if raw_final is None:
        raw_final = job.final_capital
    final_capital = float(raw_final) if raw_final is not None else 0.0

    frontend_metrics = {
        "engine": raw_metrics.get("engine", "vectorbt-opensource"),
        "symbol": params.get("symbol", ""),
        "data_source": params.get("data_source", "yahoo"),
        "strategy_type": params.get("strategy_type", "sma_crossover"),
        "sma_fast": params.get("sma_fast", 10),
        "sma_slow": params.get("sma_slow", 30),
        "initial_capital": params.get("initial_capital", 10000.0),
        "total_return_pct": get_metric("Total Return [%]", job.total_return_pct),
        "sharpe_ratio": get_metric("Sharpe Ratio", job.sharpe_ratio),
        "max_drawdown_pct": get_metric("Max Drawdown [%]", job.max_drawdown_pct),
        "win_rate_pct": raw_metrics.get("Win Rate [%]"),
        "num_trades": num_trades,
        "final_capital": final_capital,
    }

    # Populate metrics ONLY if status is COMPLETED
    is_completed = (job.status == JobStatus.COMPLETED or job.status == "COMPLETED")

    # Faza 10 (review): wynik multi-symbol — nie spłaszczaj metryk, przenieś strukturę
    # per-ticker + flagi, aby frontend rozpoznał gałąź multi przez GET /api/backtest/{id}.
    is_multi_symbol = bool(raw_metrics.get("is_multi_symbol"))
    if is_completed and is_multi_symbol:
        symbols: list[str] = list(raw_metrics.get("symbols", []))
        nested_metrics = {sym: raw_metrics.get(sym) for sym in symbols}
        return BacktestJobResponse(
            id=job.id,
            job_id=job.id,
            strategy_id=job.strategy_id,
            status=job.status,
            symbol=params.get("symbol", symbols),
            timeframe=params.get("timeframe", ""),
            start_date=params.get("start_date", ""),
            end_date=params.get("end_date", ""),
            initial_capital=params.get("initial_capital", 10000.0),
            created_at=job.created_at,
            metrics=nested_metrics,
            parameters=params,
            error_message=job.error_message,
            equity_curve=raw_metrics.get("equity_curve") if include_curve else None,
            allocation=raw_metrics.get("allocation") if include_curve else None,
            is_multi_symbol=True,
            symbols=symbols,
        )

    return BacktestJobResponse(
        id=job.id,
        job_id=job.id,
        strategy_id=job.strategy_id,
        status=job.status,
        symbol=params.get("symbol", ""),
        timeframe=params.get("timeframe", ""),
        start_date=params.get("start_date", ""),
        end_date=params.get("end_date", ""),
        initial_capital=params.get("initial_capital", 10000.0),
        created_at=job.created_at,
        metrics=frontend_metrics if is_completed else None,
        parameters=params,
        error_message=job.error_message,
        total_return_pct=job.total_return_pct,
        sharpe_ratio=job.sharpe_ratio,
        max_drawdown_pct=job.max_drawdown_pct,
        num_trades=job.num_trades,
        final_capital=job.final_capital,
        equity_curve=raw_metrics.get("equity_curve") if include_curve else None,
        allocation=raw_metrics.get("allocation") if include_curve else None,
        is_multi_symbol=False,
    )


# ---------------------------------------------------------------------------
# API Routes
# ---------------------------------------------------------------------------


@router.post("/", summary="Wyzwalanie backtestu", status_code=202, response_model=ApiResponse[BacktestJobResponse], deprecated=True)
def trigger_backtest(
    payload: BacktestRequest,
    background_tasks: BackgroundTasks,
    request: Request,
) -> ApiResponse[BacktestJobResponse]:
    """Tworzy rekord BacktestJob o statusie PENDING, planuje wykonanie w tle i natychmiastowo
    zwraca jego identyfikator."""
    user_id = get_user_id(request)
    with get_session() as db:
        strategy = db.get(Strategy, payload.strategy_id)
        if not strategy:
            raise HTTPException(
                status_code=404,
                detail=f"Strategy id={payload.strategy_id} not found",
            )

        # Merge strategy parameters with any per-request overrides
        params: dict[str, Any] = dict(strategy.parameters)
        params["code_content"] = strategy.code_content
        overrides = payload.model_dump(exclude_unset=True, exclude={"strategy_id", "parameters"})
        params.update(overrides)
        if payload.parameters:
            params.update(payload.parameters)

        job = BacktestJob(
            strategy_id=strategy.id,
            status=JobStatus.PENDING,
            parameters_snapshot=params,
            user_id=user_id,
        )
        db.add(job)
        db.flush()
        data = _job_to_schema(job)

    # Enqueue the engine — runs in FastAPI's background thread pool
    background_tasks.add_task(run_vectorbt_backtest, job.id, params)

    return ApiResponse(success=True, data=data)


@router.post("/dag", summary="Wyzwalanie backtestu na podstawie grafu DAG", status_code=202, response_model=ApiResponse[BacktestJobResponse])
def trigger_dag_backtest(
    payload: DAGBacktestRequest,
    background_tasks: BackgroundTasks,
    request: Request,
) -> ApiResponse[BacktestJobResponse]:
    """Waliduje graf DAG i przekazuje go do wykonania."""
    try:
        parser = GraphParser(nodes=payload.dag.nodes, edges=payload.dag.edges)
        parser.validate()
    except GraphValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))

    user_id = get_user_id(request)
    with get_session() as db:
        strategy = db.get(Strategy, payload.strategy_id)
        if not strategy:
            raise HTTPException(
                status_code=404,
                detail=f"Strategy id={payload.strategy_id} not found",
            )

        # Update strategy parameters to store the DAG structure
        dag_dict = payload.dag.model_dump()
        strategy.parameters = dag_dict
        if user_id is not None and strategy.user_id is None:
            strategy.user_id = user_id
        db.add(strategy)
        
        job = BacktestJob(
            strategy_id=strategy.id,
            status=JobStatus.PENDING,
            parameters_snapshot={"dag": dag_dict},
            user_id=user_id,
        )
        db.add(job)
        db.flush()
        data = _job_to_schema(job)

    background_tasks.add_task(run_vectorbt_backtest, job.id, {"dag": dag_dict})

    return ApiResponse(success=True, data=data)


@router.get("/{job_id}", summary="Pobieranie statusu pojedynczego zadania", response_model=ApiResponse[BacktestJobResponse])
def get_backtest_status(job_id: int, request: Request) -> ApiResponse[BacktestJobResponse]:
    """Zwraca aktualny status i wyniki wyliczonych metryk określonego zadania."""
    with get_session() as db:
        job = db.get(BacktestJob, job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job id={job_id} not found")
        
        user_id = get_user_id(request)
        if user_id is not None and job.user_id is not None and job.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
            
        db.refresh(job)  # Force refresh from DB to see latest metrics
        return ApiResponse(success=True, data=_job_to_schema(job))


@router.get("/", summary="Listowanie wszystkich zadań backtestów", response_model=ApiResponse[list[BacktestJobResponse]])
def list_jobs(request: Request) -> ApiResponse[list[BacktestJobResponse]]:
    """Zwraca listę wszystkich zadań backtestowania posortowanych od najnowszych."""
    with get_session() as db:
        stmt = scoped_query(select(BacktestJob).order_by(BacktestJob.created_at.desc()), BacktestJob, request)
        jobs = db.scalars(stmt).all()
        # Audyt 2026-07-17: lista bez equity_curve (multi-MB payload przy wielu jobach)
        data = [_job_to_schema(j, include_curve=False) for j in jobs]
        return ApiResponse(success=True, data=data)
