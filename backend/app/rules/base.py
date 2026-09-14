from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class RuleViolation:
    rule: str
    message: str
    severity: str = "error"
    field: str | None = None


@dataclass(slots=True)
class RuleResult:
    passed: bool = True
    violations: list[RuleViolation] = field(default_factory=list)

    def add_violation(
        self,
        rule: str,
        message: str,
        severity: str = "error",
        field: str | None = None,
    ) -> None:
        self.passed = False
        self.violations.append(
            RuleViolation(
                rule=rule,
                message=message,
                severity=severity,
                field=field,
            )
        )


class BusinessRule(ABC):
    """
    Base class for every business rule.
    """

    name: str = "Unnamed Rule"

    @abstractmethod
    def evaluate(self, data: dict[str, Any]) -> RuleResult:
        raise NotImplementedError