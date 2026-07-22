"""
Parametry dynamicznych wskaźników registry (audyt 2026-07-17, P3).

UI pozwala wybrać wskaźnik z registry i edytować jego parametry, ale
``IndicatorsParams`` (schemat) wycinał nieznane pola, a ``run_dag_backtest``
budował ``flat_params`` wyłącznie ze stałej listy kluczy — edytowany parametr
nigdy nie docierał do silnika i backtest liczył się na wartościach domyślnych
bez ostrzeżenia.
"""


import numpy as np
import pandas as pd

from app.services.engine.opensource_engine import OpenSourceEngine


def test_indicators_params_keeps_unknown_registry_params():
    from app.schemas.dag import IndicatorsParams

    params = IndicatorsParams(indicatorType="rsi", period=7)

    assert params.model_dump().get("period") == 7


def test_run_dag_backtest_passes_dynamic_params_to_indicator_service(monkeypatch):
    from app.services.engine.indicators import IndicatorService

    idx = pd.date_range("2023-01-01", periods=60, freq="D")
    df = pd.DataFrame({"close": np.linspace(100.0, 120.0, len(idx))}, index=idx)

    captured: dict = {}

    def fake_generate(close, params, vbt):
        captured.update(params)
        signal = pd.Series(False, index=close.index)
        return signal, signal.copy()

    monkeypatch.setattr(IndicatorService, "generate_signals", staticmethod(fake_generate))

    dag = {
        "nodes": [
            {"id": "d1", "type": "dataNode", "category": "DataIngestion",
             "params": {"symbol": "TEST", "timeframe": "1d"}},
            {"id": "i1", "type": "indicatorNode", "category": "Indicators",
             "params": {"indicatorType": "rsi", "period": 7, "windows": [14]}},
            {"id": "e1", "type": "portfolioNode", "category": "Execution",
             "params": {"init_cash": 10000.0, "fees": 0.001, "slippage": 0.001}},
        ],
        "edges": [],
    }

    OpenSourceEngine().run_dag_backtest(df, dag)

    assert captured.get("period") == 7, "parametr registry nie dotarł do IndicatorService"
    assert captured.get("windows") == [14]
    assert captured.get("strategy_type") == "rsi"
