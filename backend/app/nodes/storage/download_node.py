"""
Download Node

Downloads files from storage.
"""


from typing import Any, Dict


from app.nodes.base.node import Node
from app.nodes.base.node_context import NodeContext
from app.nodes.base.node_result import NodeResult

from app.services.storage_service import StorageService



class DownloadNode(Node):

    node_type = "storage.download"
    name = "Download File"

    description = (
        "Download file from storage"
    )


    def __init__(self):

        self.storage = StorageService()



    async def execute(
        self,
        context: NodeContext,
        inputs: Dict[str, Any]
    ) -> NodeResult:


        try:

            path = inputs.get("path")


            if not path:

                return NodeResult.failed(
                    error="File path required"
                )



            file_data = await self.storage.download(
                path
            )


            return NodeResult.success(
                data={
                    "path": path,
                    "file": file_data
                }
            )


        except Exception as e:


            return NodeResult.failed(
                error=str(e)
            )