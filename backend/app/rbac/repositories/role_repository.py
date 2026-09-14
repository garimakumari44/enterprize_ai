from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.role import Role


class RoleRepository:
    """Repository for Role database operations."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, role: Role) -> Role:
        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)
        return role

    def get_by_id(self, role_id: int) -> Role | None:
        stmt = select(Role).where(Role.id == role_id)
        return self.db.scalar(stmt)

    def get_by_name(self, name: str) -> Role | None:
        stmt = select(Role).where(Role.name == name)
        return self.db.scalar(stmt)

    def list(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Role]:
        stmt = (
            select(Role)
            .offset(skip)
            .limit(limit)
            .order_by(Role.name)
        )
        return list(self.db.scalars(stmt).all())

    def update(self, role: Role) -> Role:
        self.db.commit()
        self.db.refresh(role)
        return role

    def delete(self, role: Role) -> None:
        self.db.delete(role)
        self.db.commit()