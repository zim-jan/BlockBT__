import pytest
from pydantic import ValidationError

from app.schemas.dag import (
    DAGEdge,
    DAGGraph,
    DataIngestionNode,
    ExecutionNode,
    IndicatorsNode,
    LogicOperatorsNode,
    MetaNode,
)


def test_data_ingestion_node():
    data = {
        "id": "1",
        "type": "dataSource",
        "category": "DataIngestion",
        "params": {"symbol": "BTC/USD", "timeframe": "1d"}
    }
    node = DataIngestionNode(**data)
    assert node.id == "1"
    assert node.category == "DataIngestion"
    assert node.params.symbol == "BTC/USD"
    assert node.params.timeframe == "1d"

def test_data_ingestion_missing_params():
    data = {
        "id": "1",
        "type": "dataSource",
        "category": "DataIngestion",
        "params": {"symbol": "BTC/USD"}  # missing timeframe
    }
    with pytest.raises(ValidationError):
        DataIngestionNode(**data)

def test_indicators_node_defaults():
    data = {
        "id": "2",
        "type": "indicator",
        "category": "Indicators"
    }
    node = IndicatorsNode(**data)
    assert node.params.windows == [14]

def test_logic_operators_node():
    data = {
        "id": "3",
        "type": "logic",
        "category": "LogicOperators",
        "params": {"condition": "a > b"}
    }
    node = LogicOperatorsNode(**data)
    assert node.params.condition == "a > b"

def test_execution_node_defaults():
    data = {
        "id": "4",
        "type": "execution",
        "category": "Execution"
    }
    node = ExecutionNode(**data)
    assert node.params.init_cash == 10000.0

def test_meta_node():
    data = {
        "id": "5",
        "type": "meta",
        "category": "Meta",
        "target_nodes": ["1", "2"],
        "params": {"inject_var": True}
    }
    node = MetaNode(**data)
    assert node.target_nodes == ["1", "2"]
    assert node.params["inject_var"] is True

def test_dag_edge():
    data = {
        "id": "e1",
        "source": "1",
        "target": "2",
        "sourceHandle": "out",
        "targetHandle": "in"
    }
    edge = DAGEdge(**data)
    assert edge.sourceHandle == "out"

def test_dag_graph_polymorphism():
    data = {
        "nodes": [
            {
                "id": "n1",
                "type": "dataSource",
                "category": "DataIngestion",
                "params": {"symbol": "BTC/USD", "timeframe": "1d"}
            },
            {
                "id": "n2",
                "type": "logic",
                "category": "LogicOperators",
                "params": {"condition": "a > b"}
            }
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n2"}
        ],
        "meta_nodes": [
            {
                "id": "m1",
                "type": "meta",
                "category": "Meta",
                "target_nodes": ["n1"],
                "params": {}
            }
        ]
    }

    graph = DAGGraph(**data)
    assert len(graph.nodes) == 2
    assert isinstance(graph.nodes[0], DataIngestionNode)
    assert isinstance(graph.nodes[1], LogicOperatorsNode)
    assert len(graph.edges) == 1
    assert len(graph.meta_nodes) == 1

def test_dag_graph_allows_cycles():
    data = {
        "nodes": [
            {
                "id": "n1",
                "type": "logic",
                "category": "LogicOperators",
                "params": {"condition": "a > b"}
            },
            {
                "id": "n2",
                "type": "logic",
                "category": "LogicOperators",
                "params": {"condition": "b > a"}
            }
        ],
        "edges": [
            {"id": "e1", "source": "n1", "target": "n2"},
            {"id": "e2", "source": "n2", "target": "n1"}  # cycle!
        ]
    }

    # Should not raise any validation error due to cyclic graphs
    graph = DAGGraph(**data)
    assert len(graph.edges) == 2
