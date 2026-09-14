
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession


from app.db.session import get_db


from app.schemas.rbac.policy_schema import (
    PolicyCreate,
    PolicyResponse
)


from app.services.rbac.policy_service import (
    PolicyService
)



router = APIRouter(
    prefix="/rbac/policies",
    tags=["RBAC - Policies"]
)




@router.post(
    "/",
    response_model=PolicyResponse
)
async def create_policy(
    payload: PolicyCreate,
    db: AsyncSession = Depends(get_db)
):

    service = PolicyService(db)


    return await service.create_policy(
        payload
    )





@router.get(
    "/",
    response_model=list[PolicyResponse]
)
async def list_policies(
    db: AsyncSession = Depends(get_db)
):

    service = PolicyService(db)


    return await service.get_policies()




@router.get(
    "/{policy_id}",
    response_model=PolicyResponse
)
async def get_policy(
    policy_id:int,
    db:AsyncSession = Depends(get_db)
):

    service = PolicyService(db)


    policy = await service.get_policy(
        policy_id
    )


    if not policy:

        raise HTTPException(
            status_code=404,
            detail="Policy not found"
        )


    return policy