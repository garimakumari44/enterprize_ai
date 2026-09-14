"""
Google Drive Node

Performs Google Drive operations through GoogleDriveService.

Supported Operations
--------------------
- upload
- download
- delete
- move
- copy
- create_folder
- list_files
- search
- metadata
- share
"""

from __future__ import annotations

from typing import Any

from app.nodes.base.base_node import BaseNode
from app.nodes.base.node_context import NodeContext
from app.nodes.base.node_result import NodeResult
from app.services.google_drive_service import GoogleDriveService


class GoogleDriveNode(BaseNode):
    """
    Google Drive integration node.
    """

    NODE_TYPE = "google_drive"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.drive_service = GoogleDriveService()

    def execute(self, context: NodeContext) -> NodeResult:

        operation = self.get_property("operation")

        if not operation:
            return NodeResult.failure(
                "Google Drive operation is required."
            )

        try:

            if operation == "upload":
                result = self._upload()

            elif operation == "download":
                result = self._download()

            elif operation == "delete":
                result = self._delete()

            elif operation == "move":
                result = self._move()

            elif operation == "copy":
                result = self._copy()

            elif operation == "create_folder":
                result = self._create_folder()

            elif operation == "list_files":
                result = self._list_files()

            elif operation == "search":
                result = self._search()

            elif operation == "metadata":
                result = self._metadata()

            elif operation == "share":
                result = self._share()

            else:
                return NodeResult.failure(
                    f"Unsupported Google Drive operation: {operation}"
                )

            return NodeResult.success(
                data=result
            )

        except Exception as exc:
            return NodeResult.failure(
                str(exc)
            )


    def _upload(self) -> dict:

        return self.drive_service.upload_file(
            connection=self.get_property("connection"),
            file_path=self.get_property("file_path"),
            filename=self.get_property("filename"),
            folder_id=self.get_property("folder_id"),
            mime_type=self.get_property("mime_type"),
            metadata=self.get_property(
                "metadata",
                {}
            ),
        )


    def _download(self) -> dict:

        return self.drive_service.download_file(
            connection=self.get_property("connection"),
            file_id=self.get_property("file_id"),
            destination=self.get_property(
                "destination"
            ),
        )


    def _delete(self) -> dict:

        return self.drive_service.delete_file(
            connection=self.get_property("connection"),
            file_id=self.get_property("file_id"),
        )


    def _move(self) -> dict:

        return self.drive_service.move_file(
            connection=self.get_property("connection"),
            file_id=self.get_property("file_id"),
            folder_id=self.get_property("folder_id"),
        )


    def _copy(self) -> dict:

        return self.drive_service.copy_file(
            connection=self.get_property("connection"),
            file_id=self.get_property("file_id"),
            filename=self.get_property(
                "filename"
            ),
        )


    def _create_folder(self) -> dict:

        return self.drive_service.create_folder(
            connection=self.get_property("connection"),
            name=self.get_property("name"),
            parent_id=self.get_property(
                "parent_id"
            ),
        )


    def _list_files(self) -> dict:

        return self.drive_service.list_files(
            connection=self.get_property("connection"),
            folder_id=self.get_property(
                "folder_id"
            ),
            limit=self.get_property(
                "limit",
                100
            ),
        )


    def _search(self) -> dict:

        return self.drive_service.search_files(
            connection=self.get_property("connection"),
            query=self.get_property("query"),
        )


    def _metadata(self) -> dict:

        return self.drive_service.get_metadata(
            connection=self.get_property("connection"),
            file_id=self.get_property("file_id"),
        )


    def _share(self) -> dict:

        return self.drive_service.share_file(
            connection=self.get_property("connection"),
            file_id=self.get_property("file_id"),
            email=self.get_property("email"),
            permission=self.get_property(
                "permission",
                "reader"
            ),
        )


    @classmethod
    def metadata(cls) -> dict[str, Any]:

        return {
            "type": cls.NODE_TYPE,
            "name": "Google Drive",
            "category": "Storage",
            "description": (
                "Manage files and folders in Google Drive."
            ),
            "icon": "google-drive",
            "properties": [
                "operation",
                "connection",
                "file_id",
                "file_path",
                "filename",
                "folder_id",
                "parent_id",
                "mime_type",
                "metadata",
                "destination",
                "name",
                "query",
                "limit",
                "email",
                "permission",
            ],
        }