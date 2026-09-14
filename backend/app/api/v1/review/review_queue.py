from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.review.review_service import ReviewService
from app.schemas.review.review_schema import (
    ReviewCreate,
    ReviewResponse
)


router = APIRouter(
    prefix="/review",
    tags=["Human Review"]
)


@router.get(
    "/queue",
    response_model=list[ReviewResponse]
)
async def get_review_queue(
    db: AsyncSession = Depends(get_db)
):

    service = ReviewService(db)

    tasks = await service.get_pending_reviews()

    return tasks



@router.post(
    "/queue",
    response_model=ReviewResponse
)
async def create_review_task(
    payload: ReviewCreate,
    db: AsyncSession = Depends(get_db)
):

    service = ReviewService(db)

    task = await service.create_review_task(
        payload
    )

    return task