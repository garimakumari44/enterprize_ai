"""
Execution Repository.

Provides database operations for workflow executions.
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.execution.execution import Execution
from app.constants.execution_status import ExecutionStatus


class ExecutionRepository:
    """Repository for Execution model."""

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def create(self, execution: Execution) -> Execution:
        """
        Create a new execution.

        Args:
            execution: Execution instance

        Returns:
            Persisted execution
        """
        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)
        return execution

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_by_id(self, execution_id: int) -> Optional[Execution]:
        """
        Get execution by ID.
        """
        return (
            self.db.query(Execution)
            .filter(Execution.id == execution_id)
            .first()
        )

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Execution]:
        """
        Get all executions.
        """
        return (
            self.db.query(Execution)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_workflow(
        self,
        workflow_id: int,
    ) -> List[Execution]:
        """
        Get executions for a workflow.
        """
        return (
            self.db.query(Execution)
            .filter(Execution.workflow_id == workflow_id)
            .order_by(Execution.started_at.desc())
            .all()
        )

    def get_running(self) -> List[Execution]:
        """
        Get all running executions.
        """
        return (
            self.db.query(Execution)
            .filter(
                Execution.status == ExecutionStatus.RUNNING
            )
            .all()
        )

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, execution: Execution) -> Execution:
        """
        Update execution.
        """
        self.db.commit()
        self.db.refresh(execution)
        return execution

    def update_status(
        self,
        execution: Execution,
        status: ExecutionStatus,
    ) -> Execution:
        """
        Update execution status.
        """
        execution.status = status
        self.db.commit()
        self.db.refresh(execution)
        return execution

    def update_context(
        self,
        execution: Execution,
        context: dict,
    ) -> Execution:
        """
        Update execution context.
        """
        execution.context = context
        self.db.commit()
        self.db.refresh(execution)
        return execution

    def update_outputs(
        self,
        execution: Execution,
        outputs: dict,
    ) -> Execution:
        """
        Update execution outputs.
        """
        execution.outputs = outputs
        self.db.commit()
        self.db.refresh(execution)
        return execution

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete(self, execution: Execution) -> None:
        """
        Delete execution.
        """
        self.db.delete(execution)
        self.db.commit()