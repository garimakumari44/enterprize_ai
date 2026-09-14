"""
Registry for workflow node classes.

The NodeRegistry stores all available workflow node classes and allows
the workflow engine to look them up by node type.
"""

from __future__ import annotations

from typing import Type

from app.nodes.base.base_node import BaseNode


class NodeRegistry:
    """
    Registry for workflow node classes.

    Example:
        registry.register("chat", ChatNode)
        registry.register("ocr", OCRNode)

        node_cls = registry.get("chat")
    """

    def __init__(self) -> None:
        self._nodes: dict[str, Type[BaseNode]] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(
        self,
        node_type: str,
        node_class: Type[BaseNode],
    ) -> None:
        """
        Register a workflow node class.

        Raises:
            ValueError:
                If the node type is already registered.
        """
        key = node_type.lower().strip()

        if key in self._nodes:
            raise ValueError(
                f"Node type '{node_type}' is already registered."
            )

        self._nodes[key] = node_class

    def unregister(self, node_type: str) -> None:
        """Remove a registered node."""
        self._nodes.pop(node_type.lower().strip(), None)

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def get(self, node_type: str) -> Type[BaseNode]:
        """
        Retrieve a registered node class.

        Raises:
            KeyError:
                If the node type is not registered.
        """
        key = node_type.lower().strip()

        if key not in self._nodes:
            raise KeyError(
                f"Node type '{node_type}' is not registered."
            )

        return self._nodes[key]

    def exists(self, node_type: str) -> bool:
        """Return True if a node type is registered."""
        return node_type.lower().strip() in self._nodes

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------

    def list_node_types(self) -> list[str]:
        """Return all registered node types."""
        return sorted(self._nodes.keys())

    def list_node_classes(self) -> dict[str, Type[BaseNode]]:
        """Return a copy of the registry."""
        return dict(self._nodes)

    def clear(self) -> None:
        """Remove all registered nodes."""
        self._nodes.clear()

    def __len__(self) -> int:
        return len(self._nodes)

    def __contains__(self, node_type: str) -> bool:
        return self.exists(node_type)


# ----------------------------------------------------------------------
# Global Registry
# ----------------------------------------------------------------------

node_registry = NodeRegistry()


# ----------------------------------------------------------------------
# Decorator
# ----------------------------------------------------------------------

def register_node(node_type: str):
    """
    Decorator for automatic node registration.

    Example:

        @register_node("chat")
        class ChatNode(BaseNode):
            ...
    """

    def decorator(node_class: Type[BaseNode]) -> Type[BaseNode]:
        node_registry.register(node_type, node_class)
        return node_class

    return decorator