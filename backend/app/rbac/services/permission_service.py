from uuid import UUID

from sqlalchemy.orm import Session

from app.rbac.models.permission import Permission
from app.rbac.repositories.permission_repository import PermissionRepository
from app.rbac.schemas.permission_schema import (
    PermissionCreate,
    PermissionUpdate,
)


class PermissionService:
    def __init__(self, db: Session):
        self.repository = PermissionRepository(db)

    def create_permission(
        self,
        permission_data: PermissionCreate,
    ) -> Permission:
        return self.repository.create(permission_data)

    def get_permission(
        self,
        permission_id: UUID,
    ) -> Permission | None:
        return self.repository.get_by_id(permission_id)

    def get_permission_by_name(
        self,
        name: str,
    ) -> Permission | None:
        return self.repository.get_by_name(name)

    def list_permissions(self) -> list[Permission]:
        return self.repository.get_all()

    def update_permission(
        self,
        permission_id: UUID,
        permission_data: PermissionUpdate,
    ) -> Permission | None:
        return self.repository.update(
            permission_id,
            permission_data,
        )

    def delete_permission(
        self,
        permission_id: UUID,
    ) -> bool:
        return self.repository.delete(permission_id)