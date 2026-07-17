"""Review 2026-07-16: payload jobu z ``_execute_dag_backtest`` musi zawierać ``raw``.

Silnik dokłada do ``raw`` liczniki Stop Loss/Take Profit Exits (Faza 12, per symbol
w multi z review Fazy 10), ale runner kopiował do payloadu tylko metrics/equity_curve —
liczniki nigdy nie docierały do DB ani API (bug #2 z testów manualnych faz 10–14).
"""

import pandas as pd

import app.services.engine.runner as runner_mod


class FakeDagEngine:
    """Atrapa silnika DAG — zwraca kontrakt run_dag_backtest z licznikami w raw."""

    def __init__(self, result: dict):
        self._result = result

    def run_dag_backtest(self, df: pd.DataFrame, dag: dict) -> dict:
        return self._result


_DAG = {
    "nodes": [
        {
            "id": "d1",
            "category": "DataIngestion",
            "params": {"symbol": "AAPL", "dataSource": "yahoo"},
        }
    ]
}


def _mock_fetch(monkeypatch) -> None:
    df = pd.DataFrame(
        {"close": [100.0, 101.0, 102.0]},
        index=pd.date_range("2024-01-01", periods=3, freq="D"),
    )
    monkeypatch.setattr(runner_mod, "_fetch_market_data", lambda *a, **kw: df)


def test_execute_dag_backtest_surfaces_raw_single(monkeypatch):
    """Single-symbol: raw (w tym liczniki SL/TP) trafia do payloadu jobu."""
    _mock_fetch(monkeypatch)
    engine = FakeDagEngine(
        {
            "metrics": {"Total Return [%]": 5.0, "Sharpe Ratio": 1.2},
            "equity_curve": [{"date": "2024-01-01", "value": 10000.0}],
            "raw": {"Stop Loss Exits": 2, "Take Profit Exits": 1, "Start": "2024-01-01"},
        }
    )

    payload = runner_mod._execute_dag_backtest(engine, _DAG)

    assert payload["Total Return [%]"] == 5.0
    assert payload["equity_curve"] == [{"date": "2024-01-01", "value": 10000.0}]
    assert payload["raw"]["Stop Loss Exits"] == 2
    assert payload["raw"]["Take Profit Exits"] == 1


def test_execute_dag_backtest_surfaces_raw_multi(monkeypatch):
    """Multi-symbol: zagnieżdżone raw per ticker zachowuje strukturę (serializacja
    rekurencyjna 1 poziom — jak nested metrics z Fazy 10)."""
    _mock_fetch(monkeypatch)
    engine = FakeDagEngine(
        {
            "metrics": {"Total Return [%]": {"AAPL": 5.0, "MSFT": 3.0}},
            "is_multi_symbol": True,
            "symbols": ["AAPL", "MSFT"],
            "raw": {
                "AAPL": {"Stop Loss Exits": 1},
                "MSFT": {"Stop Loss Exits": 0},
            },
        }
    )

    payload = runner_mod._execute_dag_backtest(engine, _DAG)

    assert payload["is_multi_symbol"] is True
    assert payload["raw"]["AAPL"]["Stop Loss Exits"] == 1
    assert payload["raw"]["MSFT"]["Stop Loss Exits"] == 0


def test_execute_dag_backtest_surfaces_allocation(monkeypatch):
    """ADR-0009: blok allocation z wyniku silnika trafia do payloadu jobu."""
    _mock_fetch(monkeypatch)
    allocation = {
        "timeline": {"dates": ["2024-01-01"], "weights": {"AAPL": [0.4], "cash": [0.6]}},
        "summary": {
            "AAPL": {
                "avg_exposure_pct": 40.0,
                "max_exposure_pct": 90.0,
                "time_in_market_pct": 50.0,
                "final_equity_share_pct": 100.0,
            }
        },
    }
    engine = FakeDagEngine(
        {
            "metrics": {"Total Return [%]": 5.0},
            "equity_curve": [{"date": "2024-01-01", "value": 10000.0}],
            "allocation": allocation,
        }
    )

    payload = runner_mod._execute_dag_backtest(engine, _DAG)

    assert payload["allocation"] == allocation
