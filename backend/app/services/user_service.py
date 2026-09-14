"""
User service.

Contains business logic related to users.
"""

from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.db.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate


class UserService:
    """Service for user-related operations."""

    def __init__(self, db: Session):
        self.repository = UserRepository(db)

    def create_user(self, user_in: UserCreate) -> User:
        """
        Create a new user.

        Raises:
            ValueError: If a user with the given email already exists.
        """
        existing_user = self.repository.get_by_email(user_in.email)

        if existing_user:
            raise ValueError("Email is already registered.")

        hashed_password = get_password_hash(user_in.password)

        user = User(
            email=user_in.email,
            full_name=user_in.full_name,
            hashed_password=hashed_password,
        )

        return self.repository.create(user)

    def get_user_by_id(self, user_id: int) -> User | None:
        """
        Retrieve a user by ID.
        """
        return self.repository.get_by_id(user_id)

    def get_user_by_email(self, email: str) -> User | None:
        """
        Retrieve a user by email.
        """
        return self.repository.get_by_email(email)