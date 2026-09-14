from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

from app.schemas.embedding import (
    EmbeddingRequest,
    EmbeddingResponse,
    BatchEmbeddingRequest,
    SimilarityRequest
)

from app.services.embedding_service import EmbeddingService


router = APIRouter(
    prefix="/ai/embeddings",
    tags=["AI Embeddings"]
)


# =========================================================
# Generate Single Embedding
# =========================================================

@router.post(
    "/",
    response_model=EmbeddingResponse
)
async def create_embedding(
    request: EmbeddingRequest,
    db: AsyncSession = Depends(get_db)
):

    service = EmbeddingService(db)

    try:

        result = await service.generate(
            request
        )

        return result


    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )



# =========================================================
# Batch Embeddings
# =========================================================

@router.post(
    "/batch",
    response_model=list[EmbeddingResponse]
)
async def create_batch_embeddings(
    request: BatchEmbeddingRequest,
    db: AsyncSession = Depends(get_db)
):

    service = EmbeddingService(db)


    try:

        result = await service.generate_batch(
            request
        )

        return result


    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )



# =========================================================
# Similarity Search
# =========================================================

@router.post(
    "/similarity"
)
async def calculate_similarity(
    request: SimilarityRequest
):

    service = EmbeddingService(None)


    score = await service.similarity(
        request
    )


    return {
        "similarity": score
    }



# =========================================================
# Estimate Tokens
# =========================================================

@router.post(
    "/tokens"
)
async def estimate_embedding_tokens(
    request: EmbeddingRequest
):

    from app.utils.token_counter import count_tokens


    tokens = count_tokens(
        [request.text]
    )


    return {
        "tokens": tokens
    }



# =========================================================
# Test Embedding Model
# =========================================================

@router.post(
    "/test"
)
async def test_embedding_model(
    request: EmbeddingRequest,
    db: AsyncSession = Depends(get_db)
):

    service = EmbeddingService(db)


    result = await service.test(
        request
    )


    return {
        "success": True,
        "dimension": len(result)
    }