"""
Health check API endpoints.
"""

from datetime import datetime, timezone

from fastapi import APIRouter
from sqlalchemy import text

from app.core.redis import redis_client
from app.db.session import SessionLocal


router = APIRouter(
    tags=["Health"],
)


def check_database() -> str:
    """Check PostgreSQL connectivity."""
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return "healthy"
    except Exception:
        return "unhealthy"


def check_redis() -> str:
    """Check Redis connectivity."""
    try:
        redis_client.ping()
        return "healthy"
    except Exception:
        return "unhealthy"


@router.get(
    "/health",
    summary="Health Check",
)
def health_check():
    """
    Health check endpoint.
    """

    services = {
        "database": check_database(),
        "redis": check_redis(),
    }

    overall_status = (
        "healthy"
        if all(
            status == "healthy"
            for status in services.values()
        )
        else "degraded"
    )

    return {
        "status": overall_status,
        "service": (
            "Enterprise AI Workflow "
            "Orchestration Platform"
        ),
        "timestamp": (
            datetime.now(timezone.utc).isoformat()
        ),
        "version": "1.0.0",
        "environment": "development",
        "dependencies": services,
    }