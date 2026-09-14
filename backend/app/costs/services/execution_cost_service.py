from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.costs.repositories.cost_repository import CostRepository
from app.costs.models.usage_cost import UsageCost


class ExecutionCostService:
    """
    Handles compute/runtime costs for workflow executions.
    """

    def __init__(self, db: Session):
        self.repository = CostRepository(db)

    @staticmethod
    def calculate_execution_cost(
        duration_seconds: float,
        hourly_rate: Decimal,
    ) -> Decimal:
        """
        Calculates execution cost.

        Formula:
            (seconds / 3600) * hourly_rate
        """

        hours = Decimal(str(duration_seconds)) / Decimal("3600")

        return (hours * hourly_rate).quantize(
            Decimal("0.000001")
        )

    def record_execution_cost(
        self,
        *,
        workflow_id: Optional[int],
        execution_id: int,
        provider: str,
        model: str,
        duration_seconds: float,
        hourly_rate: Decimal,
    ) -> UsageCost:

        cost = self.calculate_execution_cost(
            duration_seconds,
            hourly_rate,
        )

        usage = UsageCost(
            workflow_id=workflow_id,
            execution_id=execution_id,
            provider=provider,
            model=model,
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            total_cost=cost,
        )

        return self.repository.create(usage)

    def execution_cost(self, execution_id: int):
        return self.repository.execution_cost(execution_id)

    def workflow_cost(self, workflow_id: int):
        return self.repository.workflow_cost(workflow_id)