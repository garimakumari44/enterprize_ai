"""
Factory for creating workflow node instances.

The NodeFactory uses the NodeRegistry to locate registered node
classes and instantiate them with the supplied configuration.
"""

from __future__ import annotations

from typing import Any

from app.nodes.base.base_node import BaseNode
from app.nodes.registry.node_registry import NodeRegistry, node_registry


class NodeFactory:
    """
    Factory for creating workflow node instances.
    """

    def __init__(self, registry: NodeRegistry | None = None) -> None:
        self._registry = registry or node_registry

    # ------------------------------------------------------------------
    # Creation
    # ------------------------------------------------------------------

    def create(
        self,
        node_type: str,
        *,
        node_id: str,
        name: str | None = None,
        config: dict[str, Any] | None = None,
    ) -> BaseNode:
        """
        Create a node instance.

        Args:
            node_type:
                Registered node type.

            node_id:
                Unique workflow node identifier.

            name:
                Optional display name.

            config:
                Node configuration.

        Raises:
            KeyError:
                If the node type is not registered.
        """

        node_class = self._registry.get(node_type)

        return node_class(
            node_id=node_id,
            name=name or node_type,
            config=config or {},
        )

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def supports(self, node_type: str) -> bool:
        """Return True if a node type is registered."""
        return self._registry.exists(node_type)

    def available_nodes(self) -> list[str]:
        """Return all available node types."""
        return self._registry.list_node_types()


# ----------------------------------------------------------------------
# Global Factory
# ----------------------------------------------------------------------

node_factory = NodeFactory()