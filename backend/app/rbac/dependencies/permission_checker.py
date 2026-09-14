"""
RBAC Permission Dependency

Provides reusable FastAPI dependencies for checking user permissions.

Example:
    @router.post(
        "/roles",
        dependencies=[Depends(require_permission("roles:create"))],
    )
"""

from typing import Callable

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.permission_repository import PermissionRepository


class PermissionChecker:
    """
    Checks whether the authenticated user possesses
    a specific permission.
    """

    def __init__(self, permission: str):
        self.permission = permission

    def __call__(
        self,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        repository = PermissionRepository(db)

        has_permission = repository.user_has_permission(
            user_id=current_user.id,
            permission_name=self.permission,
        )

        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permission: {self.permission}",
            )

        return current_user


def require_permission(permission: str) -> Callable:
    """
    FastAPI dependency factory.

    Example:
        Depends(require_permission("documents:read"))
    """
    return PermissionChecker(permission)