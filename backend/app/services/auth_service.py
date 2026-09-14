"""
Authentication service.

Contains business logic for authentication.
"""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
    verify_refresh_token,
)
from app.db.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.token import Token
from app.schemas.user import UserCreate


class AuthService:
    """
    Authentication business logic.
    """

    def __init__(self, db: Session):
        self.user_repository = UserRepository(db)

    # ==========================================================
    # Register
    # ==========================================================

    def register(
        self,
        user_data: UserCreate,
    ) -> User:
        """
        Register a new user.
        """

        email = user_data.email.strip().lower()

        # Check whether the email already exists.
        existing_user = self.user_repository.get_by_email(email)

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered.",
            )

        # Hash password using pwdlib/Argon2.
        hashed_password = get_password_hash(
            user_data.password
        )

        # Create user.
        user = self.user_repository.create_user(
            user_data=user_data,
            hashed_password=hashed_password,
        )

        return user

    # ==========================================================
    # Authenticate
    # ==========================================================

    def authenticate(
        self,
        email: str,
        password: str,
    ) -> User:
        """
        Authenticate a user using email and password.

        This method also contains temporary diagnostic logging
        to identify why login may be returning HTTP 401.
        """

        email = email.strip().lower()

        # ------------------------------------------------------
        # Find user
        # ------------------------------------------------------

        user = self.user_repository.get_by_email(email)

        # Temporary authentication diagnostics.
        # Never print the actual password or complete hash.
        print("========== AUTH DEBUG ==========")
        print("Email:", repr(email))
        print("User found:", user is not None)

        if user is None:
            print("AUTH FAILED: user not found")
            print("================================")

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
                headers={
                    "WWW-Authenticate": "Bearer",
                },
            )

        # ------------------------------------------------------
        # User information
        # ------------------------------------------------------

        print("User ID:", user.id)
        print("User active:", user.is_active)

        # Only print a small prefix.
        # Do NOT print the complete password hash.
        print(
            "Hash type:",
            user.hashed_password[:20],
        )

        # ------------------------------------------------------
        # Verify password
        # ------------------------------------------------------

        password_valid = verify_password(
            password,
            user.hashed_password,
        )

        print("Password valid:", password_valid)
        print("================================")

        if not password_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
                headers={
                    "WWW-Authenticate": "Bearer",
                },
            )

        # ------------------------------------------------------
        # Check account status
        # ------------------------------------------------------

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account has been disabled.",
            )

        return user

    # ==========================================================
    # Login
    # ==========================================================

    def login(
        self,
        email: str,
        password: str,
    ) -> Token:
        """
        Authenticate user and return access + refresh tokens.
        """

        user = self.authenticate(
            email=email,
            password=password,
        )

        # Update last login time.
        user.last_login_at = datetime.now(timezone.utc)

        self.user_repository.update(user)

        # Create access token.
        access_token = create_access_token(
            subject=str(user.id),
        )

        # Create refresh token.
        refresh_token = create_refresh_token(
            subject=str(user.id),
        )

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )

    # ==========================================================
    # Refresh Token
    # ==========================================================

    def refresh(
        self,
        refresh_token: str,
    ) -> Token:
        """
        Generate new access and refresh tokens from a valid
        refresh token.
        """

        # ------------------------------------------------------
        # Verify refresh token
        # ------------------------------------------------------

        try:
            payload = verify_refresh_token(
                refresh_token
            )

        except JWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token.",
                headers={
                    "WWW-Authenticate": "Bearer",
                },
            ) from exc

        # ------------------------------------------------------
        # Extract user ID
        # ------------------------------------------------------

        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token.",
                headers={
                    "WWW-Authenticate": "Bearer",
                },
            )

        # ------------------------------------------------------
        # Validate UUID
        # ------------------------------------------------------

        try:
            user_uuid = UUID(str(user_id))

        except (ValueError, AttributeError) as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token.",
                headers={
                    "WWW-Authenticate": "Bearer",
                },
            ) from exc

        # ------------------------------------------------------
        # Find user
        # ------------------------------------------------------

        user = self.user_repository.get_by_id(
            user_uuid
        )

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found.",
                headers={
                    "WWW-Authenticate": "Bearer",
                },
            )

        # ------------------------------------------------------
        # Check account status
        # ------------------------------------------------------

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is disabled.",
            )

        # ------------------------------------------------------
        # Generate new tokens
        # ------------------------------------------------------

        new_access_token = create_access_token(
            subject=str(user.id),
        )

        new_refresh_token = create_refresh_token(
            subject=str(user.id),
        )

        return Token(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
        )