from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession


from app.db.session import get_db
from app.services.review.review_service import ReviewService
from app.schemas.review.approval_schema import (
    ApprovalRequest
)


router = APIRouter(
    prefix="/review/approvals",
    tags=["Review Approval"]
)



@router.post(
    "/approve/{task_id}"
)
async def approve_task(
    task_id:int,
    payload:ApprovalRequest,
    db:AsyncSession=Depends(get_db)
):

    service = ReviewService(db)


    result = await service.approve(
        task_id,
        payload
    )


    return {
        "status":"approved",
        "task":result
    }



@router.post(
    "/reject/{task_id}"
)
async def reject_task(
    task_id:int,
    payload:ApprovalRequest,
    db:AsyncSession=Depends(get_db)
):

    service = ReviewService(db)


    result = await service.reject(
        task_id,
        payload
    )


    return {
        "status":"rejected",
        "task":result
    }