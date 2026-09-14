
"""
app.processing.providers.implementations.pdf_extractor

Local PDF extraction provider backed by PyMuPDF.

Responsibilities
----------------
- Extract text from PDF files.
- Preserve page boundaries.
- Preserve page dimensions.
- Expose basic PDF metadata.
- Support both filesystem paths and in-memory bytes.
- Never require PyMuPDF at application import time.

The provider implements the canonical BaseExtractionProvider contract.
"""

from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Any

from ..extraction import (
    BaseExtractionProvider,
    ExtractedDocument,
    ExtractedPage,
    ExtractionRequest,
)
from ..base import (
    ProviderConfigurationError,
    ProviderUnavailableError,
)


logger = logging.getLogger(__name__)


class PDFExtractor(BaseExtractionProvider):
    """
    PDF text extraction provider using PyMuPDF.

    Configuration
    -------------

    Supported configuration values:

        strict:
            When True, unsupported/corrupt PDFs raise an exception.

        include_images:
            Whether basic image metadata should be collected.

        include_blocks:
            Whether PyMuPDF text blocks should be collected.

    Example:

        provider = PDFExtractor(
            config={
                "include_blocks": True,
                "include_images": False,
            }
        )
    """

    PROVIDER_NAME = "pdf_extractor"

    PROVIDER_TYPE = "extraction"

    VERSION = "1.0"

    SUPPORTED_MIME_TYPES = (
        "application/pdf",
    )

    SUPPORTED_EXTENSIONS = (
        ".pdf",
    )

    def __init__(
        self,
        *,
        config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            config=config
        )

        self._fitz = None

    def _load_fitz(self):
        """
        Lazily import PyMuPDF.

        This prevents an optional dependency from breaking application
        startup when PDF processing is not being used.
        """

        if self._fitz is not None:
            return self._fitz

        try:
            import fitz  # type: ignore
        except ImportError as exc:
            raise ProviderUnavailableError(
                "PyMuPDF is not installed. "
                "Install it with: pip install pymupdf"
            ) from exc

        self._fitz = fitz

        return fitz

    async def health_check(self) -> bool:
        """
        Check whether PyMuPDF is available.
        """

        try:
            self._load_fitz()
            return True
        except ProviderUnavailableError:
            return False

    def validate_config(self) -> None:
        """
        Validate PDF extractor configuration.
        """

        for key in (
            "include_images",
            "include_blocks",
            "strict",
        ):
            value = self.get_config(
                key
            )

            if value is not None and not isinstance(
                value,
                bool,
            ):
                raise ProviderConfigurationError(
                    f"'{key}' must be a boolean."
                )

    def supported_mime_types(
        self,
    ) -> tuple[str, ...]:
        return self.SUPPORTED_MIME_TYPES

    def supported_extensions(
        self,
    ) -> tuple[str, ...]:
        return self.SUPPORTED_EXTENSIONS

    def supports_mime_type(
        self,
        mime_type: str | None,
    ) -> bool:
        if not mime_type:
            return False

        normalized = (
            mime_type.strip().lower()
        )

        return normalized in self.SUPPORTED_MIME_TYPES

    def _resolve_filename(
        self,
        request: ExtractionRequest,
    ) -> str | None:
        if request.filename:
            return request.filename

        if request.source_path:
            return Path(
                request.source_path
            ).name

        return None

    def _read_content(
        self,
        request: ExtractionRequest,
    ) -> bytes | str:
        if request.content is not None:
            return request.content

        if not request.source_path:
            raise ValueError(
                "PDF extraction requires source_path or content."
            )

        path = Path(
            request.source_path
        )

        if not path.exists():
            raise FileNotFoundError(
                f"PDF source does not exist: {path}"
            )

        if not path.is_file():
            raise ValueError(
                f"PDF source is not a file: {path}"
            )

        return str(path)

    def _extract_page_blocks(
        self,
        page,
    ) -> list[dict[str, Any]]:
        """
        Extract basic text-block geometry from a PyMuPDF page.
        """

        blocks: list[dict[str, Any]] = []

        try:
            raw_blocks = page.get_text(
                "blocks"
            )
        except Exception as exc:
            logger.debug(
                "Unable to extract PDF blocks: %s",
                exc,
            )
            return blocks

        for index, block in enumerate(
            raw_blocks
        ):
            if len(block) < 5:
                continue

            x0, y0, x1, y1, text = block[:5]

            blocks.append(
                {
                    "block_id": f"block-{index}",
                    "bbox": {
                        "x1": float(x0),
                        "y1": float(y0),
                        "x2": float(x1),
                        "y2": float(y1),
                    },
                    "text": str(
                        text or ""
                    ).strip(),
                }
            )

        return blocks

    def _extract_images(
        self,
        page,
    ) -> list[dict[str, Any]]:
        """
        Extract basic image references without storing image bytes.
        """

        try:
            images = page.get_images(
                full=True
            )
        except Exception as exc:
            logger.debug(
                "Unable to inspect PDF images: %s",
                exc,
            )
            return []

        result: list[dict[str, Any]] = []

        for index, image in enumerate(
            images
        ):
            result.append(
                {
                    "image_index": index,
                    "xref": (
                        image[0]
                        if image
                        else None
                    ),
                }
            )

        return result

    async def extract(
        self,
        request: ExtractionRequest,
    ) -> ExtractedDocument:
        """
        Extract text and basic structural information from a PDF.
        """

        request.validate()

        fitz = self._load_fitz()

        content = self._read_content(
            request
        )

        include_blocks = bool(
            self.get_config(
                "include_blocks",
                True,
            )
        )

        include_images = bool(
            self.get_config(
                "include_images",
                False,
            )
        )

        strict = bool(
            self.get_config(
                "strict",
                True,
            )
        )

        filename = self._resolve_filename(
            request
        )

        document = ExtractedDocument(
            document_id=request.document_id,
            source_path=request.source_path,
            filename=filename,
            mime_type=(
                request.mime_type
                or "application/pdf"
            ),
            extraction_method="pymupdf",
        )

        pdf = None

        try:
            if isinstance(
                content,
                bytes,
            ):
                pdf = fitz.open(
                    stream=io.BytesIO(content),
                    filetype="pdf",
                )
            else:
                pdf = fitz.open(
                    content
                )

            metadata = dict(
                pdf.metadata or {}
            )

            document.metadata.update(
                {
                    "pdf_metadata": metadata,
                    "page_count": len(pdf),
                }
            )

            all_text: list[str] = []

            for page_index in range(
                len(pdf)
            ):
                page = pdf[
                    page_index
                ]

                page_number = (
                    page_index + 1
                )

                page_text = page.get_text(
                    "text"
                )

                page_text = (
                    page_text
                    if isinstance(
                        page_text,
                        str,
                    )
                    else str(
                        page_text or ""
                    )
                ).strip()

                rect = page.rect

                page_metadata: dict[str, Any] = {}

                blocks: list[Any] = []

                if include_blocks:
                    blocks = self._extract_page_blocks(
                        page
                    )

                images: list[Any] = []

                if include_images:
                    images = self._extract_images(
                        page
                    )

                extracted_page = ExtractedPage(
                    page_number=page_number,
                    text=page_text,
                    width=float(
                        rect.width
                    ),
                    height=float(
                        rect.height
                    ),
                    metadata=page_metadata,
                    blocks=blocks,
                    images=images,
                )

                document.pages.append(
                    extracted_page
                )

                if page_text:
                    all_text.append(
                        page_text
                    )

            document.text = "\n\n".join(
                all_text
            ).strip()

            document.metadata[
                "character_count"
            ] = len(
                document.text
            )

            document.metadata[
                "word_count"
            ] = len(
                document.text.split()
            )

            if not document.has_text:
                document.warnings.append(
                    "No text was extracted from the PDF; "
                    "the document may require OCR."
                )

            if document.page_count == 0:
                document.warnings.append(
                    "PDF contains no pages."
                )

            return self.normalize_result(
                document
            )

        except Exception as exc:
            logger.exception(
                "PDF extraction failed: %s",
                request.source_path,
            )

            if strict:
                raise

            document.errors.append(
                str(exc)
            )

            document.warnings.append(
                "PDF extraction completed with errors."
            )

            return document

        finally:
            if pdf is not None:
                try:
                    pdf.close()
                except Exception:
                    logger.debug(
                        "Failed to close PDF document.",
                        exc_info=True,
                    )

