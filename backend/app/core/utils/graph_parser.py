
from app.schemas.workflows import WorkflowEdge, WorkflowNode


class GraphValidationError(Exception):
    """Exception raised for errors in the workflow graph validation."""
    pass

class GraphParser:
    COMPATIBILITY_MATRIX = {
        "DataIngestion": ["Indicators", "Execution"],
        "Indicators": ["LogicOperators"],
        "LogicOperators": ["Execution"],
        "Execution": [],
        "Meta": []
    }

    def __init__(self, nodes: list[WorkflowNode], edges: list[WorkflowEdge]):
        self.nodes = {node.id: node for node in nodes}
        self.edges = edges
        self.adj_list = {node_id: [] for node_id in self.nodes}
        self.in_degree = {node_id: 0 for node_id in self.nodes}

        for edge in edges:
            if edge.source not in self.nodes or edge.target not in self.nodes:
                raise GraphValidationError(
                    f"Edge references unknown node: {edge.source} -> {edge.target}"
                )
            self.adj_list[edge.source].append(edge.target)
            self.in_degree[edge.target] += 1

    def validate(self) -> None:
        """Runs all validations on the graph."""
        self._validate_execution_count()
        self._validate_connections()
        self._validate_meta_targets()
        self._validate_no_cycles()
        self._validate_reachability()

    def _validate_execution_count(self) -> None:
        """Max one Execution node per graph."""
        execution_count = sum(
            1 for node in self.nodes.values() if node.data.get("category") == "Execution"
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

            source_category = source_node.data.get("category")
            target_category = target_node.data.get("category")

            if not source_category or not target_category:
                raise GraphValidationError(
                    f"Nodes must have a category in data. "
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
            if node.data.get("category") == "Meta":
                target_nodes = node.data.get("target_nodes", [])
                for target_id in target_nodes:
                    if target_id not in self.nodes:
                        raise GraphValidationError(
                            f"Meta node {node.id} references non-existent target node: {target_id}"
                        )

    def _validate_no_cycles(self) -> None:
        """Cycle Detection using Kahn's algorithm."""
        # We only care about non-meta nodes for cycle detection as meta nodes have no edges
        nodes_to_process = [node_id for node_id, deg in self.in_degree.items() if deg == 0]
        visited_count = 0

        while nodes_to_process:
            current = nodes_to_process.pop(0)
            visited_count += 1

            for neighbor in self.adj_list[current]:
                self.in_degree[neighbor] -= 1
                if self.in_degree[neighbor] == 0:
                    nodes_to_process.append(neighbor)

        if visited_count != len(self.nodes):
            raise GraphValidationError("Graph contains circular dependencies (cycles).")

    def _validate_reachability(self) -> None:
        """No orphan nodes. All paths must eventually reach Execution."""
        # Find the Execution node
        execution_node_id = next(
            node_id for node_id, node in self.nodes.items()
            if node.data.get("category") == "Execution"
        )

        # Reverse adjacency list to find all nodes that can reach Execution
        rev_adj_list = {node_id: [] for node_id in self.nodes}
        for u in self.adj_list:
            for v in self.adj_list[u]:
                rev_adj_list[v].append(u)

        # BFS from Execution node backwards
        reachable = set()
        queue = [execution_node_id]

        while queue:
            current = queue.pop(0)
            if current not in reachable:
                reachable.add(current)
                queue.extend(rev_adj_list[current])

        # Check that all non-Meta nodes are reachable
        for node_id, node in self.nodes.items():
            if node.data.get("category") != "Meta" and node_id not in reachable:
                raise GraphValidationError(
                    f"Node {node_id} is an orphan or cannot reach the Execution node."
                )
