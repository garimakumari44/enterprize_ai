"""
User API routes.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.user import UserResponse
from app.services.user_service import UserService


router = APIRouter(
    tags=["Users"],
)


def get_user_service(
    db: Session = Depends(get_db),
) -> UserService:
    return UserService(db)


@router.get(
    "/me",
    response_model=UserResponse,
)
def me(
    current_user: User = Depends(get_current_user),
):
    return current_user


@router.get(
    "/{user_id}",
    response_model=UserResponse,
)
def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
):
    return service.get_by_id(user_id)