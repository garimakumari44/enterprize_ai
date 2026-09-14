"""
Authentication API routes.
"""

from fastapi import (
    APIRouter,
    Depends,
    status,
)

from sqlalchemy.orm import Session

from app.db.session import get_db

from app.core.dependencies import get_current_user

from app.db.models.user import User

from app.schemas.user import (
    UserCreate,
    UserResponse,
)

from app.schemas.auth import LoginRequest

from app.schemas.token import (
    Token,
    RefreshTokenRequest,
)

from app.services.auth_service import AuthService


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


# ==========================================================
# Dependency
# ==========================================================

def get_auth_service(
    db: Session = Depends(get_db),
) -> AuthService:
    return AuthService(db)


# ==========================================================
# Register
# ==========================================================

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    user: UserCreate,
    service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """
    Register a new user.
    """
    return service.register(user)


# ==========================================================
# Login
# ==========================================================

@router.post(
    "/login",
    response_model=Token,
)
def login(
    credentials: LoginRequest,
    service: AuthService = Depends(get_auth_service),
) -> Token:
    """
    Authenticate a user and return JWT tokens.
    """
    return service.login(
        credentials.email,
        credentials.password,
    )


# ==========================================================
# Refresh Access Token
# ==========================================================

@router.post(
    "/refresh",
    response_model=Token,
)
def refresh(
    request: RefreshTokenRequest,
    service: AuthService = Depends(get_auth_service),
) -> Token:
    """
    Generate a new access token using a refresh token.
    """
    return service.refresh(
        request.refresh_token,
    )


# ==========================================================
# Current User
# ==========================================================

@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """
    Return the authenticated user.
    """
    return current_user


# ==========================================================
# Logout
# ==========================================================

@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
)
def logout(
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    """
    Logout the current user.
    """
    service.logout(current_user)

    return {
        "message": "Successfully logged out."
    }