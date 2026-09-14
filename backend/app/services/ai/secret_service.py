from app.repositories.ai.secret_repository import (
    SecretRepository
)

from app.core.security import (
    encrypt_secret,
    decrypt_secret
)


class SecretService:


    def __init__(
        self,
        repository:SecretRepository
    ):

        self.repository = repository



    async def create_secret(
        self,
        name:str,
        value:str,
        organization_id:int
    ):


        encrypted_value = encrypt_secret(
            value
        )


        return await self.repository.create(
            {
                "name":name,
                "value":encrypted_value,
                "organization_id":organization_id
            }
        )



    async def get_secret(
        self,
        secret_id:int
    ):


        secret = await self.repository.get_by_id(
            secret_id
        )


        if not secret:

            raise Exception(
                "Secret not found"
            )


        return secret



    async def get_secret_value(
        self,
        secret_id:int
    ):


        secret = await self.get_secret(
            secret_id
        )


        return decrypt_secret(
            secret.value
        )



    async def delete_secret(
        self,
        secret_id:int
    ):

        return await self.repository.delete(
            secret_id
        )