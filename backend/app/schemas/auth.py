from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Login credentials."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)