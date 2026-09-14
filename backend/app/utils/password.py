"""
Password utilities.

Provides helper functions for:

- Hashing passwords before storing them.
- Verifying plain passwords against hashed passwords.
"""

from passlib.context import CryptContext

# Configure password hashing algorithm
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


def hash_password(password: str) -> str:
    """
    Hash a plain-text password.

    Args:
        password: User's plain password.

    Returns:
        Hashed password string.
    """
    return pwd_context.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """
    Verify a plain password against its hash.

    Args:
        plain_password: Password entered by the user.
        hashed_password: Password stored in the database.

    Returns:
        True if the password matches, otherwise False.
    """
    return pwd_context.verify(
        plain_password,
        hashed_password,
    )