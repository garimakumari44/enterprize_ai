from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

from app.schemas.ai_model import (
    AIModelCreate,
    AIModelUpdate,
    AIModelResponse
)

from app.services.ai_model_service import AIModelService


router = APIRouter(
    prefix="/ai/models",
    tags=["AI Models"]
)


# =========================================================
# Create AI Model
# =========================================================

@router.post(
    "/",
    response_model=AIModelResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_model(
    data: AIModelCreate,
    db: AsyncSession = Depends(get_db)
):

    service = AIModelService(db)

    model = await service.create_model(
        data
    )

    return model



# =========================================================
# List Models
# =========================================================

@router.get(
    "/",
    response_model=list[AIModelResponse]
)
async def list_models(
    provider_id: int | None = None,
    capability: str | None = None,
    db: AsyncSession = Depends(get_db)
):

    service = AIModelService(db)

    models = await service.list_models(
        provider_id=provider_id,
        capability=capability
    )

    return models



# =========================================================
# Get Model
# =========================================================

@router.get(
    "/{model_id}",
    response_model=AIModelResponse
)
async def get_model(
    model_id: int,
    db: AsyncSession = Depends(get_db)
):

    service = AIModelService(db)

    model = await service.get_model(
        model_id
    )


    if not model:
        raise HTTPException(
            status_code=404,
            detail="AI model not found"
        )


    return model



# =========================================================
# Update Model
# =========================================================

@router.patch(
    "/{model_id}",
    response_model=AIModelResponse
)
async def update_model(
    model_id: int,
    data: AIModelUpdate,
    db: AsyncSession = Depends(get_db)
):

    service = AIModelService(db)

    model = await service.update_model(
        model_id,
        data
    )


    if not model:
        raise HTTPException(
            status_code=404,
            detail="AI model not found"
        )


    return model



# =========================================================
# Delete Model
# =========================================================

@router.delete(
    "/{model_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_model(
    model_id: int,
    db: AsyncSession = Depends(get_db)
):

    service = AIModelService(db)

    deleted = await service.delete_model(
        model_id
    )


    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="AI model not found"
        )


    return None



# =========================================================
# Enable / Disable Model
# =========================================================

@router.post(
    "/{model_id}/toggle",
    response_model=AIModelResponse
)
async def toggle_model(
    model_id: int,
    db: AsyncSession = Depends(get_db)
):

    service = AIModelService(db)

    model = await service.toggle_model(
        model_id
    )


    if not model:
        raise HTTPException(
            status_code=404,
            detail="AI model not found"
        )


    return model



# =========================================================
# Get Models By Capability
# =========================================================

@router.get(
    "/capabilities/{capability}",
    response_model=list[AIModelResponse]
)
async def models_by_capability(
    capability: str,
    db: AsyncSession = Depends(get_db)
):

    service = AIModelService(db)

    models = await service.get_by_capability(
        capability
    )

    return models