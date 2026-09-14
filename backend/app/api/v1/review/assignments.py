from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.review.review_service import ReviewService
from app.schemas.review.review_schema import (
    AssignmentCreate,
    ReviewResponse
)


router = APIRouter(
    prefix="/review/assignments",
    tags=["Review Assignment"]
)



@router.post("/")
async def assign_review_task(
    payload: AssignmentCreate,
    db: AsyncSession = Depends(get_db)
):

    service = ReviewService(db)

    result = await service.assign_task(
        payload
    )

    return result



@router.get(
    "/user/{user_id}",
    response_model=list[ReviewResponse]
)
async def get_user_assignments(
    user_id:int,
    db:AsyncSession = Depends(get_db)
):

    service = ReviewService(db)

    tasks = await service.get_user_tasks(
        user_id
    )

    return tasks