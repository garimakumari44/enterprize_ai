"""
Database Runtime

Executes SQL queries as part of a workflow.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.execution.runtime.base_runtime import BaseRuntime
from app.execution.exceptions.execution_exception import ExecutionException


class DatabaseRuntime(BaseRuntime):
    """
    Runtime for Database nodes.

    Expected config:

    {
        "query": "SELECT * FROM users WHERE id = :user_id",
        "parameters": {
            "user_id": "{{user.id}}"
        }
    }
    """

    def __init__(
        self,
        context_manager,
        db: Session,
    ):
        super().__init__(context_manager)
        self.db = db

    @property
    def node_type(self) -> str:
        return "database"

    def execute(
        self,
        node: Any,
        execution: Any,
    ) -> dict[str, Any]:
        """
        Execute a SQL query.
        """

        config = self.resolve_config(node.config)

        query = config.get("query")

        if not query:
            raise ExecutionException(
                "Database node requires a SQL query."
            )

        parameters = config.get("parameters", {})

        self.log("Executing SQL query.")

        try:
            result = self.db.execute(
                text(query),
                parameters,
            )

            query_type = query.strip().split()[0].upper()

            if query_type == "SELECT":

                rows = [
                    dict(row._mapping)
                    for row in result.fetchall()
                ]

                output = {
                    "rows": rows,
                    "count": len(rows),
                }

            else:

                self.db.commit()

                output = {
                    "rows_affected": result.rowcount,
                }

            self.save_output(
                node_id=str(node.id),
                output=output,
            )

            self.log("SQL execution completed.")

            return output

        except SQLAlchemyError as exc:

            self.db.rollback()

            raise ExecutionException(
                f"Database execution failed: {exc}"
            ) from exc