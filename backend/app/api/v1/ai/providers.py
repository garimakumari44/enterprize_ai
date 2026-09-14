from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

from app.schemas.ai_provider import (
    AIProviderCreate,
    AIProviderResponse,
    AIProviderUpdate
)

from app.services.ai_provider_service import AIProviderService


router = APIRouter(
    prefix="/ai/providers",
    tags=["AI Providers"]
)


# ---------------------------------------------------------
# Create AI Provider
# ---------------------------------------------------------

@router.post(
    "/",
    response_model=AIProviderResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_provider(
    data: AIProviderCreate,
    db: AsyncSession = Depends(get_db)
):

    service = AIProviderService(db)

    provider = await service.create_provider(
        data
    )

    return provider



# ---------------------------------------------------------
# List Providers
# ---------------------------------------------------------

@router.get(
    "/",
    response_model=list[AIProviderResponse]
)
async def list_providers(
    db: AsyncSession = Depends(get_db)
):

    service = AIProviderService(db)

    providers = await service.list_providers()

    return providers



# ---------------------------------------------------------
# Get Provider
# ---------------------------------------------------------

@router.get(
    "/{provider_id}",
    response_model=AIProviderResponse
)
async def get_provider(
    provider_id: int,
    db: AsyncSession = Depends(get_db)
):

    service = AIProviderService(db)

    provider = await service.get_provider(
        provider_id
    )

    if not provider:
        raise HTTPException(
            status_code=404,
            detail="AI provider not found"
        )

    return provider



# ---------------------------------------------------------
# Update Provider
# ---------------------------------------------------------

@router.patch(
    "/{provider_id}",
    response_model=AIProviderResponse
)
async def update_provider(
    provider_id: int,
    data: AIProviderUpdate,
    db: AsyncSession = Depends(get_db)
):

    service = AIProviderService(db)

    provider = await service.update_provider(
        provider_id,
        data
    )

    if not provider:
        raise HTTPException(
            status_code=404,
            detail="AI provider not found"
        )

    return provider



# ---------------------------------------------------------
# Delete Provider
# ---------------------------------------------------------

@router.delete(
    "/{provider_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_provider(
    provider_id: int,
    db: AsyncSession = Depends(get_db)
):

    service = AIProviderService(db)

    deleted = await service.delete_provider(
        provider_id
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="AI provider not found"
        )

    return None



# ---------------------------------------------------------
# Test Provider Connection
# ---------------------------------------------------------

@router.post(
    "/{provider_id}/test"
)
async def test_provider(
    provider_id: int,
    db: AsyncSession = Depends(get_db)
):

    service = AIProviderService(db)

    result = await service.test_connection(
        provider_id
    )

    return {
        "provider_id": provider_id,
        "status": result
    }