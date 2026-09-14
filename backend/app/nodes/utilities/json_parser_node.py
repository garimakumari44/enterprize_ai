import json
from typing import Any, Dict

from app.nodes.base.node import BaseNode
from app.nodes.base.node_context import NodeContext
from app.nodes.base.node_result import NodeResult


class JsonParserNode(BaseNode):
    """
    JSON Parser Node

    Converts JSON string into Python object.
    Supports optional field extraction.
    """


    name = "json_parser"
    description = "Parse JSON data and extract values"


    async def execute(
        self,
        context: NodeContext
    ) -> NodeResult:

        try:

            input_data = context.inputs.get(
                "data"
            )

            if not input_data:
                return NodeResult.failure(
                    error="JSON input missing"
                )


            # Convert JSON string
            if isinstance(input_data, str):

                parsed_data = json.loads(
                    input_data
                )

            else:
                parsed_data = input_data


            # Optional extraction

            path = context.inputs.get(
                "path"
            )


            if path:
                parsed_data = self.extract_value(
                    parsed_data,
                    path
                )


            return NodeResult.success(
                data={
                    "result": parsed_data
                }
            )


        except json.JSONDecodeError as e:

            return NodeResult.failure(
                error=f"Invalid JSON: {str(e)}"
            )


        except Exception as e:

            return NodeResult.failure(
                error=str(e)
            )



    def extract_value(
        self,
        data: Dict[str, Any],
        path: str
    ):

        """
        Extract nested JSON value.

        Example:

        path:
        user.name

        """

        keys = path.split(".")


        value = data


        for key in keys:

            if isinstance(value, dict):

                value = value.get(key)

            else:
                return None


        return value