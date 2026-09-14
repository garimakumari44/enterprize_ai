from fastapi import APIRouter, Depends, HTTPException

from app.schemas.explainability.explanation_schema import (
    ExplanationRequest,
    ExplanationResponse,
)

from app.services.explanation_service import ExplanationService

router = APIRouter(
    prefix="/explainability",
    tags=["Explainability"],
)


def get_service():
    return ExplanationService()


@router.post(
    "/explain",
    response_model=ExplanationResponse,
)
async def explain(
    request: ExplanationRequest,
    service: ExplanationService = Depends(get_service),
):
    """
    Generate an explanation for an AI response.
    """

    try:
        return await service.explain(request)

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@router.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "Explainability API",
    }