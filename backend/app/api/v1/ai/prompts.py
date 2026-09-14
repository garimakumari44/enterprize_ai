from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

from app.schemas.prompt import (
    PromptCreate,
    PromptUpdate,
    PromptResponse,
    PromptVersionCreate
)

from app.services.prompt_service import PromptService


router = APIRouter(
    prefix="/ai/prompts",
    tags=["AI Prompts"]
)


# =========================================================
# Create Prompt
# =========================================================

@router.post(
    "/",
    response_model=PromptResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_prompt(
    data: PromptCreate,
    db: AsyncSession = Depends(get_db)
):

    service = PromptService(db)

    prompt = await service.create_prompt(
        data
    )

    return prompt



# =========================================================
# List Prompts
# =========================================================

@router.get(
    "/",
    response_model=list[PromptResponse]
)
async def list_prompts(
    category: str | None = None,
    tag: str | None = None,
    db: AsyncSession = Depends(get_db)
):

    service = PromptService(db)

    prompts = await service.list_prompts(
        category=category,
        tag=tag
    )

    return prompts



# =========================================================
# Get Prompt
# =========================================================

@router.get(
    "/{prompt_id}",
    response_model=PromptResponse
)
async def get_prompt(
    prompt_id: int,
    db: AsyncSession = Depends(get_db)
):

    service = PromptService(db)

    prompt = await service.get_prompt(
        prompt_id
    )


    if not prompt:

        raise HTTPException(
            status_code=404,
            detail="Prompt not found"
        )


    return prompt



# =========================================================
# Update Prompt
# =========================================================

@router.patch(
    "/{prompt_id}",
    response_model=PromptResponse
)
async def update_prompt(
    prompt_id: int,
    data: PromptUpdate,
    db: AsyncSession = Depends(get_db)
):

    service = PromptService(db)

    prompt = await service.update_prompt(
        prompt_id,
        data
    )


    if not prompt:

        raise HTTPException(
            status_code=404,
            detail="Prompt not found"
        )


    return prompt



# =========================================================
# Delete Prompt
# =========================================================

@router.delete(
    "/{prompt_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_prompt(
    prompt_id: int,
    db: AsyncSession = Depends(get_db)
):

    service = PromptService(db)

    deleted = await service.delete_prompt(
        prompt_id
    )


    if not deleted:

        raise HTTPException(
            status_code=404,
            detail="Prompt not found"
        )


    return None



# =========================================================
# Create Prompt Version
# =========================================================

@router.post(
    "/{prompt_id}/versions",
    response_model=PromptResponse
)
async def create_prompt_version(
    prompt_id: int,
    data: PromptVersionCreate,
    db: AsyncSession = Depends(get_db)
):

    service = PromptService(db)


    prompt = await service.create_version(
        prompt_id,
        data
    )


    if not prompt:

        raise HTTPException(
            status_code=404,
            detail="Prompt not found"
        )


    return prompt



# =========================================================
# Get Prompt Versions
# =========================================================

@router.get(
    "/{prompt_id}/versions"
)
async def get_versions(
    prompt_id: int,
    db: AsyncSession = Depends(get_db)
):

    service = PromptService(db)

    versions = await service.get_versions(
        prompt_id
    )

    return versions



# =========================================================
# Execute Prompt Test
# =========================================================

@router.post(
    "/{prompt_id}/test"
)
async def test_prompt(
    prompt_id: int,
    variables: dict,
    db: AsyncSession = Depends(get_db)
):

    service = PromptService(db)

    result = await service.test_prompt(
        prompt_id,
        variables
    )

    return result