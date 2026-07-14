"""
Faza 10 (review): test integracyjny mapowania ORM → BacktestJobResponse dla multi-symbol.

Luka wykryta w code review: `_job_to_schema` spłaszczał metryki i gubił pola
`is_multi_symbol`, `symbols` oraz zagnieżdżone metryki per-ticker — przez co gałąź
multi-symbol nigdy nie docierała do frontendu przez realny endpoint GET /api/backtest/{id}.
"""

import datetime

from app.api.backtest import _job_to_schema
from app.models.orm import BacktestJob, JobStatus


def _multi_metrics() -> dict:
    return {
        "AAPL": {
            "Total Return [%]": 1.2,
            "Sharpe Ratio": 0.5,
            "Max Drawdown [%]": -3.0,
            "Total Trades": 4,
            "Final Value": 10120.0,
            "Win Rate [%]": 50.0,
        },
        "MSFT": {
            "Total Return [%]": 2.4,
            "Sharpe Ratio": 0.8,
            "Max Drawdown [%]": -2.0,
            "Total Trades": 6,
            "Final Value": 10240.0,
            "Win Rate [%]": 60.0,
        },
        "is_multi_symbol": True,
        "symbols": ["AAPL", "MSFT"],
        "equity_curve": {
            "AAPL": [{"date": "2024-01-01", "value": 10000.0}],
            "MSFT": [{"date": "2024-01-01", "value": 10000.0}],
        },
    }


def _make_job(metrics: dict, symbol) -> BacktestJob:
    job = BacktestJob(
        strategy_id=1,
        status=JobStatus.COMPLETED,
        parameters_snapshot={"symbol": symbol, "timeframe": "1d"},
        metrics=metrics,
    )
    job.id = 123
    job.created_at = datetime.datetime(2024, 1, 1)
    return job


def test_job_to_schema_propagates_multi_symbol():
    """Multi-symbol: response zachowuje flagi, symbols, zagniezdzone metryki i equity_curve dict."""
    job = _make_job(_multi_metrics(), symbol=["AAPL", "MSFT"])

    resp = _job_to_schema(job)

    assert resp.is_multi_symbol is True
    assert resp.symbols == ["AAPL", "MSFT"]
    # Zagniezdzenie per-ticker zachowane (bez splaszczenia)
    assert isinstance(resp.metrics, dict)
    assert "AAPL" in resp.metrics and "MSFT" in resp.metrics
    assert resp.metrics["AAPL"]["Total Return [%]"] == 1.2
    # equity_curve jako slownik per symbol
    assert isinstance(resp.equity_curve, dict)
    assert "AAPL" in resp.equity_curve
    assert resp.symbol == ["AAPL", "MSFT"]


def test_job_to_schema_single_symbol_unchanged():
    """Single-symbol: plaskie metryki, brak is_multi_symbol, equity_curve to lista."""
    metrics = {
        "Total Return [%]": 15.5,
        "Sharpe Ratio": 1.8,
        "Max Drawdown [%]": -5.0,
        "Total Trades": 10,
        "Final Value": 11550.0,
        "equity_curve": [{"date": "2024-01-01", "value": 10000.0}],
    }
    job = _make_job(metrics, symbol="AAPL")

    resp = _job_to_schema(job)

    assert not resp.is_multi_symbol
    assert resp.symbols is None
    assert resp.metrics is not None
    assert resp.metrics["total_return_pct"] == 15.5
    assert isinstance(resp.equity_curve, list)
