from typing import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.models.audit_log import AuditLog
from app.audit.schemas.audit_schema import (
    AuditLogCreate,
    AuditLogFilter,
)


class AuditRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, audit: AuditLogCreate) -> AuditLog:
        log = AuditLog(**audit.model_dump())

        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)

        return log

    def get_by_id(self, audit_id: UUID) -> AuditLog | None:
        stmt = select(AuditLog).where(AuditLog.id == audit_id)

        return self.db.scalar(stmt)

    def list(self, filters: AuditLogFilter) -> Sequence[AuditLog]:
        stmt = select(AuditLog)

        if filters.organization_id:
            stmt = stmt.where(
                AuditLog.organization_id == filters.organization_id
            )

        if filters.project_id:
            stmt = stmt.where(
                AuditLog.project_id == filters.project_id
            )

        if filters.user_id:
            stmt = stmt.where(
                AuditLog.user_id == filters.user_id
            )

        if filters.action:
            stmt = stmt.where(
                AuditLog.action == filters.action
            )

        if filters.resource_type:
            stmt = stmt.where(
                AuditLog.resource_type == filters.resource_type
            )

        if filters.status:
            stmt = stmt.where(
                AuditLog.status == filters.status
            )

        stmt = (
            stmt.order_by(AuditLog.created_at.desc())
            .offset(filters.offset)
            .limit(filters.limit)
        )

        return self.db.scalars(stmt).all()

    def delete(self, audit_id: UUID) -> bool:
        log = self.get_by_id(audit_id)

        if not log:
            return False

        self.db.delete(log)
        self.db.commit()

        return True