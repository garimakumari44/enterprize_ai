"""
app/nodes/metadata/node_metadata.py

Metadata definition for workflow nodes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.nodes.metadata.node_categories import NodeCategory


@dataclass(slots=True)
class NodeMetadata:
    """
    Describes a workflow node.

    This metadata is used by:
    - Node Registry
    - Workflow Builder
    - Node Search
    - Documentation
    - Validation
    """

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    node_type: str
    name: str
    category: NodeCategory
    version: str = "1.0.0"

    # ------------------------------------------------------------------
    # Description
    # ------------------------------------------------------------------

    description: str = ""
    tags: list[str] = field(default_factory=list)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    icon: str = "Box"
    color: str = "#64748B"

    # ------------------------------------------------------------------
    # Ports
    # ------------------------------------------------------------------

    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    configurable: bool = True
    properties: dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Runtime
    # ------------------------------------------------------------------

    supports_streaming: bool = False
    supports_batch: bool = False
    supports_parallel: bool = False

    # ------------------------------------------------------------------
    # Documentation
    # ------------------------------------------------------------------

    documentation_url: str | None = None
    examples: list[str] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Visibility
    # ------------------------------------------------------------------

    enabled: bool = True
    experimental: bool = False
    deprecated: bool = False

    # ------------------------------------------------------------------
    # Methods
    # ------------------------------------------------------------------

    @property
    def display_name(self) -> str:
        """Display name for UI."""
        return self.name

    @property
    def searchable_text(self) -> str:
        """Combined searchable text."""
        return " ".join(
            [
                self.name,
                self.description,
                self.category.value,
                *self.tags,
            ]
        ).lower()

    def supports(self, feature: str) -> bool:
        """
        Check whether a runtime feature is supported.

        Example:
            metadata.supports("streaming")
        """
        feature = feature.lower()

        return {
            "streaming": self.supports_streaming,
            "batch": self.supports_batch,
            "parallel": self.supports_parallel,
        }.get(feature, False)

    def to_dict(self) -> dict[str, Any]:
        """Serialize metadata into a dictionary."""
        return {
            "node_type": self.node_type,
            "name": self.name,
            "category": self.category.value,
            "version": self.version,
            "description": self.description,
            "tags": self.tags,
            "icon": self.icon,
            "color": self.color,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "configurable": self.configurable,
            "properties": self.properties,
            "supports_streaming": self.supports_streaming,
            "supports_batch": self.supports_batch,
            "supports_parallel": self.supports_parallel,
            "documentation_url": self.documentation_url,
            "examples": self.examples,
            "enabled": self.enabled,
            "experimental": self.experimental,
            "deprecated": self.deprecated,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NodeMetadata":
        """Create metadata from a dictionary."""
        return cls(
            node_type=data["node_type"],
            name=data["name"],
            category=NodeCategory(data["category"]),
            version=data.get("version", "1.0.0"),
            description=data.get("description", ""),
            tags=data.get("tags", []),
            icon=data.get("icon", "Box"),
            color=data.get("color", "#64748B"),
            inputs=data.get("inputs", []),
            outputs=data.get("outputs", []),
            configurable=data.get("configurable", True),
            properties=data.get("properties", {}),
            supports_streaming=data.get("supports_streaming", False),
            supports_batch=data.get("supports_batch", False),
            supports_parallel=data.get("supports_parallel", False),
            documentation_url=data.get("documentation_url"),
            examples=data.get("examples", []),
            enabled=data.get("enabled", True),
            experimental=data.get("experimental", False),
            deprecated=data.get("deprecated", False),
        )