"""
User repository.

Contains all database operations related to users.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.user import User
from app.schemas.user import UserCreate


class UserRepository:
    """Repository for user database operations."""

    def __init__(self, db: Session):
        self.db = db

    def create_user(
        self,
        user_data: UserCreate,
        hashed_password: str,
    ) -> User:
        """
        Create a new user.
        """

        user = User(
            email=user_data.email.lower().strip(),
            full_name=user_data.full_name.strip(),
            hashed_password=hashed_password,
            is_active=True,
            is_verified=False,
            is_superuser=False,
        )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        return user

    def get_by_id(
        self,
        user_id: UUID,
    ) -> User | None:
        """
        Get user by ID.
        """

        statement = (
            select(User)
            .where(User.id == user_id)
        )

        result = self.db.execute(statement)

        return result.scalar_one_or_none()

    def get_by_email(
        self,
        email: str,
    ) -> User | None:
        """
        Get user by email.
        """

        statement = (
            select(User)
            .where(User.email == email.lower().strip())
        )

        result = self.db.execute(statement)

        return result.scalar_one_or_none()

    def email_exists(
        self,
        email: str,
    ) -> bool:
        """
        Check whether an email already exists.
        """

        return self.get_by_email(email) is not None

    def update(
        self,
        user: User,
    ) -> User:
        """
        Update an existing user.
        """

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        return user

    def delete(
        self,
        user: User,
    ) -> None:
        """
        Delete a user.
        """

        self.db.delete(user)
        self.db.commit()