import pytest
import pandas as pd
from app.services.engine.opensource_engine import OpenSourceEngine

def test_portfolio_stop_loss_take_profit():
    engine = OpenSourceEngine()
    dag_dict = {
        "nodes": [
            {"id": "p1", "category": "Execution", "type": "portfolioNode", "params": {"sl_stop": 0.05, "tp_stop": 0.10}}
        ]
    }
    # Symulujemy dummy DataFrame i sygnały
    df = pd.DataFrame({"close": [100, 90, 110, 105, 95]})
    
    # Aktualnie OpenSourceEngine ignoruje te parametry, test powinien to wyłapać (wymaga implementacji)
    result = engine.run_dag_backtest(df, dag_dict)
    
    # Powinno wygenerować transakcje na podstawie uderzenia w SL/TP
    # Weryfikujemy czy SL/TP zadziałały (aktualnie nie zadziałają, bo execute_dag_portfolio ich nie używa)
    metrics = result.get("metrics", {})
    
    # Jeśli SL/TP by działało, liczba transakcji powinna być różna od 0 przy takich ruchach ceny
    # Ale przede wszystkim szukamy potwierdzenia w 'raw' stats lub logach jeśli by istniały.
    # Na ten moment sprawdzamy czy test FAILUJE na braku implementacji SL/TP w silniku.
    # W vbt stats SL/TP exitów szukamy w countach exitów.
    raw_stats = result.get("raw", {})
    assert raw_stats.get("Stop Loss Exits", 0) > 0 or raw_stats.get("Take Profit Exits", 0) > 0
