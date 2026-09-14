from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.permission import Permission


class PermissionRepository:
    """Repository for Permission database operations."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, permission: Permission) -> Permission:
        self.db.add(permission)
        self.db.commit()
        self.db.refresh(permission)
        return permission

    def get_by_id(self, permission_id: int) -> Permission | None:
        stmt = select(Permission).where(
            Permission.id == permission_id
        )
        return self.db.scalar(stmt)

    def get_by_name(self, name: str) -> Permission | None:
        stmt = select(Permission).where(
            Permission.name == name
        )
        return self.db.scalar(stmt)

    def list(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Permission]:
        stmt = (
            select(Permission)
            .offset(skip)
            .limit(limit)
            .order_by(Permission.resource, Permission.action)
        )
        return list(self.db.scalars(stmt).all())

    def update(self, permission: Permission) -> Permission:
        self.db.commit()
        self.db.refresh(permission)
        return permission

    def delete(self, permission: Permission) -> None:
        self.db.delete(permission)
        self.db.commit()