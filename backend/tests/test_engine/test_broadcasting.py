import pytest
import pandas as pd
from app.services.engine.opensource_engine import OpenSourceEngine

def test_broadcasting_multiple_tickers():
    engine = OpenSourceEngine()
    # Przekazujemy listę tickerów
    dag_dict = {
        "nodes": [
            {"id": "d1", "category": "DataIngestion", "type": "dataNode", "params": {"symbol": ["AAPL", "MSFT"]}},
            {"id": "i1", "category": "Indicators", "type": "indicatorNode", "params": {"indicatorType": "sma_crossover", "smaFast": 10, "smaSlow": 30}},
            {"id": "e1", "category": "Execution", "type": "executionNode", "params": {"init_cash": 10000.0}}
        ]
    }
    # Symulujemy df z MultiIndex (wymaga implementacji)
    dummy_index = pd.MultiIndex.from_product([["AAPL", "MSFT"], pd.date_range("2020-01-01", periods=100)], names=["symbol", "date"])
    df = pd.DataFrame({"close": [100.0]*200}, index=dummy_index)
    
    # Próba uruchomienia - powinna rzucić błąd lub nie zwrócić oczekiwanego formatu
    result = engine.run_dag_backtest(df, dag_dict)
    
    # Oczekujemy że metryki będą zgrupowane per ticker (nowa funkcjonalność)
    # Obecna implementacja prawdopodobnie zwróci słownik bez kluczy AAPL/MSFT na tym poziomie
    assert "AAPL" in result.get("metrics", {}), "Metric AAPL missing from result"
    assert "MSFT" in result.get("metrics", {}), "Metric MSFT missing from result"
    assert result.get("metrics", {}).get("AAPL") is not None
    assert result.get("metrics", {}).get("MSFT") is not None
