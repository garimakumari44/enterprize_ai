"""
Graph Traverser.

Determines the next node(s) to execute
based on workflow edges.
"""

from typing import Dict, List, Optional, Any


class GraphTraverser:
    """
    Traverses workflow graphs.
    """

    def __init__(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
    ) -> None:
        self.nodes = {node["id"]: node for node in nodes}
        self.edges = edges

    def get_node(
        self,
        node_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Return a node by ID.
        """

        return self.nodes.get(node_id)

    def get_start_node(self) -> Optional[Dict[str, Any]]:
        """
        Find the workflow start node.
        """

        for node in self.nodes.values():
            if node.get("type") == "start":
                return node

        return None

    def get_next_nodes(
        self,
        current_node_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Return all connected downstream nodes.
        """

        next_nodes = []

        for edge in self.edges:
            if edge["source"] == current_node_id:
                node = self.get_node(edge["target"])

                if node:
                    next_nodes.append(node)

        return next_nodes

    def get_next_node(
        self,
        current_node_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Return the first downstream node.

        Useful for simple sequential workflows.
        """

        nodes = self.get_next_nodes(current_node_id)

        if nodes:
            return nodes[0]

        return None

    def get_condition_node(
        self,
        current_node_id: str,
        condition: bool,
    ) -> Optional[Dict[str, Any]]:
        """
        Resolve the next node after a condition.

        Edges should contain labels:
        - true
        - false
        """

        expected = "true" if condition else "false"

        for edge in self.edges:
            if edge["source"] != current_node_id:
                continue

            if edge.get("label") == expected:
                return self.get_node(edge["target"])

        return None

    def is_terminal(
        self,
        node_id: str,
    ) -> bool:
        """
        Returns True if the node has no outgoing edges.
        """

        return not any(
            edge["source"] == node_id
            for edge in self.edges
        )