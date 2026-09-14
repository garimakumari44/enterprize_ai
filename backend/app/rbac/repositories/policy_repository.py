from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.policy import Policy


class PolicyRepository:
    """Repository for Policy database operations."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, policy: Policy) -> Policy:
        self.db.add(policy)
        self.db.commit()
        self.db.refresh(policy)
        return policy

    def get_by_id(self, policy_id: int) -> Policy | None:
        stmt = select(Policy).where(
            Policy.id == policy_id
        )
        return self.db.scalar(stmt)

    def get_by_name(self, name: str) -> Policy | None:
        stmt = select(Policy).where(
            Policy.name == name
        )
        return self.db.scalar(stmt)

    def list(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Policy]:
        stmt = (
            select(Policy)
            .offset(skip)
            .limit(limit)
            .order_by(Policy.name)
        )
        return list(self.db.scalars(stmt).all())

    def update(self, policy: Policy) -> Policy:
        self.db.commit()
        self.db.refresh(policy)
        return policy

    def delete(self, policy: Policy) -> None:
        self.db.delete(policy)
        self.db.commit()