from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.costs.models.usage_cost import UsageCost
from app.costs.repositories.cost_repository import CostRepository


class TokenCostService:
    """
    Business logic for token pricing and cost calculation.
    """

    def __init__(self, db: Session):
        self.repository = CostRepository(db)

    # ---------------------------------------------------------
    # Pricing
    # ---------------------------------------------------------

    @staticmethod
    def calculate_cost(
        prompt_tokens: int,
        completion_tokens: int,
        input_price_per_1k: Decimal,
        output_price_per_1k: Decimal,
    ) -> Decimal:
        """
        Calculate total token cost.

        Formula:
            (prompt_tokens / 1000) * input_price
          + (completion_tokens / 1000) * output_price
        """

        input_cost = (
            Decimal(prompt_tokens) / Decimal("1000")
        ) * input_price_per_1k

        output_cost = (
            Decimal(completion_tokens) / Decimal("1000")
        ) * output_price_per_1k

        return (input_cost + output_cost).quantize(Decimal("0.000001"))

    # ---------------------------------------------------------
    # Recording
    # ---------------------------------------------------------

    def create_usage_record(
        self,
        *,
        workflow_id: Optional[int],
        execution_id: Optional[int],
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        input_price_per_1k: Decimal,
        output_price_per_1k: Decimal,
    ) -> UsageCost:
        """
        Create a cost record after LLM execution.
        """

        total_tokens = prompt_tokens + completion_tokens

        total_cost = self.calculate_cost(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            input_price_per_1k=input_price_per_1k,
            output_price_per_1k=output_price_per_1k,
        )

        usage = UsageCost(
            workflow_id=workflow_id,
            execution_id=execution_id,
            provider=provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            total_cost=total_cost,
        )

        return self.repository.create(usage)

    # ---------------------------------------------------------
    # Queries
    # ---------------------------------------------------------

    def get(self, cost_id: int):
        return self.repository.get(cost_id)

    def list(self, skip: int = 0, limit: int = 100):
        return self.repository.list(skip, limit)

    def by_execution(self, execution_id: int):
        return self.repository.get_by_execution(execution_id)

    def by_workflow(self, workflow_id: int):
        return self.repository.get_by_workflow(workflow_id)

    # ---------------------------------------------------------
    # Statistics
    # ---------------------------------------------------------

    def total_cost(self) -> Decimal:
        return self.repository.total_cost()

    def total_tokens(self) -> int:
        return self.repository.total_tokens()

    def provider_cost(self, provider: str) -> Decimal:
        return self.repository.provider_cost(provider)

    def workflow_cost(self, workflow_id: int) -> Decimal:
        return self.repository.workflow_cost(workflow_id)

    def execution_cost(self, execution_id: int) -> Decimal:
        return self.repository.execution_cost(execution_id)