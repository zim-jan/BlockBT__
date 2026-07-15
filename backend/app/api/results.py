import datetime
from typing import Any

import pandas as pd
from fastapi import APIRouter, HTTPException

from app.db.session import get_session
from app.models.orm import BacktestJob, ChatMessage
from app.schemas.base import ApiResponse
from app.schemas.results import (
    AIAnalysisResponse,
    ChatMessageResponse,
    ChatRequest,
    TearsheetResponse,
)
from app.services.engine.qsadapter import QSAdapterService
from app.services.mcp.llm_client import OllamaClient
from app.services.mcp.report_builder import ReportBuilder

router = APIRouter()


@router.get("/{job_id}", response_model=ApiResponse[dict[str, Any]])
def get_simulation_result(job_id: int) -> ApiResponse[dict[str, Any]]:
    """Retrieve the status and metrics of a backtest run by its Simulation ID."""
    with get_session() as db:
        job = db.get(BacktestJob, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Simulation Result not found")

        data = {
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
        return ApiResponse(success=True, data=data)


@router.get("/{job_id}/tearsheet", response_model=ApiResponse[TearsheetResponse])
def get_tearsheet(job_id: int) -> ApiResponse[TearsheetResponse]:
    """Faza 13: generuje tearsheet HTML z metryk ukończonego backtestu.

    ``BacktestJob`` nie przechowuje żywego obiektu vbt Portfolio, więc budujemy
    lekki adapter udostępniający ``stats()`` na podstawie zapisanych metryk joba,
    a następnie renderujemy air-gapped HTML przez ``QSAdapterService``.
    """
    with get_session() as db:
        job = db.get(BacktestJob, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Simulation Result not found")

        if job.status.upper() != "COMPLETED":
            raise HTTPException(
                status_code=400,
                detail="Cannot generate a tearsheet for a simulation that is not completed.",
            )

        # Metryki nagłówkowe (kolumny) + elastyczny słownik `metrics` (JSON).
        stats: dict[str, Any] = {
            "Total Return [%]": job.total_return_pct,
            "Sharpe Ratio": job.sharpe_ratio,
            "Max Drawdown [%]": job.max_drawdown_pct,
            "Total Trades": job.num_trades,
            "Final Value": job.final_capital,
        }
        if job.metrics:
            for key, value in job.metrics.items():
                # Pomijamy złożone struktury (np. equity_curve_json) — tabela to skalary.
                if isinstance(value, (int, float, str, type(None))):
                    stats.setdefault(str(key), value)

        class _StoredMetricsPortfolio:
            def stats(self) -> dict[str, Any]:
                return stats

        html_output = QSAdapterService.generate_tearsheet(_StoredMetricsPortfolio())

        data = TearsheetResponse(
            job_id=job.id,
            html=html_output,
            format="html",
            generated_at=datetime.datetime.now(datetime.UTC),
        )
        return ApiResponse(success=True, data=data)


@router.post("/{job_id}/analyze", response_model=ApiResponse[AIAnalysisResponse])
async def analyze_simulation_result(job_id: int) -> ApiResponse[AIAnalysisResponse]:
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
            return ApiResponse(success=True, data=AIAnalysisResponse(prompt=None, report=job.ai_analysis_report))

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
            result=result, strategy_name=strategy_name, raw_params=raw_params
        )
        prompt = payload.to_prompt()
        
        # Fetch the default system prompt, or fallback to the hardcoded default
        from sqlalchemy import select

        from app.models.orm import SystemPrompt
        from app.services.mcp.llm_client import _SYSTEM_PROMPT
        
        system_prompt = db.execute(
            select(SystemPrompt).where(SystemPrompt.is_default == True) # noqa: E712
        ).scalar_one_or_none()
        system_content = system_prompt.content if system_prompt else _SYSTEM_PROMPT
        
        report = await OllamaClient().generate_report(prompt, system=system_content)
        job.ai_analysis_report = report

        # Zapisanie promptu (user) i raportu (assistant) do tabeli ChatMessage
        db.add(ChatMessage(job_id=job.id, role="user", content=prompt))
        db.add(ChatMessage(job_id=job.id, role="assistant", content=report))

        db.commit()
        data = AIAnalysisResponse(prompt=prompt, report=job.ai_analysis_report)
        return ApiResponse(success=True, data=data)


@router.get("/{job_id}/chat", response_model=ApiResponse[list[ChatMessageResponse]])
def get_chat_history(job_id: int) -> ApiResponse[list[ChatMessageResponse]]:
    """Retrieve the chat history for a specific backtest job."""
    with get_session() as db:
        job = db.get(BacktestJob, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Simulation Result not found")

        messages = sorted(job.chat_messages, key=lambda m: m.created_at)
        data = [
            ChatMessageResponse(
                id=m.id, job_id=m.job_id, role=m.role, content=m.content, created_at=m.created_at
            )
            for m in messages
        ]
        return ApiResponse(success=True, data=data)


@router.post("/{job_id}/chat", response_model=ApiResponse[ChatMessageResponse])
async def add_chat_message(job_id: int, request: ChatRequest) -> ApiResponse[ChatMessageResponse]:
    """Pobiera wiadomość analityka, przekazuje kontekst i zwraca odpowiedź LLM."""
    with get_session() as db:
        job = db.get(BacktestJob, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Simulation Result not found")

        if not job.ai_analysis_report:
            raise HTTPException(
                status_code=400, detail="Cannot start chat without initial AI analysis report."
            )

        # Zapisz wiadomość analityka, ale nie commituj
        user_message = ChatMessage(job_id=job.id, role="user", content=request.content)
        db.add(user_message)
        db.flush()  # pobranie ID i uwzględnienie w sesji bez zatwierdzania transakcji

        # Przygotuj historię czatu dla Ollamy
        history = sorted(job.chat_messages, key=lambda m: m.created_at)
        llm_messages = [{"role": m.role, "content": m.content} for m in history]

        # Wywołanie Ollamy (async)
        client = OllamaClient()
        response_content = await client.chat(llm_messages)

        if response_content.startswith("[ERROR]"):
            db.rollback()
            raise HTTPException(status_code=500, detail=response_content)

        assistant_message = ChatMessage(job_id=job.id, role="assistant", content=response_content)
        db.add(assistant_message)

        db.commit()
        db.refresh(assistant_message)

        data = ChatMessageResponse(
            id=assistant_message.id,
            job_id=assistant_message.job_id,
            role=assistant_message.role,
            content=assistant_message.content,
            created_at=assistant_message.created_at,
        )
        return ApiResponse(success=True, data=data)
