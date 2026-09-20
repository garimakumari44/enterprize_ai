"""
Workflow storage utilities.

Responsible for serializing and deserializing workflow
definitions stored in the database.

This is NOT execution storage.
Execution history belongs to Phase 3.
"""

from __future__ import annotations

import json
from typing import Any

from app.models.workflow.workflow import Workflow


class WorkflowStorage:
    """
    Handles workflow definition storage.

    Workflow JSON format:

    {
        "nodes": [...],
        "edges": [...],
        "metadata": {...}
    }
    """

    @staticmethod
    def serialize(
        *,
        nodes: list[dict[str, Any]],
        edges: list[dict[str, Any]],
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Build a workflow JSON document.
        """

        return {
            "nodes": nodes,
            "edges": edges,
            "metadata": metadata or {},
        }

    @staticmethod
    def deserialize(workflow: Workflow) -> dict[str, Any]:
        """
        Return workflow JSON from database model.
        """

        if workflow.definition is None:
            return {
                "nodes": [],
                "edges": [],
                "metadata": {},
            }

        return workflow.definition

    @staticmethod
    def export_json(workflow: Workflow) -> str:
        """
        Export workflow as formatted JSON.
        """

        return json.dumps(
            WorkflowStorage.deserialize(workflow),
            indent=2,
            ensure_ascii=False,
        )

    @staticmethod
    def import_json(json_string: str) -> dict[str, Any]:
        """
        Parse imported workflow JSON.
        """

        return json.loads(json_string)

    @staticmethod
    def update_definition(
        workflow: Workflow,
        *,
        nodes: list[dict[str, Any]],
        edges: list[dict[str, Any]],
        metadata: dict[str, Any] | None = None,
    ) -> Workflow:
        """
        Replace workflow definition.
        """

        workflow.definition = WorkflowStorage.serialize(
            nodes=nodes,
            edges=edges,
            metadata=metadata,
        )

        return workflow