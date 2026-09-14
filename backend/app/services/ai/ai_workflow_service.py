from typing import Dict, Any, List

from app.repositories.ai.prompt_repository import PromptRepository
from app.repositories.ai.provider_repository import ProviderRepository
from app.repositories.ai.secret_repository import SecretRepository


class AIWorkflowService:

    def __init__(
        self,
        prompt_repository: PromptRepository,
        provider_repository: ProviderRepository,
        secret_repository: SecretRepository,
    ):
        self.prompt_repository = prompt_repository
        self.provider_repository = provider_repository
        self.secret_repository = secret_repository


    async def execute_workflow(
        self,
        workflow_config: Dict[str, Any],
        input_data: Dict[str, Any],
    ) -> Dict[str, Any]:

        """
        Execute AI workflow.

        Example workflow:

        {
            "provider": "openai",
            "model": "gpt-5",
            "prompt_id": 10
        }

        """

        provider_name = workflow_config.get(
            "provider"
        )

        model = workflow_config.get(
            "model"
        )

        prompt_id = workflow_config.get(
            "prompt_id"
        )


        prompt = None

        if prompt_id:
            prompt = await self.prompt_repository.get_by_id(
                prompt_id
            )


        provider = await self.provider_repository.get_by_name(
            provider_name
        )


        if not provider:
            raise Exception(
                "AI Provider not configured"
            )


        result = {
            "provider": provider_name,
            "model": model,
            "prompt": prompt.template if prompt else None,
            "input": input_data,
            "status": "completed"
        }


        return result



    async def validate_workflow(
        self,
        workflow_config: Dict[str,Any]
    ) -> bool:


        required = [
            "provider",
            "model"
        ]


        for field in required:

            if field not in workflow_config:
                return False


        return True