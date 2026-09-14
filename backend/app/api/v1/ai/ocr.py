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

from app.schemas.ocr import (
    OCRRequest,
    OCRResponse
)

from app.services.ocr_service import OCRService


router = APIRouter(
    prefix="/ai/ocr",
    tags=["AI OCR"]
)


# =========================================================
# Extract Text From File
# =========================================================

@router.post(
    "/extract",
    response_model=OCRResponse
)
async def extract_text(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):

    service = OCRService(db)


    try:

        result = await service.extract(
            file
        )

        return result


    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )



# =========================================================
# OCR From Existing Document
# =========================================================

@router.post(
    "/document/{document_id}",
    response_model=OCRResponse
)
async def process_document(
    document_id: int,
    db: AsyncSession = Depends(get_db)
):

    service = OCRService(db)


    result = await service.process_document(
        document_id
    )


    if not result:

        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )


    return result



# =========================================================
# OCR Configuration
# =========================================================

@router.get(
    "/providers"
)
async def list_ocr_providers():

    return {
        "providers": [
            {
                "name": "tesseract",
                "type": "local"
            },
            {
                "name": "azure_document_intelligence",
                "type": "cloud"
            },
            {
                "name": "google_vision",
                "type": "cloud"
            }
        ]
    }



# =========================================================
# Test OCR Provider
# =========================================================

@router.post(
    "/test"
)
async def test_ocr(
    request: OCRRequest,
    db: AsyncSession = Depends(get_db)
):

    service = OCRService(db)


    result = await service.test(
        request
    )


    return {
        "success": True,
        "characters_detected": len(result.text)
    }