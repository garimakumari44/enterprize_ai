from __future__ import annotations

from typing import Any

from fastapi import Request


class AuditFormatter:
    """
    Helper utilities for creating consistent audit metadata.
    """

    @staticmethod
    def metadata(**kwargs: Any) -> dict[str, Any]:
        """
        Remove None values from metadata.
        """

        return {
            key: value
            for key, value in kwargs.items()
            if value is not None
        }

    @staticmethod
    def request_info(request: Request) -> dict[str, Any]:
        """
        Extract request information for audit logging.
        """

        return {
            "method": request.method,
            "path": request.url.path,
            "query": str(request.url.query),
            "client": request.client.host if request.client else None,
            "user_agent": request.headers.get("User-Agent"),
        }

    @staticmethod
    def resource(
        resource_type: str,
        resource_id: str | None = None,
    ) -> dict[str, Any]:

        return {
            "resource_type": resource_type,
            "resource_id": resource_id,
        }

    @staticmethod
    def user(
        user_id: str | None,
        organization_id: str | None = None,
        project_id: str | None = None,
    ) -> dict[str, Any]:

        return {
            "user_id": user_id,
            "organization_id": organization_id,
            "project_id": project_id,
        }

    @staticmethod
    def exception(exc: Exception) -> dict[str, Any]:
        """
        Format exception details for storage.
        """

        return {
            "exception": exc.__class__.__name__,
            "message": str(exc),
        }

    @staticmethod
    def merge(*objects: dict[str, Any]) -> dict[str, Any]:
        """
        Merge multiple metadata dictionaries.
        """

        result: dict[str, Any] = {}

        for obj in objects:
            result.update(
                {
                    k: v
                    for k, v in obj.items()
                    if v is not None
                }
            )

        return result