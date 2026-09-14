"""
PostgreSQL Node

Executes SQL queries against a configured PostgreSQL connection.

Supported Operations
--------------------
- SELECT
- INSERT
- UPDATE
- DELETE
- DDL (optional)

Outputs
-------
{
    "rows": [...],
    "row_count": 10,
    "execution_time_ms": 42
}
"""

from __future__ import annotations

from time import perf_counter
from typing import Any

from app.nodes.base.base_node import BaseNode
from app.nodes.base.node_context import NodeContext
from app.nodes.base.node_result import NodeResult
from app.services.database_service import DatabaseService


class PostgresNode(BaseNode):
    """
    Execute PostgreSQL queries.
    """

    NODE_TYPE = "postgres"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.database_service = DatabaseService()

    def execute(self, context: NodeContext) -> NodeResult:
        connection = self.get_property("connection")

        sql = self.get_property("query")

        parameters = self.get_property("parameters", {})

        fetch = self.get_property("fetch", True)

        if not connection:
            return NodeResult.failure(
                "Database connection is required."
            )

        if not sql:
            return NodeResult.failure(
                "SQL query is required."
            )

        start = perf_counter()

        try:
            result = self.database_service.execute(
                connection_name=connection,
                query=sql,
                parameters=parameters,
                fetch=fetch,
            )

            elapsed = int(
                (perf_counter() - start) * 1000
            )

            return NodeResult.success(
                data={
                    "rows": result.get("rows", []),
                    "row_count": result.get("row_count", 0),
                    "execution_time_ms": elapsed,
                }
            )

        except Exception as exc:
            return NodeResult.failure(str(exc))

    @classmethod
    def metadata(cls) -> dict[str, Any]:
        return {
            "type": cls.NODE_TYPE,
            "name": "PostgreSQL",
            "category": "Database",
            "description": (
                "Execute SQL queries against PostgreSQL."
            ),
            "icon": "database",
            "properties": [
                "connection",
                "query",
                "parameters",
                "fetch",
            ],
        }