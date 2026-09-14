"""
app.processing.providers.extraction

Provider contract for document text extraction.

The extraction layer converts an input document into structured text
that downstream processing stages can consume.

Typical flow:

    Stored document
          |
          v
    ExtractionProvider
          |
          v
    ExtractedDocument
          |
          +--> pages
          +--> text
          +--> metadata
          +--> tables
          +--> warnings
          |
          v
    OCR / Classification / Layout
"""

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from .base import (
    BaseProcessingProvider,
    ProviderResult,
)
from .capabilities import (
    ProviderCapability,
)


@dataclass(slots=True)
class ExtractedPage:
    """
    Structured representation of one extracted page.
    """

    page_number: int

    text: str = ""

    width: float | None = None

    height: float | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    tables: list[Any] = field(
        default_factory=list
    )

    blocks: list[Any] = field(
        default_factory=list
    )

    images: list[Any] = field(
        default_factory=list
    )

    confidence: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert the page to a serializable dictionary."""

        return {
            "page_number": self.page_number,
            "text": self.text,
            "width": self.width,
            "height": self.height,
            "metadata": dict(self.metadata),
            "tables": list(self.tables),
            "blocks": list(self.blocks),
            "images": list(self.images),
            "confidence": self.confidence,
        }


@dataclass(slots=True)
class ExtractedDocument:
    """
    Canonical output of the extraction stage.
    """

    document_id: str | None = None

    source_path: str | None = None

    filename: str | None = None

    mime_type: str | None = None

    text: str = ""

    pages: list[ExtractedPage] = field(
        default_factory=list
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    tables: list[Any] = field(
        default_factory=list
    )

    images: list[Any] = field(
        default_factory=list
    )

    warnings: list[str] = field(
        default_factory=list
    )

    errors: list[str] = field(
        default_factory=list
    )

    language: str | None = None

    extraction_method: str | None = None

    confidence: float | None = None

    @property
    def page_count(self) -> int:
        """Return the number of extracted pages."""

        return len(self.pages)

    @property
    def character_count(self) -> int:
        """Return total extracted character count."""

        return len(self.text)

    @property
    def word_count(self) -> int:
        """Return approximate extracted word count."""

        return len(
            self.text.split()
        )

    @property
    def has_text(self) -> bool:
        """Return whether meaningful text was extracted."""

        return bool(
            self.text.strip()
        )

    @property
    def needs_ocr(self) -> bool:
        """
        Return whether the document appears to require OCR.

        A document with pages but no extracted text is considered
        a candidate for OCR.
        """

        return (
            self.page_count > 0
            and not self.has_text
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert the extracted document to a serializable dictionary."""

        return {
            "document_id": self.document_id,
            "source_path": self.source_path,
            "filename": self.filename,
            "mime_type": self.mime_type,
            "text": self.text,
            "pages": [
                page.to_dict()
                for page in self.pages
            ],
            "metadata": dict(self.metadata),
            "tables": list(self.tables),
            "images": list(self.images),
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "language": self.language,
            "extraction_method": self.extraction_method,
            "confidence": self.confidence,
            "page_count": self.page_count,
            "character_count": self.character_count,
            "word_count": self.word_count,
            "needs_ocr": self.needs_ocr,
        }


@dataclass(slots=True)
class ExtractionRequest:
    """
    Input contract for extraction providers.

    `source_path` is normally the path supplied by the processing
    infrastructure after the document has been retrieved from object
    storage.

    `content` can be used when the caller already has the document
    bytes in memory.
    """

    source_path: str | None = None

    content: bytes | None = None

    filename: str | None = None

    mime_type: str | None = None

    document_id: str | None = None

    options: dict[str, Any] = field(
        default_factory=dict
    )

    def validate(self) -> None:
        """Validate the extraction request."""

        if (
            self.source_path is None
            and self.content is None
        ):
            raise ValueError(
                "ExtractionRequest requires either "
                "source_path or content."
            )

        if (
            self.source_path is not None
            and not isinstance(
                self.source_path,
                str,
            )
        ):
            raise TypeError(
                "source_path must be a string or None."
            )

        if self.content is not None and not isinstance(
            self.content,
            bytes,
        ):
            raise TypeError(
                "content must be bytes or None."
            )

        if self.filename is not None:
            if not isinstance(
                self.filename,
                str,
            ):
                raise TypeError(
                    "filename must be a string or None."
                )

        if self.mime_type is not None:
            if not isinstance(
                self.mime_type,
                str,
            ):
                raise TypeError(
                    "mime_type must be a string or None."
                )


class BaseExtractionProvider(
    BaseProcessingProvider
):
    """
    Base contract for all document extraction providers.

    Concrete implementations may include:

        PdfExtractor
        DocxExtractor
        ImageExtractor
        OfficeExtractor
        UniversalExtractor
    """

    PROVIDER_TYPE = "extraction"

    PROCESSING_STAGE = "text_extraction"

    def capabilities(self) -> set[str]:
        """Return standard extraction capabilities."""

        return {
            ProviderCapability.TEXT_EXTRACTION.value,
        }

    @abstractmethod
    async def extract(
        self,
        request: ExtractionRequest,
    ) -> ExtractedDocument:
        """
        Extract text and document structure.

        Implementations must return an ExtractedDocument.

        Raises:
            ProviderError:
                When extraction cannot be completed.
        """

        raise NotImplementedError

    async def process(
        self,
        request: ExtractionRequest,
    ) -> ProviderResult:
        """
        Standard provider entry point.

        This wraps the domain-specific `extract()` method in the common
        ProviderResult contract.
        """

        request.validate()

        extracted = await self.extract(
            request
        )

        return ProviderResult.ok(
            provider=self.name,
            operation="extract",
            data=extracted.to_dict(),
            metadata={
                "document_id": extracted.document_id,
                "filename": extracted.filename,
                "mime_type": extracted.mime_type,
                "page_count": extracted.page_count,
                "character_count": extracted.character_count,
                "word_count": extracted.word_count,
                "needs_ocr": extracted.needs_ocr,
                "extraction_method": (
                    extracted.extraction_method
                ),
            },
            warnings=extracted.warnings,
        )

    def supports_mime_type(
        self,
        mime_type: str | None,
    ) -> bool:
        """
        Return whether the provider supports a MIME type.

        Base implementation accepts all MIME types. Concrete providers
        should override this.
        """

        return bool(mime_type)

    def supported_mime_types(
        self,
    ) -> Sequence[str]:
        """
        Return supported MIME types.

        Base implementation returns an empty sequence, meaning that
        the provider does not advertise specific MIME types.
        """

        return ()

    def supports_extension(
        self,
        extension: str | None,
    ) -> bool:
        """
        Return whether the provider supports a file extension.
        """

        if not extension:
            return False

        normalized = extension.lower().strip()

        if not normalized.startswith("."):
            normalized = (
                "." + normalized
            )

        supported = {
            item.lower()
            for item in self.supported_extensions()
        }

        return normalized in supported

    def supported_extensions(
        self,
    ) -> Sequence[str]:
        """Return supported file extensions."""

        return ()

    def normalize_result(
        self,
        document: ExtractedDocument,
    ) -> ExtractedDocument:
        """
        Normalize an extraction result.

        This provides a central place for common cleanup without
        forcing concrete providers to duplicate it.
        """

        document.text = (
            document.text
            if isinstance(
                document.text,
                str,
            )
            else str(document.text or "")
        )

        for page in document.pages:
            page.text = (
                page.text
                if isinstance(
                    page.text,
                    str,
                )
                else str(page.text or "")
            )

        return document

