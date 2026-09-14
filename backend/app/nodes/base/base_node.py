"""
Base input models for workflow nodes.

Every node receives a NodeInput instance containing:
- input data
- execution metadata
- runtime variables
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class NodeInput:
    """
    Standard input passed to every node.

    Attributes:
        data:
            Primary input payload.

        variables:
            Workflow variables available to this node.

        metadata:
            Extra runtime metadata.

        previous_output:
            Output from the previous node (if any).
    """

    data: Any = None

    variables: dict[str, Any] = field(default_factory=dict)

    metadata: dict[str, Any] = field(default_factory=dict)

    previous_output: Any = None

    def get(self, key: str, default: Any = None) -> Any:
        """Shortcut for reading variables."""
        return self.variables.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Store a workflow variable."""
        self.variables[key] = value