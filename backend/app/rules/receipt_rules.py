from __future__ import annotations

from datetime import date

from .base import BusinessRule, RuleResult


class ContractRuleEngine(BusinessRule):

    name = "Contract Rules"

    def evaluate(self, data: dict) -> RuleResult:
        result = RuleResult()

        start = data.get("start_date")
        end = data.get("end_date")
        parties = data.get("parties")

        if not parties:
            result.add_violation(
                "parties",
                "Contract parties are missing.",
                field="parties",
            )

        if isinstance(start, date) and isinstance(end, date):
            if end < start:
                result.add_violation(
                    "date_range",
                    "Contract end date cannot precede start date.",
                )

        return result