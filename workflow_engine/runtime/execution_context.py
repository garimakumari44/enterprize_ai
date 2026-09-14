from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from datetime import datetime
import uuid


@dataclass
class ExecutionContext:
    """
    Shared runtime context passed between workflow nodes.

    Stores:
    - workflow metadata
    - execution metadata
    - shared variables
    - node outputs
    """

    execution_id: str = field(
        default_factory=lambda: str(uuid.uuid4())
    )

    workflow_id: Optional[str] = None

    started_at: datetime = field(
        default_factory=datetime.utcnow
    )

    variables: Dict[str, Any] = field(
        default_factory=dict
    )

    outputs: Dict[str, Any] = field(
        default_factory=dict
    )

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    errors: Dict[str, str] = field(
        default_factory=dict
    )

    # -------------------------
    # Variables
    # -------------------------

    def set(self, key: str, value: Any) -> None:
        self.variables[key] = value

    def get(
        self,
        key: str,
        default: Any = None
    ) -> Any:
        return self.variables.get(key, default)

    # -------------------------
    # Outputs
    # -------------------------

    def set_output(
        self,
        node_id: str,
        output: Any
    ) -> None:
        self.outputs[node_id] = output

    def get_output(
        self,
        node_id: str
    ) -> Any:
        return self.outputs.get(node_id)

    # -------------------------
    # Errors
    # -------------------------

    def add_error(
        self,
        node_id: str,
        error: str
    ) -> None:
        self.errors[node_id] = error

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    # -------------------------
    # Metadata
    # -------------------------

    def update_metadata(
        self,
        key: str,
        value: Any
    ) -> None:
        self.metadata[key] = value

    def get_metadata(
        self,
        key: str,
        default: Any = None
    ) -> Any:
        return self.metadata.get(key, default)