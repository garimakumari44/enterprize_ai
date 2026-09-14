from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.costs.repositories.cost_repository import CostRepository
from app.costs.models.usage_cost import UsageCost


class StorageCostService:
    """
    Handles storage pricing.

    Examples:
    - Documents
    - Attachments
    - Vector embeddings
    - Object storage
    """

    def __init__(self, db: Session):
        self.repository = CostRepository(db)

    @staticmethod
    def calculate_storage_cost(
        storage_gb: Decimal,
        price_per_gb: Decimal,
    ) -> Decimal:
        """
        Formula:

            storage_gb * price_per_gb
        """

        return (storage_gb * price_per_gb).quantize(
            Decimal("0.000001")
        )

    def record_storage_cost(
        self,
        *,
        workflow_id: Optional[int],
        execution_id: Optional[int],
        provider: str,
        model: str,
        storage_gb: Decimal,
        price_per_gb: Decimal,
    ) -> UsageCost:

        cost = self.calculate_storage_cost(
            storage_gb,
            price_per_gb,
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

    def total_storage_cost(self):
        return self.repository.total_cost()

    def workflow_storage_cost(self, workflow_id: int):
        return self.repository.workflow_cost(workflow_id)

    def execution_storage_cost(self, execution_id: int):
        return self.repository.execution_cost(execution_id)