import re

from app.nodes.base.node import BaseNode
from app.nodes.base.node_context import NodeContext
from app.nodes.base.node_result import NodeResult



class TemplateNode(BaseNode):

    """
    Template Rendering Node

    Replaces variables inside templates.
    """


    name = "template"

    description = (
        "Render dynamic templates using variables"
    )


    async def execute(
        self,
        context: NodeContext
    ) -> NodeResult:


        try:

            template = context.inputs.get(
                "template"
            )


            variables = context.inputs.get(
                "variables",
                {}
            )


            if not template:

                return NodeResult.failure(
                    error="Template missing"
                )


            rendered = self.render(
                template,
                variables
            )


            return NodeResult.success(
                data={
                    "result": rendered
                }
            )


        except Exception as e:

            return NodeResult.failure(
                error=str(e)
            )



    def render(
        self,
        template: str,
        variables: dict
    ):


        pattern = r"\{\{\s*(.*?)\s*\}\}"


        def replace(match):

            key = match.group(1)

            return str(
                variables.get(
                    key,
                    ""
                )
            )


        return re.sub(
            pattern,
            replace,
            template
        )