"""
File Node

General file operations.
"""


from typing import Any, Dict


from app.nodes.base.node import Node
from app.nodes.base.node_context import NodeContext
from app.nodes.base.node_result import NodeResult


from app.services.storage_service import StorageService




class FileNode(Node):

    node_type = "storage.file"

    name = "File Operation"

    description = (
        "Perform file operations"
    )


    def __init__(self):

        self.storage = StorageService()



    async def execute(
        self,
        context: NodeContext,
        inputs: Dict[str, Any]
    ) -> NodeResult:


        try:


            operation = inputs.get(
                "operation"
            )


            path = inputs.get(
                "path"
            )


            if not operation:

                return NodeResult.failed(
                    error="Operation required"
                )


            if not path:

                return NodeResult.failed(
                    error="File path required"
                )



            result = None



            if operation == "exists":

                result = await self.storage.exists(
                    path
                )



            elif operation == "delete":

                result = await self.storage.delete(
                    path
                )



            elif operation == "metadata":

                result = await self.storage.metadata(
                    path
                )



            elif operation == "move":

                destination = inputs.get(
                    "destination"
                )

                if not destination:

                    return NodeResult.failed(
                        error="Destination required"
                    )


                result = await self.storage.move(
                    path,
                    destination
                )



            else:

                return NodeResult.failed(
                    error=f"Unsupported operation {operation}"
                )



            return NodeResult.success(
                data={
                    "operation": operation,
                    "result": result
                }
            )



        except Exception as e:


            return NodeResult.failed(
                error=str(e)
            )