from __future__ import annotations

from azure.ai.documentintelligence.aio import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from azure.core.credentials import AzureKeyCredential

from app.core.config import settings
from app.ocr.base import (
    BaseOCR,
    OCRPage,
    OCRResult,
)


class AzureOCRProvider(BaseOCR):
    """
    Azure AI Document Intelligence OCR.

    pip install azure-ai-documentintelligence
    """

    def __init__(self):

        self.client = DocumentIntelligenceClient(
            endpoint=settings.AZURE_DOCUMENT_ENDPOINT,
            credential=AzureKeyCredential(
                settings.AZURE_DOCUMENT_KEY,
            ),
        )

    async def extract(
        self,
        file_path: str,
    ) -> OCRResult:

        with open(file_path, "rb") as f:

            poller = await self.client.begin_analyze_document(
                "prebuilt-read",
                AnalyzeDocumentRequest(
                    bytes_source=f.read(),
                ),
            )

        result = await poller.result()

        pages = []
        texts = []

        for page in result.pages:

            lines = []

            for line in page.lines:
                lines.append(line.content)

            page_text = "\n".join(lines)

            pages.append(
                OCRPage(
                    page_number=page.page_number,
                    text=page_text,
                )
            )

            texts.append(page_text)

        return OCRResult(
            text="\n".join(texts),
            pages=pages,
            metadata={
                "engine": "Azure Document Intelligence",
            },
        )