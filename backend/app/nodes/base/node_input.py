"""
Base input model for workflow nodes.

NodeInput represents the input supplied to a single node execution.
It contains the primary payload, node parameters, and a reference
to the shared execution context.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.nodes.base.node_context import NodeContext


@dataclass(slots=True)
class NodeInput:
    """
    Input passed to a workflow node.

    Attributes:
        data:
            Primary input payload.

        context:
            Shared workflow execution context.

        parameters:
            Static configuration for this node instance.

        metadata:
            Node-specific execution metadata.

        previous_output:
            Output from the previous node (if available).
    """

    data: Any = None

    context: NodeContext | None = None

    parameters: dict[str, Any] = field(default_factory=dict)

    metadata: dict[str, Any] = field(default_factory=dict)

    previous_output: Any = None

    # ------------------------------------------------------------------
    # Parameters
    # ------------------------------------------------------------------

    def get_parameter(self, name: str, default: Any = None) -> Any:
        """Retrieve a node parameter."""
        return self.parameters.get(name, default)

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    def get_metadata(self, name: str, default: Any = None) -> Any:
        """Retrieve execution metadata."""
        return self.metadata.get(name, default)

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Serialize the input."""
        return {
            "data": self.data,
            "parameters": self.parameters,
            "metadata": self.metadata,
            "previous_output": self.previous_output,
            "context": (
                self.context.to_dict()
                if self.context is not None
                else None
            ),
        }