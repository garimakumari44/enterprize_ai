from typing import Dict, List, Set
from contracts.node  import Node
from contracts.dag import DAG


class DAGBuilder:
    """
    Responsible for constructing and validating a Directed Acyclic Graph.
    """

    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.edges: Dict[str, List[str]] = {}

    def add_node(self, node: Node) -> "DAGBuilder":
        if node.id in self.nodes:
            raise ValueError(f"Node already exists: {node.id}")

        self.nodes[node.id] = node
        self.edges.setdefault(node.id, [])
        return self

    def add_edge(self, from_node: str, to_node: str) -> "DAGBuilder":
        if from_node not in self.nodes or to_node not in self.nodes:
            raise ValueError("Both nodes must exist before adding an edge")

        self.edges[from_node].append(to_node)

        if self._has_cycle():
            self.edges[from_node].pop()
            raise ValueError("Cycle detected in DAG")

        return self

    def build(self) -> DAG:
        return DAG(
            nodes=self.nodes,
            edges=self.edges
        )

    # -------------------------
    # Internal validation logic
    # -------------------------

    def _has_cycle(self) -> bool:
        visited: Set[str] = set()
        rec_stack: Set[str] = set()

        def dfs(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)

            for neighbor in self.edges.get(node_id, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node_id)
            return False

        for node_id in self.nodes:
            if node_id not in visited:
                if dfs(node_id):
                    return True

        return False