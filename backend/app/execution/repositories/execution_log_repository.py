"""
Repository for execution logs.

Handles database operations for execution logs.
"""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from app.execution.models.execution_log import ExecutionLog


class ExecutionLogRepository:
    """Repository for execution log database operations."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, log: ExecutionLog) -> ExecutionLog:
        """
        Create a new execution log.

        Args:
            log: ExecutionLog instance.

        Returns:
            Persisted ExecutionLog.
        """
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def get_by_id(self, log_id: int) -> Optional[ExecutionLog]:
        """
        Retrieve a log by ID.
        """
        return (
            self.db.query(ExecutionLog)
            .filter(ExecutionLog.id == log_id)
            .first()
        )

    def get_execution_logs(
        self,
        execution_id: int,
    ) -> List[ExecutionLog]:
        """
        Get all logs for an execution.

        Ordered by creation time.
        """
        return (
            self.db.query(ExecutionLog)
            .filter(
                ExecutionLog.execution_id == execution_id
            )
            .order_by(ExecutionLog.created_at.asc())
            .all()
        )

    def get_node_logs(
        self,
        execution_id: int,
        node_id: str,
    ) -> List[ExecutionLog]:
        """
        Get logs for a specific node within an execution.
        """
        return (
            self.db.query(ExecutionLog)
            .filter(
                ExecutionLog.execution_id == execution_id,
                ExecutionLog.node_id == node_id,
            )
            .order_by(ExecutionLog.created_at.asc())
            .all()
        )

    def delete(self, log: ExecutionLog) -> None:
        """
        Delete a log.
        """
        self.db.delete(log)
        self.db.commit()

    def delete_execution_logs(
        self,
        execution_id: int,
    ) -> int:
        """
        Delete all logs for an execution.

        Returns:
            Number of deleted rows.
        """
        count = (
            self.db.query(ExecutionLog)
            .filter(
                ExecutionLog.execution_id == execution_id
            )
            .delete()
        )

        self.db.commit()
        return count