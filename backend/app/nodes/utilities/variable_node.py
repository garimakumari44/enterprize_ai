from app.nodes.base.node import BaseNode
from app.nodes.base.node_context import NodeContext
from app.nodes.base.node_result import NodeResult



class VariableNode(BaseNode):

    """
    Workflow Variable Node

    Creates and retrieves variables.
    """


    name = "variable"

    description = (
        "Manage workflow variables"
    )


    async def execute(
        self,
        context: NodeContext
    ) -> NodeResult:


        try:


            operation = context.inputs.get(
                "operation",
                "set"
            )


            variable_name = context.inputs.get(
                "name"
            )


            if operation == "set":

                value = context.inputs.get(
                    "value"
                )


                context.variables[
                    variable_name
                ] = value


                return NodeResult.success(
                    data={
                        "variable": variable_name,
                        "value": value
                    }
                )



            elif operation == "get":


                value = context.variables.get(
                    variable_name
                )


                return NodeResult.success(
                    data={
                        "value": value
                    }
                )



            elif operation == "delete":


                context.variables.pop(
                    variable_name,
                    None
                )


                return NodeResult.success(
                    data={
                        "deleted": variable_name
                    }
                )


            else:

                return NodeResult.failure(
                    error="Invalid operation"
                )


        except Exception as e:


            return NodeResult.failure(
                error=str(e)
            )