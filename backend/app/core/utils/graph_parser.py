
from app.schemas.dag import BaseNode, DAGEdge


class GraphValidationError(Exception):
    """Exception raised for errors in the workflow graph validation."""
    pass

class GraphParser:
    COMPATIBILITY_MATRIX = {
        "DataIngestion": ["Indicators", "Execution"],
        "Indicators": ["LogicOperators", "Execution"],
        "LogicOperators": ["LogicOperators", "Execution"],
        "Execution": [],
        "Meta": []
    }

    def __init__(self, nodes: list[BaseNode], edges: list[DAGEdge]):
        self.nodes = {node.id: node for node in nodes}
        self.edges = edges
        self.adj_list: dict[str, list[str]] = {node_id: [] for node_id in self.nodes}
        self.in_degree: dict[str, int] = {node_id: 0 for node_id in self.nodes}

        for edge in edges:
            if edge.source not in self.nodes or edge.target not in self.nodes:
                raise GraphValidationError(
                    f"Edge references unknown node: {edge.source} -> {edge.target}"
                )
            self.adj_list[edge.source].append(edge.target)
            self.in_degree[edge.target] += 1

    # Audyt 2026-07-17: operatory deklarujące transformację sygnałów, której
    # silnik (run_dag_backtest) nie wykonuje — cichy no-op dawałby wynik innej
    # strategii niż zbudowana. Pass-through pozostają: time_shift (no-op,
    # ADR-0007) i cross_validation (marker walidatora dla Overfitting Trap).
    _UNSUPPORTED_OPERATORS = frozenset({"crossover", "crossunder", "typing_cast"})

    def validate(self) -> None:
        """Runs all validations on the graph."""
        self._validate_execution_count()
        self._validate_connections()
        self._validate_meta_targets()
        self._validate_no_cycles()
        self._validate_reachability()
        self._validate_financial_traps()
        self._validate_supported_topology()

    def _validate_execution_count(self) -> None:
        """Max one Execution node per graph."""
        execution_count = sum(
            1 for node in self.nodes.values() if node.category == "Execution"
        )
        if execution_count > 1:
            raise GraphValidationError(
                f"Maximum one Execution node allowed. Found {execution_count}."
            )
        if execution_count == 0:
            raise GraphValidationError("Graph must have exactly one Execution node.")

    def _validate_connections(self) -> None:
        """Validate connections using the Compatibility Matrix."""
        for edge in self.edges:
            source_node = self.nodes[edge.source]
            target_node = self.nodes[edge.target]

            source_category = source_node.category
            target_category = target_node.category

            if not source_category or not target_category:
                raise GraphValidationError(
                    f"Nodes must have a category. "
                    f"Missing for {source_node.id} or {target_node.id}."
                )

            if source_category == "Meta" or target_category == "Meta":
                raise GraphValidationError("Meta nodes cannot be connected via edges.")

            allowed_targets = self.COMPATIBILITY_MATRIX.get(source_category, [])
            if target_category not in allowed_targets:
                raise GraphValidationError(
                    f"Invalid connection: {source_category} -> {target_category}"
                )

    def _validate_meta_targets(self) -> None:
        """Meta target_nodes IDs must exist in main nodes list."""
        for node in self.nodes.values():
            if node.category == "Meta":
                target_nodes = getattr(node, 'target_nodes', [])
                for target_id in target_nodes:
                    if target_id not in self.nodes:
                        raise GraphValidationError(
                            f"Meta node {node.id} references non-existent target node: {target_id}"
                        )

    def _validate_no_cycles(self) -> None:
        """Cycle Detection using Kahn's algorithm."""
        # Work on a copy to avoid mutating state
        in_degree = dict(self.in_degree)
        nodes_to_process = [node_id for node_id, deg in in_degree.items() if deg == 0]
        visited_count = 0

        while nodes_to_process:
            current = nodes_to_process.pop(0)
            visited_count += 1

            for neighbor in self.adj_list[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    nodes_to_process.append(neighbor)

        if visited_count != len(self.nodes):
            raise GraphValidationError("Graph contains circular dependencies (cycles).")

    def _validate_reachability(self) -> None:
        """No orphan nodes. All paths must eventually reach Execution."""
        # Find the Execution node
        execution_node_id = next(
            node_id for node_id, node in self.nodes.items()
            if node.category == "Execution"
        )

        # Reverse adjacency list to find all nodes that can reach Execution
        rev_adj_list: dict[str, list[str]] = {node_id: [] for node_id in self.nodes}
        for u in self.adj_list:
            for v in self.adj_list[u]:
                rev_adj_list[v].append(u)

        # BFS from Execution node backwards
        reachable: set[str] = set()
        queue = [execution_node_id]

        while queue:
            current = queue.pop(0)
            if current not in reachable:
                reachable.add(current)
                queue.extend(rev_adj_list[current])

        # Check that all non-Meta nodes are reachable
        for node_id, node in self.nodes.items():
            if node.category != "Meta" and node_id not in reachable:
                raise GraphValidationError(
                    f"Node {node_id} is an orphan or cannot reach the Execution node."
                )

    def _validate_financial_traps(self) -> None:
        """Wymusza zasady inżynierii finansowej (Prewencja Pułapek)."""
        # 1. Overfitting Trap: Meta Node wymaga Cross-Validation Node
        has_meta = any(node.category == "Meta" for node in self.nodes.values())
        has_cv = any(
            node.category == "LogicOperators" and getattr(node.params, "operator_type", "") == "cross_validation"
            for node in self.nodes.values()
        )
        if has_meta and not has_cv:
            raise GraphValidationError("Overfitting Trap: Optymalizacja (Meta Node) wymaga węzła Cross-Validation.")

        # 2. Look-ahead Bias (review 2026-07-16): wymóg jawnego węzła TimeShift
        # usunięty — ochrona przeniesiona do silnika, który bezwarunkowo
        # przesuwa entries/exits o 1 okres (OpenSourceEngine.run_dag_backtest).

    def _validate_supported_topology(self) -> None:
        """Odrzuca topologie, których silnik nie wykonuje (audyt 2026-07-17).

        ``run_dag_backtest`` wykonuje dokładnie jeden łańcuch
        DataIngestion → Indicators → Execution (węzły LogicOperators są
        pass-through). Wcześniej drugi wskaźnik, drugie źródło danych czy
        aktywny operator logiczny były po cichu ignorowane — użytkownik
        dostawał wynik INNEJ strategii niż zbudowana na kanwie.
        """
        data_count = sum(1 for n in self.nodes.values() if n.category == "DataIngestion")
        if data_count > 1:
            raise GraphValidationError(
                f"Nieobsługiwana topologia: silnik wykonuje dokładnie jeden węzeł DataIngestion "
                f"(znaleziono {data_count}). Wiele tickerów podaje się listą w polu symbol "
                f"jednego węzła Data."
            )

        indicators_count = sum(1 for n in self.nodes.values() if n.category == "Indicators")
        if indicators_count > 1:
            raise GraphValidationError(
                f"Nieobsługiwana topologia: silnik wykonuje dokładnie jeden węzeł Indicators "
                f"(znaleziono {indicators_count}) — łączenie sygnałów wielu wskaźników nie jest "
                f"jeszcze wspierane."
            )

        for node in self.nodes.values():
            if node.category != "LogicOperators":
                continue
            operator = getattr(node.params, "operator_type", None)
            if operator in self._UNSUPPORTED_OPERATORS:
                raise GraphValidationError(
                    f"Nieobsługiwany operator logiczny {operator!r} (węzeł {node.id}): "
                    f"silnik nie wykonuje tej operacji — węzeł zostałby po cichu zignorowany, "
                    f"a wynik nie odpowiadałby zbudowanej strategii."
                )