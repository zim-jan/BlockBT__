import datetime
from typing import Any

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException
from loguru import logger

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
        # Pomijamy wartości `None` — brak metryki nie powinien pojawiać się w tabeli
        # jako pusty wiersz; dzięki temu pusty `stats` poprawnie trafia w gałąź
        # "Brak dostępnych metryk" w QSAdapterService, zamiast renderować same myślniki.
        raw_headline: dict[str, Any] = {
            "Total Return [%]": job.total_return_pct,
            "Sharpe Ratio": job.sharpe_ratio,
            "Max Drawdown [%]": job.max_drawdown_pct,
            "Total Trades": job.num_trades,
            "Final Value": job.final_capital,
        }
        stats: dict[str, Any] = {k: v for k, v in raw_headline.items() if v is not None}

        if job.metrics:
            for key, value in job.metrics.items():
                if value is None:
                    continue
                # Pomijamy złożone struktury (np. equity_curve_json) — tabela to skalary.
                # Numpy scalary (np. numpy.float64/int64 z etapu backtestu) rzutujemy
                # jawnie na natywny float, żeby nie trafiły w niezmienionej postaci
                # do JSON-a (np.float64 nie jest natywnie serializowalny/porównywalny
                # tak jak float w niektórych ścieżkach).
                if isinstance(value, np.floating | np.integer):
                    stats.setdefault(str(key), float(value))
                elif isinstance(value, (int, float, str)):
                    stats.setdefault(str(key), value)

        if not stats:
            logger.warning(
                "Tearsheet dla job_id={} nie ma dostępnych metryk (metrics=None, kolumny puste).",
                job_id,
            )

        class _StoredMetricsPortfolio:
            def stats(self) -> dict[str, Any]:
                return stats

        # Jedno źródło czasu: przekazujemy generated_at do wnętrza HTML, żeby nie
        # dublować niezależnie generowanego znacznika czasu w treści i w odpowiedzi API.
        generated_at = datetime.datetime.now(datetime.UTC)
        html_output = QSAdapterService.generate_tearsheet(
            _StoredMetricsPortfolio(), generated_at=generated_at
        )

        data = TearsheetResponse(
            job_id=job.id,
            html=html_output,
            format="html",
            generated_at=generated_at,
        )
        return ApiResponse(success=True, data=data)


@router.post("/{job_id}/analyze", response_model=ApiResponse[AIAnalysisResponse])
async def analyze_simulation_result(job_id: int) -> ApiResponse[AIAnalysisResponse]:
    """Generate an AI analysis report for a completed simulation.

    Audyt 2026-07-17: sesja DB jest zamykana PRZED wywołaniem LLM (potrafi
    trwać dziesiątki sekund) — wcześniej otwarta sesja trzymana przez await
    blokowała pulę połączeń; persystencja odbywa się w drugiej, krótkiej sesji.
    """
    # 1) Krótka sesja: walidacja + zebranie danych do promptu
    with get_session() as db:
        job = db.get(BacktestJob, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Simulation Result not found")

        if job.status.upper() != "COMPLETED":
            raise HTTPException(
                status_code=400, detail="Cannot analyze a simulation that is not completed."
            )

        if job.ai_analysis_report:
            return ApiResponse(
                success=True,
                data=AIAnalysisResponse(prompt=None, report=job.ai_analysis_report),
            )

        # Kopia — nie mutujemy ORM-owego JSON-a job.metrics (audyt 2026-07-17:
        # wcześniejsza mutacja in-place wstrzykiwała m.in. pd.Series do atrybutu ORM)
        result = dict(job.metrics or {})
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

        # Fetch the default system prompt, or fallback to the hardcoded default
        from sqlalchemy import select

        from app.models.orm import SystemPrompt
        from app.services.mcp.llm_client import _SYSTEM_PROMPT

        system_prompt = db.execute(
            select(SystemPrompt).where(SystemPrompt.is_default == True) # noqa: E712
        ).scalar_one_or_none()
        system_content = system_prompt.content if system_prompt else _SYSTEM_PROMPT

    payload = ReportBuilder.build(
        result=result, strategy_name=strategy_name, raw_params=raw_params
    )
    prompt = payload.to_prompt()

    # 2) LLM poza sesją — żadne połączenie z puli nie jest trzymane przez await
    report = await OllamaClient().generate_report(prompt, system=system_content)

    # 3) Krótka sesja: persystencja raportu i historii czatu
    with get_session() as db:
        job = db.get(BacktestJob, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Simulation Result not found")
        job.ai_analysis_report = report

        # Zapisanie promptu (user) i raportu (assistant) do tabeli ChatMessage
        db.add(ChatMessage(job_id=job.id, role="user", content=prompt))
        db.add(ChatMessage(job_id=job.id, role="assistant", content=report))

        db.commit()

    return ApiResponse(success=True, data=AIAnalysisResponse(prompt=prompt, report=report))


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
    """Pobiera wiadomość analityka, przekazuje kontekst i zwraca odpowiedź LLM.

    Audyt 2026-07-17: wcześniej ``flush()`` otwierał transakcję ZAPISU
    trzymaną przez cały await LLM — każdy inny pisarz SQLite dostawał
    ``database is locked``. Teraz: krótka sesja na odczyt historii →
    LLM poza sesją → druga krótka sesja zapisuje parę wiadomości atomowo
    (błąd LLM = zero zapisów, bez rollbacku po fakcie).
    """
    # 1) Krótka sesja: walidacja + odczyt historii czatu
    with get_session() as db:
        job = db.get(BacktestJob, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Simulation Result not found")

        if not job.ai_analysis_report:
            raise HTTPException(
                status_code=400, detail="Cannot start chat without initial AI analysis report."
            )

        history = sorted(job.chat_messages, key=lambda m: m.created_at)
        llm_messages = [{"role": m.role, "content": m.content} for m in history]

    # Nowa wiadomość analityka dokładana do kontekstu bez zapisu do DB
    llm_messages.append({"role": "user", "content": request.content})

    # 2) Wywołanie Ollamy poza sesją/transakcją
    response_content = await OllamaClient().chat(llm_messages)

    if response_content.startswith("[ERROR]"):
        raise HTTPException(status_code=500, detail=response_content)

    # 3) Krótka sesja: atomowy zapis pary user/assistant
    with get_session() as db:
        job = db.get(BacktestJob, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Simulation Result not found")

        user_message = ChatMessage(job_id=job.id, role="user", content=request.content)
        assistant_message = ChatMessage(job_id=job.id, role="assistant", content=response_content)
        db.add_all([user_message, assistant_message])
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
