"""
Database session management.

Provides both synchronous and asynchronous SQLAlchemy sessions.

The existing application can continue using the synchronous session,
while async application services such as DocumentService can use
the asynchronous session.
"""

from typing import AsyncGenerator, Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


# ============================================================================
# Synchronous Database
# ============================================================================

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def get_db() -> Generator[Session, None, None]:
    """
    Provide a synchronous database session.

    Used by existing synchronous repositories and services.
    """

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# ============================================================================
# Asynchronous Database
# ============================================================================

# Convert the existing synchronous PostgreSQL URL into
# an asyncpg URL.
#
# Example:
#
# postgresql+psycopg://...
#
# becomes:
#
# postgresql+asyncpg://...

ASYNC_DATABASE_URL = settings.DATABASE_URL

if "+psycopg" in ASYNC_DATABASE_URL:
    ASYNC_DATABASE_URL = ASYNC_DATABASE_URL.replace(
        "+psycopg",
        "+asyncpg",
    )

elif ASYNC_DATABASE_URL.startswith("postgresql://"):
    ASYNC_DATABASE_URL = ASYNC_DATABASE_URL.replace(
        "postgresql://",
        "postgresql+asyncpg://",
        1,
    )


async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    pool_pre_ping=True,
)


AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autoflush=False,
    expire_on_commit=False,
)


# ============================================================================
# Async Database Dependency
# ============================================================================

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide an asynchronous database session.

    The transaction is committed when the request completes
    successfully.

    If an exception occurs, the transaction is rolled back.

    Used by asynchronous application services such as
    DocumentService and WorkflowService.
    """

    async with AsyncSessionLocal() as db:
        try:
            yield db

            # Commit successful request-level database changes.
            await db.commit()

        except Exception:
            # Roll back any uncommitted changes if the request fails.
            await db.rollback()
            raise

        finally:
            await db.close()