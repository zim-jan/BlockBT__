import pandas as pd

from app.services.engine.opensource_engine import OpenSourceEngine


def test_portfolio_stop_loss_take_profit():
    engine = OpenSourceEngine()
    # Faza 12: wymóg węzła Indicators wymusza dodanie źródła sygnałów w DAG.
    # Custom indicator (ścieżka Fazy 11): wejście na barze 0, brak własnych exitów —
    # dzięki temu SL na spadku 100->90 (-10%) faktycznie odpala.
    custom_code = (
        "entries = pd.Series(False, index=close.index)\n"
        "entries.iloc[0] = True\n"
        "exits = pd.Series(False, index=close.index)\n"
    )
    dag_dict = {
        "nodes": [
            {"id": "i1", "category": "Indicators", "type": "indicatorNode",
             "params": {"indicatorType": "custom", "codeContent": custom_code}},
            {"id": "p1", "category": "Execution", "type": "portfolioNode", "params": {"sl_stop": 0.05, "tp_stop": 0.10}}
        ]
    }
    # Dummy dane cenowe: spadek 100->90 (-10%) powinien odpalić SL=5%.
    df = pd.DataFrame({"close": [100, 90, 110, 105, 95]})

    result = engine.run_dag_backtest(df, dag_dict)
    metrics = result.get("metrics", {})

    # Weryfikacja: `_count_stop_exits` klasyfikuje zamknięte transakcje po cenie
    # wyjścia względem poziomu stopu (patrz ADR-0003) i surfacuje licznik w `raw`.
    raw_stats = result.get("raw", {})
    assert raw_stats.get("Stop Loss Exits", 0) > 0 or raw_stats.get("Take Profit Exits", 0) > 0
