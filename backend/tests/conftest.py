"""
Shared pytest fixtures.

Provides:
- Test database
- FastAPI TestClient
- Dependency overrides
"""

import pytest

from fastapi.testclient import TestClient

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app

from app.db.base import Base
from app.db.session import get_db


# --------------------------------------------------
# Test Database
# --------------------------------------------------

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# --------------------------------------------------
# Create / Drop Tables
# --------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """
    Create all tables before tests
    and remove them afterwards.
    """

    Base.metadata.create_all(bind=engine)

    yield

    Base.metadata.drop_all(bind=engine)


# --------------------------------------------------
# Database Session
# --------------------------------------------------

@pytest.fixture()
def db():
    """
    Provide a database session.
    """

    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()


# --------------------------------------------------
# FastAPI Dependency Override
# --------------------------------------------------

@pytest.fixture()
def client(db):
    """
    FastAPI test client.
    """

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()