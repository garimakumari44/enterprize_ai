from app.repositories.ai.provider_repository import (
    ProviderRepository
)

from app.schemas.ai.provider_schema import (
    ProviderCreate,
    ProviderUpdate
)



class ProviderService:


    def __init__(
        self,
        repository:ProviderRepository
    ):

        self.repository = repository



    async def create_provider(
        self,
        data:ProviderCreate
    ):

        return await self.repository.create(
            data
        )



    async def get_provider(
        self,
        provider_id:int
    ):

        provider = await self.repository.get_by_id(
            provider_id
        )


        if not provider:

            raise Exception(
                "Provider not found"
            )


        return provider



    async def list_providers(
        self,
        organization_id:int
    ):

        return await self.repository.list_by_org(
            organization_id
        )



    async def update_provider(
        self,
        provider_id:int,
        data:ProviderUpdate
    ):

        return await self.repository.update(
            provider_id,
            data
        )



    async def delete_provider(
        self,
        provider_id:int
    ):

        return await self.repository.delete(
            provider_id
        )



    async def test_connection(
        self,
        provider_id:int
    ):


        provider = await self.get_provider(
            provider_id
        )


        return {
            "provider":provider.name,
            "status":"connected"
        }