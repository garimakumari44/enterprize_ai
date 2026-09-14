"""
app/nodes/metadata/property_schema.py

Defines schemas for node configuration properties.

These schemas are used by:
- Workflow Builder
- Node Registry
- Validation
- Dynamic Form Generation
- Documentation
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PropertyType(str, Enum):
    """Supported property types."""

    STRING = "string"
    TEXT = "text"
    NUMBER = "number"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"

    PASSWORD = "password"
    SECRET = "secret"

    SELECT = "select"
    MULTI_SELECT = "multi_select"

    JSON = "json"
    ARRAY = "array"
    OBJECT = "object"

    FILE = "file"
    IMAGE = "image"

    MODEL = "model"
    PROMPT = "prompt"

    VARIABLE = "variable"

    CODE = "code"


class PropertyGroup(str, Enum):
    """Logical UI grouping."""

    GENERAL = "general"
    INPUT = "input"
    OUTPUT = "output"
    MODEL = "model"
    ADVANCED = "advanced"
    SECURITY = "security"
    RUNTIME = "runtime"


@dataclass(slots=True)
class PropertyOption:
    """Select option."""

    label: str
    value: Any


@dataclass(slots=True)
class PropertySchema:
    """
    Defines a single configurable property of a workflow node.
    """

    # Identity

    name: str
    label: str

    # Type

    property_type: PropertyType

    # Description

    description: str = ""

    # Validation

    required: bool = False

    default: Any = None

    placeholder: str = ""

    # UI

    group: PropertyGroup = PropertyGroup.GENERAL

    order: int = 0

    hidden: bool = False

    read_only: bool = False

    # Constraints

    minimum: float | None = None
    maximum: float | None = None

    min_length: int | None = None
    max_length: int | None = None

    pattern: str | None = None

    # Select values

    options: list[PropertyOption] = field(default_factory=list)

    # Examples

    examples: list[Any] = field(default_factory=list)

    # Metadata

    metadata: dict[str, Any] = field(default_factory=dict)

    def is_numeric(self) -> bool:
        return self.property_type in {
            PropertyType.NUMBER,
            PropertyType.INTEGER,
            PropertyType.FLOAT,
        }

    def is_select(self) -> bool:
        return self.property_type in {
            PropertyType.SELECT,
            PropertyType.MULTI_SELECT,
        }

    def validate(self, value: Any) -> bool:
        """
        Basic validation.
        """

        if value is None:
            return not self.required

        if self.is_numeric():
            if self.minimum is not None and value < self.minimum:
                return False

            if self.maximum is not None and value > self.maximum:
                return False

        if isinstance(value, str):
            if self.min_length is not None:
                if len(value) < self.min_length:
                    return False

            if self.max_length is not None:
                if len(value) > self.max_length:
                    return False

        return True

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "label": self.label,
            "type": self.property_type.value,
            "description": self.description,
            "required": self.required,
            "default": self.default,
            "placeholder": self.placeholder,
            "group": self.group.value,
            "order": self.order,
            "hidden": self.hidden,
            "read_only": self.read_only,
            "minimum": self.minimum,
            "maximum": self.maximum,
            "min_length": self.min_length,
            "max_length": self.max_length,
            "pattern": self.pattern,
            "options": [
                {
                    "label": option.label,
                    "value": option.value,
                }
                for option in self.options
            ],
            "examples": self.examples,
            "metadata": self.metadata,
        }


@dataclass(slots=True)
class PropertyCollection:
    """
    Collection of node properties.
    """

    properties: list[PropertySchema] = field(default_factory=list)

    def add(self, schema: PropertySchema) -> None:
        self.properties.append(schema)

    def get(self, name: str) -> PropertySchema | None:
        for prop in self.properties:
            if prop.name == name:
                return prop
        return None

    def required(self) -> list[PropertySchema]:
        return [p for p in self.properties if p.required]

    def optional(self) -> list[PropertySchema]:
        return [p for p in self.properties if not p.required]

    def to_dict(self) -> list[dict[str, Any]]:
        return [prop.to_dict() for prop in self.properties]