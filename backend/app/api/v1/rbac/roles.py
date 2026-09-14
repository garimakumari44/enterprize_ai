from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

from app.schemas.rbac.role_schema import (
    RoleCreate,
    RoleUpdate,
    RoleResponse
)

from app.services.rbac.role_service import RoleService


router = APIRouter(
    prefix="/rbac/roles",
    tags=["RBAC - Roles"]
)


@router.post(
    "/",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_role(
    payload: RoleCreate,
    db: AsyncSession = Depends(get_db)
):

    service = RoleService(db)

    return await service.create_role(payload)



@router.get(
    "/",
    response_model=list[RoleResponse]
)
async def get_roles(
    db: AsyncSession = Depends(get_db)
):

    service = RoleService(db)

    return await service.get_roles()



@router.get(
    "/{role_id}",
    response_model=RoleResponse
)
async def get_role(
    role_id: int,
    db: AsyncSession = Depends(get_db)
):

    service = RoleService(db)

    role = await service.get_role(role_id)

    if not role:
        raise HTTPException(
            status_code=404,
            detail="Role not found"
        )

    return role



@router.put(
    "/{role_id}",
    response_model=RoleResponse
)
async def update_role(
    role_id: int,
    payload: RoleUpdate,
    db: AsyncSession = Depends(get_db)
):

    service = RoleService(db)

    return await service.update_role(
        role_id,
        payload
    )



@router.delete(
    "/{role_id}"
)
async def delete_role(
    role_id: int,
    db: AsyncSession = Depends(get_db)
):

    service = RoleService(db)

    await service.delete_role(role_id)

    return {
        "message": "Role deleted successfully"
    }