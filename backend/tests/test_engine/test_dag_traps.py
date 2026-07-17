import pytest
from pydantic import ValidationError

from app.core.utils.graph_parser import GraphParser, GraphValidationError
from app.schemas.dag import (
    DAGEdge,
    DataIngestionNode,
    DataIngestionParams,
    ExecutionNode,
    ExecutionParams,
    IndicatorsNode,
    IndicatorsParams,
    MetaNode,
)


def test_zero_cost_fallacy_trap():
    """TDD: Węzeł Execution musi wymuszać dodatnie fees i slippage."""
    with pytest.raises(ValidationError) as exc_info:
        ExecutionNode(
            id="exec-1",
            type="portfolioNode",
            params=ExecutionParams(init_cash=10000.0, fees=0.0, slippage=0.0)  # Błąd: fees/slippage muszą być > 0
        )
    assert "fees" in str(exc_info.value)


def test_look_ahead_bias_auto_shift_no_time_shift_required():
    """Review 2026-07-16: ochrona przed look-ahead przeniesiona do silnika
    (bezwarunkowy fshift po generate_signals) — graf bez TimeShift jest poprawny."""
    nodes = [
        DataIngestionNode(id="data-1", type="dataNode", params=DataIngestionParams(symbol="BTC", timeframe="1d")),
        IndicatorsNode(id="ind-1", type="indicatorNode", params=IndicatorsParams(windows=[14])),
        ExecutionNode(id="exec-1", type="portfolioNode",
                      params=ExecutionParams(init_cash=10000.0, fees=0.001, slippage=0.001))
    ]
    edges = [
        DAGEdge(id="e1", source="data-1", target="ind-1"),
        DAGEdge(id="e2", source="ind-1", target="exec-1")  # OK: silnik auto-shiftuje sygnały
    ]

    parser = GraphParser(nodes=nodes, edges=edges)
    parser.validate()  # Nie może rzucić


def test_overfitting_trap():
    """TDD: Węzeł Meta (Optymalizator) wymaga węzła Cross-Validation."""
    nodes = [
        DataIngestionNode(id="data-1", type="dataNode", params=DataIngestionParams(symbol="BTC", timeframe="1d")),
        ExecutionNode(id="exec-1", type="portfolioNode",
                      params=ExecutionParams(init_cash=10000.0, fees=0.001, slippage=0.001)),
        MetaNode(id="meta-1", type="optimizerNode", target_nodes=["exec-1"])
    ]
    edges = [DAGEdge(id="e1", source="data-1", target="exec-1")]

    parser = GraphParser(nodes=nodes, edges=edges)
    with pytest.raises(GraphValidationError, match="Overfitting Trap"):
        parser.validate()

# Audyt 2026-07-17: dwa pola kapitału z cichym przesłanianiem — legacy zapis
# z samym initialCapital dostawał domyślne init_cash=10000 (model_dump zawsze
# emituje oba pola, a silnik czyta init_cash w pierwszej kolejności).
def test_execution_params_initial_capital_alias():
    params = ExecutionParams(initialCapital=50000.0)
    assert params.init_cash == 50000.0


def test_execution_params_init_cash_wins_when_both_set():
    params = ExecutionParams(init_cash=7000.0, initialCapital=50000.0)
    assert params.init_cash == 7000.0
