from typing import List, Optional

from app.repositories.ai.prompt_repository import PromptRepository
from app.schemas.ai.prompt_schema import (
    PromptCreate,
    PromptUpdate
)



class PromptService:


    def __init__(
        self,
        repository: PromptRepository
    ):

        self.repository = repository



    async def create_prompt(
        self,
        data: PromptCreate
    ):

        return await self.repository.create(
            data
        )



    async def get_prompt(
        self,
        prompt_id:int
    ):

        prompt = await self.repository.get_by_id(
            prompt_id
        )

        if not prompt:
            raise Exception(
                "Prompt not found"
            )

        return prompt



    async def list_prompts(
        self,
        organization_id:int
    ):

        return await self.repository.list_by_org(
            organization_id
        )



    async def update_prompt(
        self,
        prompt_id:int,
        data:PromptUpdate
    ):

        return await self.repository.update(
            prompt_id,
            data
        )



    async def delete_prompt(
        self,
        prompt_id:int
    ):

        return await self.repository.delete(
            prompt_id
        )