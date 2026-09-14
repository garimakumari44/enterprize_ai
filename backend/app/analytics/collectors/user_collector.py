from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.organizations.models.organization import Organization
from app.projects.models.project import Project
from app.users.models.user import User


class UserCollector:
    """
    Collects user and organization metrics.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def collect(self) -> dict:
        """
        Collect current platform user metrics.
        """

        total_users = await self.db.scalar(
            select(func.count(User.id))
        ) or 0

        active_users = await self.db.scalar(
            select(func.count(User.id)).where(User.is_active.is_(True))
        ) or 0

        organizations = await self.db.scalar(
            select(func.count(Organization.id))
        ) or 0

        projects = await self.db.scalar(
            select(func.count(Project.id))
        ) or 0

        return {
            "total_users": total_users,
            "active_users": active_users,
            "new_users": 0,  # Replace with a 30-day query if tracking user creation dates
            "organizations": organizations,
            "projects": projects,
        }