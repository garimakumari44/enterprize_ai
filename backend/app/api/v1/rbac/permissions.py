from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession


from app.db.session import get_db

from app.schemas.rbac.permission_schema import (
    PermissionCreate,
    PermissionResponse
)

from app.services.rbac.permission_service import (
    PermissionService
)


router = APIRouter(
    prefix="/rbac/permissions",
    tags=["RBAC - Permissions"]
)



@router.post(
    "/",
    response_model=PermissionResponse
)
async def create_permission(
    payload: PermissionCreate,
    db: AsyncSession = Depends(get_db)
):

    service = PermissionService(db)

    return await service.create_permission(
        payload
    )



@router.get(
    "/",
    response_model=list[PermissionResponse]
)
async def list_permissions(
    db: AsyncSession = Depends(get_db)
):

    service = PermissionService(db)

    return await service.get_permissions()



@router.get(
    "/{permission_id}",
    response_model=PermissionResponse
)
async def get_permission(
    permission_id: int,
    db: AsyncSession = Depends(get_db)
):

    service = PermissionService(db)

    permission = await service.get_permission(
        permission_id
    )


    if not permission:
        raise HTTPException(
            status_code=404,
            detail="Permission not found"
        )


    return permission