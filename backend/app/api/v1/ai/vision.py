from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    status
)

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

from app.schemas.vision import (
    VisionRequest,
    VisionResponse,
    ImageAnalysisRequest
)

from app.services.vision_service import VisionService


router = APIRouter(
    prefix="/ai/vision",
    tags=["AI Vision"]
)


# =========================================================
# Analyze Image
# =========================================================

@router.post(
    "/analyze",
    response_model=VisionResponse
)
async def analyze_image(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):

    service = VisionService(db)

    try:

        result = await service.analyze(
            file
        )

        return result


    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )



# =========================================================
# Vision Question Answering
# =========================================================

@router.post(
    "/ask",
    response_model=VisionResponse
)
async def ask_about_image(
    request: VisionRequest,
    db: AsyncSession = Depends(get_db)
):

    service = VisionService(db)


    try:

        result = await service.ask(
            request
        )

        return result


    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )



# =========================================================
# Analyze Existing Document Image
# =========================================================

@router.post(
    "/document/{document_id}",
    response_model=VisionResponse
)
async def analyze_document_image(
    document_id: int,
    db: AsyncSession = Depends(get_db)
):

    service = VisionService(db)


    result = await service.analyze_document(
        document_id
    )


    if not result:

        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )


    return result



# =========================================================
# Batch Image Analysis
# =========================================================

@router.post(
    "/batch",
    response_model=list[VisionResponse]
)
async def batch_analysis(
    files: list[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db)
):

    service = VisionService(db)


    results = await service.batch_analyze(
        files
    )


    return results



# =========================================================
# Available Vision Models
# =========================================================

@router.get(
    "/models"
)
async def vision_models():

    return {
        "models": [
            {
                "name": "gpt-5-vision",
                "capabilities": [
                    "image_analysis",
                    "ocr",
                    "reasoning"
                ]
            },
            {
                "name": "gemini-vision",
                "capabilities": [
                    "image_analysis",
                    "document_understanding"
                ]
            }
        ]
    }



# =========================================================
# Test Vision Provider
# =========================================================

@router.post(
    "/test"
)
async def test_vision(
    request: ImageAnalysisRequest,
    db: AsyncSession = Depends(get_db)
):

    service = VisionService(db)


    result = await service.test(
        request
    )


    return {
        "success": True,
        "response": result
    }