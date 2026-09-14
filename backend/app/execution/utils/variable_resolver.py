"""
Variable Resolver

Replaces template variables in node configurations using
the current execution context.

Example:
    "{{user_id}}" -> 123
"""

from __future__ import annotations

import re
from typing import Any


VARIABLE_PATTERN = re.compile(r"\{\{\s*([a-zA-Z0-9_.-]+)\s*\}\}")


class VariableResolver:
    """
    Resolves {{variables}} from the execution context.

    Supports:
    - strings
    - dicts
    - lists
    - nested objects
    """

    @classmethod
    def resolve(cls, value: Any, context: dict[str, Any]) -> Any:
        """
        Resolve variables recursively.

        Args:
            value: Value to resolve.
            context: Execution context variables.

        Returns:
            Resolved value.
        """

        if isinstance(value, str):
            return cls._resolve_string(value, context)

        if isinstance(value, dict):
            return {
                key: cls.resolve(val, context)
                for key, val in value.items()
            }

        if isinstance(value, list):
            return [
                cls.resolve(item, context)
                for item in value
            ]

        return value

    @classmethod
    def _resolve_string(cls, text: str, context: dict[str, Any]) -> Any:
        """
        Resolve variables inside a string.

        If the entire string is a single variable,
        return the actual object instead of a string.

        Example:
            "{{count}}" -> 10 (int)
            "{{data}}" -> dict
        """

        match = VARIABLE_PATTERN.fullmatch(text)

        # Entire string is a variable
        if match:
            return cls._lookup(context, match.group(1))

        # Partial replacement
        def replace(match: re.Match) -> str:
            value = cls._lookup(context, match.group(1))
            return "" if value is None else str(value)

        return VARIABLE_PATTERN.sub(replace, text)

    @staticmethod
    def _lookup(context: dict[str, Any], path: str) -> Any:
        """
        Lookup nested variables using dot notation.

        Example:
            user.id
            workflow.name
            outputs.http.response
        """

        current: Any = context

        for part in path.split("."):
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None

            if current is None:
                return None

        return current