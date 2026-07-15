"""Testy E2E endpointu Walk-Forward Optimization (Faza 15).

POST /api/optimizer/wfo z zamockowanymi danymi rynkowymi (syntetyczne OHLC),
następnie odczyt wyniku przez GET /api/optimizer/{job_id}.
TestClient wykonuje BackgroundTasks synchronicznie po odpowiedzi.
"""

import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

from app.db.session import get_session
from app.main import app
from app.models.orm import Strategy

client = TestClient(app)


def _synthetic_market_data(n: int = 400) -> pd.DataFrame:
    """Syntetyczne dane dzienne (sinusoida + dryf) — deterministyczne, offline."""
    dates = pd.date_range("2021-01-01", periods=n, freq="D")
    close = 100.0 + np.sin(np.arange(n) / 8.0) * 4.0 + np.arange(n) * 0.02
    return pd.DataFrame({"close": close}, index=dates)


def _create_strategy() -> int:
    with get_session() as db:
        strategy = Strategy(
            name="WFO E2E Strategy",
            description="Strategia do testu E2E WFO",
            parameters={"sma_fast": 5, "sma_slow": 20},
        )
        db.add(strategy)
        db.commit()
        db.refresh(strategy)
        return strategy.id


def _mock_market_data(monkeypatch) -> None:
    import app.services.engine.runner as runner_mod

    def fake_fetch(source, symbol, start, end, timeframe):
        return _synthetic_market_data()

    monkeypatch.setattr(runner_mod, "_fetch_market_data", fake_fetch)


def test_trigger_wfo_fixed_params_e2e(db_session, monkeypatch):
    """Ścieżka bez param_bounds — walk-forward na stałych parametrach strategii."""
    _mock_market_data(monkeypatch)
    strategy_id = _create_strategy()

    payload = {
        "strategy_id": strategy_id,
        "symbol": "SYNTHETIC",
        "window_size": "180d",
        "step_size": "60d",
        "parameters": {"sma_fast": 5, "sma_slow": 20},
    }
    response = client.post("/api/optimizer/wfo", json=payload)
    assert response.status_code == 202
    job_id = response.json()["data"]["job_id"]

    status_res = client.get(f"/api/optimizer/{job_id}")
    assert status_res.status_code == 200
    data = status_res.json()["data"]

    assert data["status"] == "COMPLETED"
    assert data["error_message"] is None
    # Wyniki per okno trafiają do trials_data.trials (kontrakt frontendowego WfoNode)
    windows = data["trials_data"]["trials"]
    # 400 dni, IS 180d, OOS/step 60d -> 4 okna
    assert len(windows) == 4
    for window in windows:
        assert window["oos_start"] >= window["is_end"]
        assert "Total Return [%]" in window["oos_metrics"]
        assert "Sharpe Ratio" in window["oos_metrics"]

    assert data["best_parameters"] is not None
    assert data["best_value"] is not None


def test_trigger_wfo_with_optimization_e2e(db_session, monkeypatch):
    """Ścieżka z param_bounds (Optuna in-sample) + tryb anchored."""
    _mock_market_data(monkeypatch)
    strategy_id = _create_strategy()

    payload = {
        "strategy_id": strategy_id,
        "symbol": "SYNTHETIC",
        "window_size": "180d",
        "step_size": "60d",
        "mode": "anchored",
        "n_trials": 2,
        "parameters": {"sma_slow": 20},
        "param_bounds": {"sma_fast": {"min": 3, "max": 10, "type": "int"}},
    }
    response = client.post("/api/optimizer/wfo", json=payload)
    assert response.status_code == 202
    job_id = response.json()["data"]["job_id"]

    status_res = client.get(f"/api/optimizer/{job_id}")
    data = status_res.json()["data"]

    assert data["status"] == "COMPLETED"
    windows = data["trials_data"]["trials"]
    assert len(windows) == 4
    for window in windows:
        assert 3 <= window["best_params"]["sma_fast"] <= 10

    assert 3 <= data["best_parameters"]["sma_fast"] <= 10


def test_trigger_wfo_invalid_mode_rejected(db_session):
    """Ścisła walidacja Pydantic: nieznany tryb -> 422."""
    strategy_id = _create_strategy()
    payload = {
        "strategy_id": strategy_id,
        "symbol": "SYNTHETIC",
        "mode": "sideways",
    }
    response = client.post("/api/optimizer/wfo", json=payload)
    assert response.status_code == 422


def test_trigger_wfo_strategy_not_found(db_session):
    payload = {"strategy_id": 999999, "symbol": "SYNTHETIC"}
    response = client.post("/api/optimizer/wfo", json=payload)
    assert response.status_code == 404
