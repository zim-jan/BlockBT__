import pytest

from app.core.utils.graph_parser import GraphParser, GraphValidationError
from app.schemas.workflows import WorkflowEdge, WorkflowNode


def make_node(id: str, category: str, target_nodes: list[str] = None) -> WorkflowNode:
    data = {"category": category}
    if target_nodes is not None:
        data["target_nodes"] = target_nodes
    return WorkflowNode(id=id, type="customNode", position={"x": 0, "y": 0}, data=data)

def make_edge(id: str, source: str, target: str) -> WorkflowEdge:
    return WorkflowEdge(id=id, source=source, target=target)

def test_valid_graph():
    nodes = [
        make_node("n1", "DataIngestion"),
        make_node("n2", "Indicators"),
        make_node("n3", "LogicOperators"),
        make_node("n4", "Execution"),
        make_node("m1", "Meta", target_nodes=["n2", "n3"])
    ]
    edges = [
        make_edge("e1", "n1", "n2"),
        make_edge("e2", "n2", "n3"),
        make_edge("e3", "n3", "n4"),
        make_edge("e4", "n1", "n4")  # DataIngestion -> Execution is valid
    ]
    parser = GraphParser(nodes, edges)
    parser.validate()  # Should not raise

def test_no_execution_node():
    nodes = [
        make_node("n1", "DataIngestion"),
        make_node("n2", "Indicators")
    ]
    edges = [make_edge("e1", "n1", "n2")]

    with pytest.raises(GraphValidationError, match="exactly one Execution node"):
        GraphParser(nodes, edges).validate()

def test_multiple_execution_nodes():
    nodes = [
        make_node("n1", "DataIngestion"),
        make_node("n2", "Execution"),
        make_node("n3", "Execution")
    ]
    edges = [
        make_edge("e1", "n1", "n2"),
        make_edge("e2", "n1", "n3")
    ]
    with pytest.raises(GraphValidationError, match="Maximum one Execution node"):
        GraphParser(nodes, edges).validate()

def test_invalid_connection():
    nodes = [
        make_node("n1", "DataIngestion"),
        make_node("n2", "LogicOperators"),
        make_node("n3", "Execution")
    ]
    edges = [
        make_edge("e1", "n1", "n2"), # Invalid: DataIngestion -> LogicOperators
        make_edge("e2", "n2", "n3")
    ]
    with pytest.raises(
        GraphValidationError, match="Invalid connection: DataIngestion -> LogicOperators"
    ):
        GraphParser(nodes, edges).validate()

def test_meta_edge_connection():
    nodes = [
        make_node("n1", "DataIngestion"),
        make_node("n2", "Execution"),
        make_node("m1", "Meta")
    ]
    edges = [
        make_edge("e1", "n1", "n2"),
        make_edge("e2", "m1", "n1") # Meta cannot be connected via edges
    ]
    with pytest.raises(GraphValidationError, match="Meta nodes cannot be connected via edges"):
        GraphParser(nodes, edges).validate()

def test_invalid_meta_target():
    nodes = [
        make_node("n1", "DataIngestion"),
        make_node("n2", "Execution"),
        make_node("m1", "Meta", target_nodes=["n99"]) # n99 does not exist
    ]
    edges = [make_edge("e1", "n1", "n2")]

    with pytest.raises(GraphValidationError, match="references non-existent target node: n99"):
        GraphParser(nodes, edges).validate()

def test_circular_dependency():
    nodes = [
        make_node("n1", "DataIngestion"),
        make_node("n2", "Indicators"),
        make_node("n3", "LogicOperators"),
        make_node("n4", "Execution")
    ]
    edges = [
        make_edge("e1", "n1", "n2"),
        make_edge("e2", "n2", "n3"),
        make_edge("e3", "n3", "n2"), # Cycle: n2 -> n3 -> n2
        make_edge("e4", "n3", "n4")
    ]
    parser = GraphParser(nodes, edges)
    # Mock COMPATIBILITY_MATRIX to allow LogicOperators -> Indicators for testing cycle detection
    parser.COMPATIBILITY_MATRIX["LogicOperators"].append("Indicators")
    with pytest.raises(GraphValidationError, match="circular dependencies"):
        parser.validate()

def test_orphan_node():
    nodes = [
        make_node("n1", "DataIngestion"),
        make_node("n2", "Indicators"), # Orphan, doesn't reach execution
        make_node("n3", "DataIngestion"),
        make_node("n4", "Execution")
    ]
    edges = [
        make_edge("e1", "n1", "n2"),
        make_edge("e2", "n3", "n4")
    ]
    with pytest.raises(
        GraphValidationError, match="is an orphan or cannot reach the Execution node"
    ):
        GraphParser(nodes, edges).validate()
