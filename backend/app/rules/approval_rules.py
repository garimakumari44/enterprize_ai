from __future__ import annotations

from .base import BusinessRule, RuleResult


class ApprovalRuleEngine(BusinessRule):

    name = "Approval Rules"

    APPROVAL_LIMIT = 10000.0

    def evaluate(self, data: dict) -> RuleResult:
        result = RuleResult()

        amount = data.get("total_amount", 0)
        approved_by = data.get("approved_by")

        if amount > self.APPROVAL_LIMIT and not approved_by:
            result.add_violation(
                "approval",
                (
                    f"Documents above {self.APPROVAL_LIMIT:,.2f} "
                    "require manager approval."
                ),
                severity="warning",
                field="approved_by",
            )

        return result