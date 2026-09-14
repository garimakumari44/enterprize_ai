from uuid import UUID

from sqlalchemy.orm import Session

from app.rbac.models.policy import Policy
from app.rbac.repositories.policy_repository import PolicyRepository
from app.rbac.schemas.policy_schema import (
    PolicyCreate,
    PolicyUpdate,
)


class PolicyService:
    def __init__(self, db: Session):
        self.repository = PolicyRepository(db)

    def create_policy(
        self,
        policy_data: PolicyCreate,
    ) -> Policy:
        return self.repository.create(policy_data)

    def get_policy(
        self,
        policy_id: UUID,
    ) -> Policy | None:
        return self.repository.get_by_id(policy_id)

    def list_policies(self) -> list[Policy]:
        return self.repository.get_all()

    def update_policy(
        self,
        policy_id: UUID,
        policy_data: PolicyUpdate,
    ) -> Policy | None:
        return self.repository.update(
            policy_id,
            policy_data,
        )

    def delete_policy(
        self,
        policy_id: UUID,
    ) -> bool:
        return self.repository.delete(policy_id)