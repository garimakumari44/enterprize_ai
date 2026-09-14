from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

from app.schemas.ai_chat import (
    ChatRequest,
    ChatResponse,
    StreamChatRequest
)

from app.services.ai_chat_service import AIChatService


router = APIRouter(
    prefix="/ai/chat",
    tags=["AI Chat"]
)



# =========================================================
# Normal Chat Completion
# =========================================================

@router.post(
    "/",
    response_model=ChatResponse
)
async def chat_completion(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):

    service = AIChatService(db)


    try:

        response = await service.chat(
            request
        )

        return response


    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )



# =========================================================
# Streaming Chat
# =========================================================

@router.post(
    "/stream"
)
async def stream_chat(
    request: StreamChatRequest,
    db: AsyncSession = Depends(get_db)
):

    service = AIChatService(db)


    try:

        return await service.stream(
            request
        )


    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )



# =========================================================
# Test Model
# =========================================================

@router.post(
    "/test"
)
async def test_model(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):

    service = AIChatService(db)


    result = await service.test_chat(
        request
    )


    return {
        "success": True,
        "response": result
    }



# =========================================================
# Token Estimate
# =========================================================

@router.post(
    "/tokens"
)
async def estimate_tokens(
    request: ChatRequest
):

    from app.utils.token_counter import count_tokens


    tokens = count_tokens(
        request.messages
    )


    return {
        "tokens": tokens
    }