"""
Filesystem Node

Performs local filesystem operations through FileSystemService.

Supported Operations
--------------------
- read
- write
- append
- delete
- move
- copy
- exists
- list
- create_directory
- get_metadata

Use Cases
---------
- Workflow temporary files
- Document processing pipelines
- AI model artifacts
- Export generated reports
"""

from __future__ import annotations

from typing import Any

from app.nodes.base.base_node import BaseNode
from app.nodes.base.node_context import NodeContext
from app.nodes.base.node_result import NodeResult
from app.services.filesystem_service import FileSystemService


class FileSystemNode(BaseNode):
    """
    Filesystem integration node.
    """

    NODE_TYPE = "filesystem"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.filesystem_service = FileSystemService()


    def execute(self, context: NodeContext) -> NodeResult:

        operation = self.get_property("operation")

        if not operation:
            return NodeResult.failure(
                "Filesystem operation is required."
            )

        try:

            if operation == "read":
                result = self._read()

            elif operation == "write":
                result = self._write()

            elif operation == "append":
                result = self._append()

            elif operation == "delete":
                result = self._delete()

            elif operation == "move":
                result = self._move()

            elif operation == "copy":
                result = self._copy()

            elif operation == "exists":
                result = self._exists()

            elif operation == "list":
                result = self._list()

            elif operation == "create_directory":
                result = self._create_directory()

            elif operation == "metadata":
                result = self._metadata()

            else:
                return NodeResult.failure(
                    f"Unsupported filesystem operation: {operation}"
                )


            return NodeResult.success(
                data=result
            )


        except Exception as exc:

            return NodeResult.failure(
                str(exc)
            )


    def _read(self) -> dict:

        return self.filesystem_service.read_file(
            path=self.get_property("path"),
            encoding=self.get_property(
                "encoding",
                "utf-8"
            ),
        )


    def _write(self) -> dict:

        return self.filesystem_service.write_file(
            path=self.get_property("path"),
            content=self.get_property(
                "content"
            ),
            encoding=self.get_property(
                "encoding",
                "utf-8"
            ),
        )


    def _append(self) -> dict:

        return self.filesystem_service.append_file(
            path=self.get_property("path"),
            content=self.get_property(
                "content"
            ),
        )


    def _delete(self) -> dict:

        return self.filesystem_service.delete_file(
            path=self.get_property("path"),
        )


    def _move(self) -> dict:

        return self.filesystem_service.move_file(
            source=self.get_property(
                "source"
            ),
            destination=self.get_property(
                "destination"
            ),
        )


    def _copy(self) -> dict:

        return self.filesystem_service.copy_file(
            source=self.get_property(
                "source"
            ),
            destination=self.get_property(
                "destination"
            ),
        )


    def _exists(self) -> dict:

        return {
            "exists": self.filesystem_service.exists(
                path=self.get_property(
                    "path"
                )
            )
        }


    def _list(self) -> dict:

        return self.filesystem_service.list_directory(
            path=self.get_property(
                "path"
            ),
            recursive=self.get_property(
                "recursive",
                False
            ),
        )


    def _create_directory(self) -> dict:

        return self.filesystem_service.create_directory(
            path=self.get_property(
                "path"
            )
        )


    def _metadata(self) -> dict:

        return self.filesystem_service.get_metadata(
            path=self.get_property(
                "path"
            )
        )


    @classmethod
    def metadata(cls) -> dict[str, Any]:

        return {
            "type": cls.NODE_TYPE,
            "name": "Filesystem",
            "category": "Storage",
            "description": (
                "Perform filesystem operations."
            ),
            "icon": "folder",
            "properties": [
                "operation",
                "path",
                "source",
                "destination",
                "content",
                "encoding",
                "recursive",
            ],
        }