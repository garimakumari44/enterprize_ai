from __future__ import annotations

from typing import Any
from uuid import UUID

from app.audit.repositories.audit_repository import AuditRepository
from app.audit.schemas.audit_schema import (
    AuditLogCreate,
    AuditLogFilter,
    AuditLogRead,
)


class AuditService:
    """
    Service responsible for recording and retrieving audit events.
    """

    def __init__(self, repository: AuditRepository):
        self.repository = repository

    def log_event(
        self,
        *,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
        organization_id: UUID | None = None,
        project_id: UUID | None = None,
        user_id: UUID | None = None,
        status: str = "SUCCESS",
        ip_address: str | None = None,
        user_agent: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLogRead:

        audit = AuditLogCreate(
            organization_id=organization_id,
            project_id=project_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            status=status,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata or {},
        )

        created = self.repository.create(audit)

        return AuditLogRead.model_validate(created)

    def get_audit_log(
        self,
        audit_id: UUID,
    ) -> AuditLogRead | None:

        audit = self.repository.get_by_id(audit_id)

        if audit is None:
            return None

        return AuditLogRead.model_validate(audit)

    def list_logs(
        self,
        filters: AuditLogFilter,
    ) -> list[AuditLogRead]:

        logs = self.repository.list(filters)

        return [
            AuditLogRead.model_validate(log)
            for log in logs
        ]

    def delete_log(
        self,
        audit_id: UUID,
    ) -> bool:

        return self.repository.delete(audit_id)

    def log_success(
        self,
        *,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
        organization_id: UUID | None = None,
        project_id: UUID | None = None,
        user_id: UUID | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLogRead:

        return self.log_event(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            organization_id=organization_id,
            project_id=project_id,
            user_id=user_id,
            status="SUCCESS",
            metadata=metadata,
        )

    def log_failure(
        self,
        *,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
        organization_id: UUID | None = None,
        project_id: UUID | None = None,
        user_id: UUID | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditLogRead:

        return self.log_event(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            organization_id=organization_id,
            project_id=project_id,
            user_id=user_id,
            status="FAILED",
            metadata=metadata,
        )