"""
S3 Storage Node

Performs object storage operations using the configured StorageService.

Supported Operations
--------------------
- upload
- download
- delete
- copy
- move
- exists
- list
- metadata
- presigned_url
"""

from __future__ import annotations

from typing import Any

from app.nodes.base.base_node import BaseNode
from app.nodes.base.node_context import NodeContext
from app.nodes.base.node_result import NodeResult
from app.services.storage_service import StorageService


class S3Node(BaseNode):
    """
    Execute S3-compatible storage operations.
    """

    NODE_TYPE = "s3"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.storage_service = StorageService()

    def execute(self, context: NodeContext) -> NodeResult:
        operation = self.get_property("operation")

        if not operation:
            return NodeResult.failure("Storage operation is required.")

        try:
            if operation == "upload":
                result = self._upload()

            elif operation == "download":
                result = self._download()

            elif operation == "delete":
                result = self._delete()

            elif operation == "copy":
                result = self._copy()

            elif operation == "move":
                result = self._move()

            elif operation == "exists":
                result = self._exists()

            elif operation == "list":
                result = self._list()

            elif operation == "metadata":
                result = self._metadata()

            elif operation == "presigned_url":
                result = self._presigned_url()

            else:
                return NodeResult.failure(
                    f"Unsupported operation: {operation}"
                )

            return NodeResult.success(data=result)

        except Exception as exc:
            return NodeResult.failure(str(exc))

    def _upload(self) -> dict:
        return self.storage_service.upload(
            connection=self.get_property("connection"),
            bucket=self.get_property("bucket"),
            key=self.get_property("key"),
            file_path=self.get_property("file_path"),
            content=self.get_property("content"),
            content_type=self.get_property("content_type"),
            metadata=self.get_property("metadata", {}),
        )

    def _download(self) -> dict:
        return self.storage_service.download(
            connection=self.get_property("connection"),
            bucket=self.get_property("bucket"),
            key=self.get_property("key"),
            destination=self.get_property("destination"),
        )

    def _delete(self) -> dict:
        return self.storage_service.delete(
            connection=self.get_property("connection"),
            bucket=self.get_property("bucket"),
            key=self.get_property("key"),
        )

    def _copy(self) -> dict:
        return self.storage_service.copy(
            connection=self.get_property("connection"),
            bucket=self.get_property("bucket"),
            source_key=self.get_property("source_key"),
            destination_key=self.get_property("destination_key"),
        )

    def _move(self) -> dict:
        return self.storage_service.move(
            connection=self.get_property("connection"),
            bucket=self.get_property("bucket"),
            source_key=self.get_property("source_key"),
            destination_key=self.get_property("destination_key"),
        )

    def _exists(self) -> dict:
        return {
            "exists": self.storage_service.exists(
                connection=self.get_property("connection"),
                bucket=self.get_property("bucket"),
                key=self.get_property("key"),
            )
        }

    def _list(self) -> dict:
        return self.storage_service.list_objects(
            connection=self.get_property("connection"),
            bucket=self.get_property("bucket"),
            prefix=self.get_property("prefix", ""),
        )

    def _metadata(self) -> dict:
        return self.storage_service.metadata(
            connection=self.get_property("connection"),
            bucket=self.get_property("bucket"),
            key=self.get_property("key"),
        )

    def _presigned_url(self) -> dict:
        return {
            "url": self.storage_service.generate_presigned_url(
                connection=self.get_property("connection"),
                bucket=self.get_property("bucket"),
                key=self.get_property("key"),
                expires_in=self.get_property("expires_in", 3600),
            )
        }

    @classmethod
    def metadata(cls) -> dict[str, Any]:
        return {
            "type": cls.NODE_TYPE,
            "name": "S3 Storage",
            "category": "Storage",
            "description": "Perform operations on S3-compatible object storage.",
            "icon": "database",
            "properties": [
                "operation",
                "connection",
                "bucket",
                "key",
                "source_key",
                "destination_key",
                "file_path",
                "destination",
                "content",
                "content_type",
                "metadata",
                "prefix",
                "expires_in",
            ],
        }