import pytest

from app.core.utils.graph_parser import GraphParser, GraphValidationError
from app.schemas.dag import (
    BaseNode,
    DAGEdge,
    DataIngestionNode,
    DataIngestionParams,
    ExecutionNode,
    ExecutionParams,
    IndicatorsNode,
    IndicatorsParams,
    LogicOperatorsNode,
    LogicOperatorsParams,
    MetaNode,
)


def make_node(id: str, category: str, target_nodes: list[str] | None = None) -> BaseNode:
    """Factory helper that builds typed DAG nodes based on category string."""
    if category == "DataIngestion":
        return DataIngestionNode(
            id=id, type="dataNode", params=DataIngestionParams(symbol="AAPL", timeframe="1d")
        )
    elif category == "Indicators":
        return IndicatorsNode(id=id, type="indicatorNode", params=IndicatorsParams())
    elif category == "LogicOperators":
        # Audyt 2026-07-17: fabryka odzwierciedla realny eksport frontendu
        # (signalNode = pass-through time_shift); operator "crossover" nie
        # istnieje w palecie i jest odrzucany przez walidator (patrz niżej).
        return LogicOperatorsNode(
            id=id,
            type="signalNode",
            params=LogicOperatorsParams(signalType="sma_crossover", operator_type="time_shift"),
        )
    elif category == "TimeShift":
        return LogicOperatorsNode(
            id=id, type="signalNode", params=LogicOperatorsParams(signalType="fshift", operator_type="time_shift", shift_periods=1)
        )
    elif category == "CrossValidation":
        return LogicOperatorsNode(
            id=id, type="signalNode", params=LogicOperatorsParams(signalType="cv", operator_type="cross_validation")
        )
    elif category == "Execution":
        return ExecutionNode(id=id, type="portfolioNode", params=ExecutionParams(fees=0.001, slippage=0.001))
    elif category == "Meta":
        return MetaNode(id=id, type="optimizerNode", target_nodes=target_nodes or [])
    else:
        raise ValueError(f"Unknown category: {category}")


def make_edge(id: str, source: str, target: str) -> DAGEdge:
    return DAGEdge(id=id, source=source, target=target)


def test_valid_graph():
    nodes = [
        make_node("n1", "DataIngestion"),
        make_node("n2", "Indicators"),
        make_node("n3", "LogicOperators"),
        make_node("ts1", "TimeShift"),
        make_node("cv1", "CrossValidation"),
        make_node("n4", "Execution"),
        make_node("m1", "Meta", target_nodes=["n2", "n3"]),
    ]
    edges = [
        make_edge("e1", "n1", "n2"),
        make_edge("e2", "n2", "n3"),
        make_edge("e3", "n3", "cv1"),
        make_edge("e_cv", "cv1", "ts1"),
        make_edge("e_ts_exec", "ts1", "n4"),
        make_edge("e4", "n1", "n4"),  # DataIngestion -> Execution is valid
    ]
    parser = GraphParser(nodes, edges)
    parser.validate()  # Should not raise


def test_valid_graph_shortcut_indicators_to_execution():
    """3-node flow: Data → Indicator → Execution jest poprawny (review 2026-07-16):
    silnik shiftuje sygnały automatycznie, węzeł TimeShift nie jest już wymagany."""
    nodes = [
        make_node("n1", "DataIngestion"),
        make_node("n2", "Indicators"),
        make_node("n3", "Execution"),
    ]
    edges = [
        make_edge("e1", "n1", "n2"),
        make_edge("e2", "n2", "n3"),  # Indicators -> Execution
    ]
    parser = GraphParser(nodes, edges)
    parser.validate()  # Nie może rzucić — auto-shift w silniku zastępuje wymóg TimeShift


def test_no_execution_node():
    nodes = [
        make_node("n1", "DataIngestion"),
        make_node("n2", "Indicators"),
    ]
    edges = [make_edge("e1", "n1", "n2")]

    with pytest.raises(GraphValidationError, match="exactly one Execution node"):
        GraphParser(nodes, edges).validate()


def test_multiple_execution_nodes():
    nodes = [
        make_node("n1", "DataIngestion"),
        make_node("n2", "Execution"),
        make_node("n3", "Execution"),
    ]
    edges = [
        make_edge("e1", "n1", "n2"),
        make_edge("e2", "n1", "n3"),
    ]
    with pytest.raises(GraphValidationError, match="Maximum one Execution node"):
        GraphParser(nodes, edges).validate()


def test_invalid_connection():
    nodes = [
        make_node("n1", "DataIngestion"),
        make_node("n2", "LogicOperators"),
        make_node("ts", "TimeShift"),
        make_node("n3", "Execution"),
    ]
    edges = [
        make_edge("e1", "n1", "n2"),  # Invalid: DataIngestion -> LogicOperators
        make_edge("e2", "n2", "ts"),
        make_edge("e3", "ts", "n3"),
    ]
    with pytest.raises(
        GraphValidationError, match="Invalid connection: DataIngestion -> LogicOperators"
    ):
        GraphParser(nodes, edges).validate()


def test_meta_edge_connection():
    nodes = [
        make_node("n1", "DataIngestion"),
        make_node("n2", "Execution"),
        make_node("m1", "Meta"),
    ]
    edges = [
        make_edge("e1", "n1", "n2"),
        make_edge("e2", "m1", "n1"),  # Meta cannot be connected via edges
    ]
    with pytest.raises(GraphValidationError, match="Meta nodes cannot be connected via edges"):
        GraphParser(nodes, edges).validate()


def test_invalid_meta_target():
    nodes = [
        make_node("n1", "DataIngestion"),
        make_node("n2", "Execution"),
        make_node("m1", "Meta", target_nodes=["n99"]),  # n99 does not exist
    ]
    edges = [make_edge("e1", "n1", "n2")]

    with pytest.raises(GraphValidationError, match="references non-existent target node: n99"):
        GraphParser(nodes, edges).validate()


def test_circular_dependency():
    nodes = [
        make_node("n1", "DataIngestion"),
        make_node("n2", "Indicators"),
        make_node("n3", "LogicOperators"),
        make_node("ts", "TimeShift"),
        make_node("n4", "Execution"),
    ]
    edges = [
        make_edge("e1", "n1", "n2"),
        make_edge("e2", "n2", "n3"),
        make_edge("e3", "n3", "n2"),  # Cycle: n2 -> n3 -> n2
        make_edge("e_ts", "n3", "ts"),
        make_edge("e4", "ts", "n4"),
    ]
    parser = GraphParser(nodes, edges)
    # Temporarily allow LogicOperators -> Indicators for testing cycle detection
    parser.COMPATIBILITY_MATRIX["LogicOperators"].append("Indicators")
    with pytest.raises(GraphValidationError, match="circular dependencies"):
        parser.validate()


def test_orphan_node():
    nodes = [
        make_node("n1", "DataIngestion"),
        make_node("n2", "Indicators"),  # Orphan, doesn't reach execution
        make_node("n3", "Indicators"),
        make_node("ts", "TimeShift"),
        make_node("n4", "Execution"),
    ]
    edges = [
        make_edge("e1", "n1", "n2"),
        make_edge("e2", "n3", "ts"),
        make_edge("e3", "ts", "n4"),
    ]
    with pytest.raises(
        GraphValidationError, match="is an orphan or cannot reach the Execution node"
    ):
        GraphParser(nodes, edges).validate()


# ---------------------------------------------------------------------------
# Audyt 2026-07-17: silnik wykonuje dokładnie jeden łańcuch
# DataIngestion → Indicators → Execution. Topologie, które silnik by po cichu
# zignorował (drugi wskaźnik, drugie źródło danych, aktywne operatory logiczne),
# muszą być odrzucane na walidacji — inaczej użytkownik dostaje wynik INNEJ
# strategii niż ta, którą zbudował na kanwie.
# ---------------------------------------------------------------------------


def test_multiple_indicators_nodes_rejected():
    nodes = [
        make_node("d1", "DataIngestion"),
        make_node("i1", "Indicators"),
        make_node("i2", "Indicators"),
        make_node("x1", "Execution"),
    ]
    edges = [
        make_edge("e1", "d1", "i1"),
        make_edge("e2", "d1", "i2"),
        make_edge("e3", "i1", "x1"),
        make_edge("e4", "i2", "x1"),
    ]
    with pytest.raises(GraphValidationError, match="jeden węzeł Indicators"):
        GraphParser(nodes, edges).validate()


def test_multiple_data_ingestion_nodes_rejected():
    nodes = [
        make_node("d1", "DataIngestion"),
        make_node("d2", "DataIngestion"),
        make_node("i1", "Indicators"),
        make_node("x1", "Execution"),
    ]
    edges = [
        make_edge("e1", "d1", "i1"),
        make_edge("e2", "i1", "x1"),
        make_edge("e3", "d2", "x1"),
    ]
    with pytest.raises(GraphValidationError, match="jeden węzeł DataIngestion"):
        GraphParser(nodes, edges).validate()


def test_active_logic_operator_rejected():
    """crossover/crossunder/typing_cast deklarują transformację sygnałów,
    której silnik nie wykonuje — cichy no-op byłby fałszywym wynikiem."""
    crossover = LogicOperatorsNode(
        id="op1",
        type="signalNode",
        params=LogicOperatorsParams(operator_type="crossover"),
    )
    nodes = [
        make_node("d1", "DataIngestion"),
        make_node("i1", "Indicators"),
        crossover,
        make_node("x1", "Execution"),
    ]
    edges = [
        make_edge("e1", "d1", "i1"),
        make_edge("e2", "i1", "op1"),
        make_edge("e3", "op1", "x1"),
    ]
    with pytest.raises(GraphValidationError, match="crossover"):
        GraphParser(nodes, edges).validate()


def test_passthrough_logic_operators_allowed():
    """time_shift (no-op, ADR-0007) i cross_validation (marker Overfitting
    Trap) pozostają dozwolone — to udokumentowane pass-through."""
    nodes = [
        make_node("d1", "DataIngestion"),
        make_node("i1", "Indicators"),
        make_node("ts1", "TimeShift"),
        make_node("cv1", "CrossValidation"),
        make_node("x1", "Execution"),
    ]
    edges = [
        make_edge("e1", "d1", "i1"),
        make_edge("e2", "i1", "ts1"),
        make_edge("e3", "ts1", "cv1"),
        make_edge("e4", "cv1", "x1"),
    ]
    GraphParser(nodes, edges).validate()  # nie może rzucić
