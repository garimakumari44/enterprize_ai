"""
app/core/security.py

Authentication and security utilities.

Responsibilities:
- Password hashing
- Password verification
- Access token creation
- Refresh token creation
- JWT decoding
- JWT validation
- Token subject extraction
- Bearer token extraction
"""

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from jose import JWTError, jwt
from pwdlib import PasswordHash

from app.core.config import settings


# ============================================================================
# HTTP Authentication
# ============================================================================

security = HTTPBearer(
    auto_error=True,
)


# ============================================================================
# Password Hashing
# ============================================================================

"""
Password hashing is handled by pwdlib.

pwdlib's recommended configuration uses Argon2.

Install:
    pip install "pwdlib[argon2]"

New passwords will be stored as Argon2 hashes.
"""

password_hash = PasswordHash.recommended()


def get_password_hash(password: str) -> str:
    """
    Hash a plain-text password.

    Args:
        password: Plain-text password.

    Returns:
        Secure Argon2 password hash.

    Raises:
        ValueError: If password is empty.
    """
    if not password:
        raise ValueError("Password cannot be empty")

    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """
    Verify a plain-text password against a stored hash.

    Args:
        plain_password: Password supplied by the user.
        hashed_password: Password hash stored in the database.

    Returns:
        True if password matches, otherwise False.
    """
    if not plain_password or not hashed_password:
        return False

    try:
        return password_hash.verify(
            plain_password,
            hashed_password,
        )
    except Exception:
        # Invalid or incompatible hash formats should simply
        # result in a failed authentication attempt.
        return False


# ============================================================================
# JWT Creation
# ============================================================================


def _create_token(
    *,
    subject: str,
    token_type: str,
    expires_delta: timedelta,
) -> str:
    """
    Create a JWT token.

    Args:
        subject: User identifier.
        token_type: Token type ("access" or "refresh").
        expires_delta: Token lifetime.

    Returns:
        Encoded JWT.
    """
    now = datetime.now(timezone.utc)

    payload: dict[str, Any] = {
        "sub": str(subject),
        "type": token_type,
        "jti": str(uuid4()),
        "iat": now,
        "exp": now + expires_delta,
    }

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def create_access_token(
    subject: str,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create an access token.

    Args:
        subject: User identifier.
        expires_delta: Optional custom expiration duration.

    Returns:
        Encoded access JWT.
    """
    expiration = (
        expires_delta
        if expires_delta is not None
        else timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    )

    return _create_token(
        subject=subject,
        token_type="access",
        expires_delta=expiration,
    )


def create_refresh_token(
    subject: str,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a refresh token.

    Args:
        subject: User identifier.
        expires_delta: Optional custom expiration duration.

    Returns:
        Encoded refresh JWT.
    """
    expiration = (
        expires_delta
        if expires_delta is not None
        else timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
    )

    return _create_token(
        subject=subject,
        token_type="refresh",
        expires_delta=expiration,
    )


# ============================================================================
# JWT Decoding
# ============================================================================


def decode_token(
    token: str,
) -> dict[str, Any]:
    """
    Decode and validate a JWT.

    Args:
        token: Encoded JWT.

    Returns:
        Decoded JWT payload.

    Raises:
        JWTError: If token is invalid or expired.
    """
    if not token:
        raise JWTError("Token is required")

    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )


# ============================================================================
# Access Token Verification
# ============================================================================


def verify_access_token(
    token: str,
) -> dict[str, Any]:
    """
    Verify an access token.

    Args:
        token: Encoded access JWT.

    Returns:
        Validated JWT payload.

    Raises:
        JWTError: If token is invalid or expired.
    """
    try:
        payload = decode_token(token)

        # Make sure this is actually an access token.
        if payload.get("type") != "access":
            raise JWTError("Invalid access token")

        # Make sure the token contains a subject.
        subject = payload.get("sub")

        if not subject:
            raise JWTError(
                "Access token missing subject"
            )

        return payload

    except JWTError as exc:
        raise JWTError(
            "Invalid or expired access token"
        ) from exc


# ============================================================================
# Refresh Token Verification
# ============================================================================


def verify_refresh_token(
    token: str,
) -> dict[str, Any]:
    """
    Verify a refresh token.

    Args:
        token: Encoded refresh JWT.

    Returns:
        Validated JWT payload.

    Raises:
        JWTError: If token is invalid or expired.
    """
    try:
        payload = decode_token(token)

        # Make sure this is actually a refresh token.
        if payload.get("type") != "refresh":
            raise JWTError("Invalid refresh token")

        # Make sure the token contains a subject.
        subject = payload.get("sub")

        if not subject:
            raise JWTError(
                "Refresh token missing subject"
            )

        return payload

    except JWTError as exc:
        raise JWTError(
            "Invalid or expired refresh token"
        ) from exc


# ============================================================================
# Token Subject Helpers
# ============================================================================


def get_token_subject(
    token: str,
) -> str:
    """
    Get the user ID from an access token.

    Args:
        token: Encoded access JWT.

    Returns:
        User identifier.

    Raises:
        JWTError: If token is invalid.
    """
    payload = verify_access_token(token)

    subject = payload.get("sub")

    if not subject:
        raise JWTError("Token missing subject")

    return str(subject)


def get_refresh_token_subject(
    token: str,
) -> str:
    """
    Get the user ID from a refresh token.

    Args:
        token: Encoded refresh JWT.

    Returns:
        User identifier.

    Raises:
        JWTError: If token is invalid.
    """
    payload = verify_refresh_token(token)

    subject = payload.get("sub")

    if not subject:
        raise JWTError("Token missing subject")

    return str(subject)


# ============================================================================
# Bearer Token Helper
# ============================================================================


def extract_bearer_token(
    credentials: HTTPAuthorizationCredentials,
) -> str:
    """
    Extract the raw JWT from HTTP Bearer credentials.

    Args:
        credentials: FastAPI HTTP authorization credentials.

    Returns:
        Raw JWT string.

    Raises:
        JWTError: If authentication scheme is not Bearer
            or the token is missing.
    """
    if credentials.scheme.lower() != "bearer":
        raise JWTError(
            "Invalid authentication scheme"
        )

    if not credentials.credentials:
        raise JWTError(
            "Missing bearer token"
        )

    return credentials.credentials