from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ============================================================
# Shared User Fields
# ============================================================

class UserBase(BaseModel):
    """
    Fields shared across user schemas.
    """

    full_name: str = Field(
        min_length=2,
        max_length=255,
    )

    email: EmailStr


# ============================================================
# Registration
# ============================================================

class UserCreate(UserBase):
    """
    Schema used when creating a new user account.
    """

    password: str = Field(
        min_length=8,
        max_length=128,
    )


# ============================================================
# Update Profile
# ============================================================

class UserUpdate(BaseModel):
    """
    Schema used for updating user information.
    """

    full_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=255,
    )


# ============================================================
# API Response
# ============================================================

class UserResponse(UserBase):
    """
    User object returned from API.
    """

    id: UUID

    is_active: bool
    is_superuser: bool
    is_verified: bool

    last_login_at: datetime | None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )