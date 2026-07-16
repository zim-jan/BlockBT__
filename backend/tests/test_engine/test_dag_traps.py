import pytest
from pydantic import ValidationError
from app.schemas.dag import (
    DataIngestionNode, IndicatorsNode, LogicOperatorsNode,
    ExecutionNode, MetaNode, DAGEdge, DataIngestionParams,
    IndicatorsParams, LogicOperatorsParams, ExecutionParams
)
from app.core.utils.graph_parser import GraphParser, GraphValidationError


def test_zero_cost_fallacy_trap():
    """TDD: Węzeł Execution musi wymuszać dodatnie fees i slippage."""
    with pytest.raises(ValidationError) as exc_info:
        ExecutionNode(
            id="exec-1",
            type="portfolioNode",
            params=ExecutionParams(init_cash=10000.0, fees=0.0, slippage=0.0)  # Błąd: fees/slippage muszą być > 0
        )
    assert "fees" in str(exc_info.value)


def test_look_ahead_bias_trap():
    """TDD: Węzeł Execution musi być poprzedzony węzłem TimeShift."""
    nodes = [
        DataIngestionNode(id="data-1", type="dataNode", params=DataIngestionParams(symbol="BTC", timeframe="1d")),
        IndicatorsNode(id="ind-1", type="indicatorNode", params=IndicatorsParams(windows=[14])),
        ExecutionNode(id="exec-1", type="portfolioNode",
                      params=ExecutionParams(init_cash=10000.0, fees=0.001, slippage=0.001))
    ]
    edges = [
        DAGEdge(id="e1", source="data-1", target="ind-1"),
        DAGEdge(id="e2", source="ind-1", target="exec-1")  # Błąd: Brak TimeShift pomiędzy ind-1 a exec-1
    ]

    parser = GraphParser(nodes=nodes, edges=edges)
    with pytest.raises(GraphValidationError, match="Look-ahead Bias"):
        parser.validate()


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