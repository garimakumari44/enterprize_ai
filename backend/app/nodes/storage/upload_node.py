"""
Upload Node

Uploads files/data into configured storage backend.

Supported:
- Local filesystem
- S3
- Cloud storage (through StorageService abstraction)
"""

from typing import Any, Dict

from app.nodes.base.node import Node
from app.nodes.base.node_context import NodeContext
from app.nodes.base.node_result import NodeResult

from app.services.storage_service import StorageService


class UploadNode(Node):
    """
    Workflow node for uploading files.
    """

    node_type = "storage.upload"
    name = "Upload File"
    description = "Upload a file to storage"

    def __init__(self):
        self.storage = StorageService()


    async def execute(
        self,
        context: NodeContext,
        inputs: Dict[str, Any]
    ) -> NodeResult:

        try:
            file_data = inputs.get("file")

            if not file_data:
                return NodeResult.failed(
                    error="File data missing"
                )


            filename = inputs.get(
                "filename",
                "uploaded_file"
            )


            storage_path = inputs.get(
                "path",
                filename
            )


            result = await self.storage.upload(
                file=file_data,
                path=storage_path
            )


            return NodeResult.success(
                data={
                    "filename": filename,
                    "path": storage_path,
                    "url": result.url,
                    "size": result.size
                }
            )


        except Exception as e:

            return NodeResult.failed(
                error=str(e)
            )