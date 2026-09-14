
"""
app.processing.providers.implementations.azure_ocr

Azure Document Intelligence OCR provider.

This implementation provides OCR through Microsoft's Azure AI
Document Intelligence service.

Design goals
------------

- Implements the canonical OCR provider contract.
- Uses lazy Azure SDK imports.
- Does not require Azure dependencies merely to import the module.
- Supports endpoint/key configuration through constructor config.
- Supports local file paths and in-memory bytes when supported by the
  OCR request contract.
- Converts Azure's response into the application's canonical OCR
  result structures.

Expected configuration
----------------------

    {
        "endpoint": "https://<resource>.cognitiveservices.azure.com/",
        "api_key": "<secret>",
        "model": "prebuilt-read"
    }

Environment variables can also be used:

    AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT
    AZURE_DOCUMENT_INTELLIGENCE_API_KEY

The SDK is imported only when OCR is actually used.

Dependency
----------

    pip install azure-ai-documentintelligence

Depending on the version of the Azure SDK, the client API may differ.
This implementation supports the current Azure Document Intelligence
client interface while keeping SDK-specific code isolated here.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Mapping

from ..base import (
    ProviderConfigurationError,
    ProviderUnavailableError,
)
from ..ocr import (
    BaseOCRProvider,
    OCRRequest,
    OCRResult,
    OCRPage,
    OCRTextBlock,
)


logger = logging.getLogger(__name__)


class AzureOCRProvider(BaseOCRProvider):
    """
    Azure AI Document Intelligence OCR provider.

    Provider name:
        azure_ocr

    Processing stage:
        ocr

    Default Azure model:
        prebuilt-read
    """

    PROVIDER_NAME = "azure_ocr"

    PROVIDER_TYPE = "ocr"

    VERSION = "1.0"

    DEFAULT_MODEL = "prebuilt-read"

    def __init__(
        self,
        *,
        config: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(
            config=config
        )

        self._client = None

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    @property
    def endpoint(self) -> str | None:
        """
        Return Azure Document Intelligence endpoint.

        Configuration takes precedence over environment variables.
        """

        value = self.get_config(
            "endpoint"
        )

        if value is None:
            value = os.getenv(
                "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT"
            )

        if value is None:
            # Also support the commonly used Azure variable name.
            value = os.getenv(
                "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT_URL"
            )

        if value is None:
            return None

        value = str(
            value
        ).strip()

        return value or None

    @property
    def api_key(self) -> str | None:
        """
        Return Azure API key.

        Configuration takes precedence over environment variables.
        """

        value = self.get_config(
            "api_key"
        )

        if value is None:
            value = os.getenv(
                "AZURE_DOCUMENT_INTELLIGENCE_API_KEY"
            )

        if value is None:
            # Backwards-compatible/common Azure naming.
            value = os.getenv(
                "AZURE_DOCUMENT_INTELLIGENCE_KEY"
            )

        if value is None:
            return None

        value = str(
            value
        ).strip()

        return value or None

    @property
    def model(self) -> str:
        """
        Return Azure analysis model.
        """

        value = self.get_config(
            "model",
            self.DEFAULT_MODEL,
        )

        value = str(
            value
        ).strip()

        return (
            value
            or self.DEFAULT_MODEL
        )

    def validate_config(self) -> None:
        """
        Validate provider configuration.

        We allow missing Azure configuration during object creation so
        that the provider can be registered without immediately
        requiring credentials.

        Actual OCR execution requires endpoint and API key.
        """

        if self.endpoint:
            if not (
                self.endpoint.startswith(
                    "https://"
                )
                or self.endpoint.startswith(
                    "http://"
                )
            ):
                raise ProviderConfigurationError(
                    "Azure Document Intelligence endpoint "
                    "must be a valid HTTP/HTTPS URL."
                )

        if self.model == "":
            raise ProviderConfigurationError(
                "Azure OCR model cannot be empty."
            )

    def _validate_runtime_configuration(
        self,
    ) -> None:
        """
        Validate configuration required for an actual Azure request.
        """

        self.validate_config()

        if not self.endpoint:
            raise ProviderConfigurationError(
                "Azure Document Intelligence endpoint is not configured. "
                "Set 'endpoint' in provider config or "
                "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT."
            )

        if not self.api_key:
            raise ProviderConfigurationError(
                "Azure Document Intelligence API key is not configured. "
                "Set 'api_key' in provider config or "
                "AZURE_DOCUMENT_INTELLIGENCE_API_KEY."
            )

    # ------------------------------------------------------------------
    # Capabilities
    # ------------------------------------------------------------------

    def supported_mime_types(
        self,
    ) -> tuple[str, ...]:
        return (
            "application/pdf",
            "image/png",
            "image/jpeg",
            "image/jpg",
            "image/tiff",
            "image/bmp",
            "image/webp",
        )

    # ------------------------------------------------------------------
    # Azure SDK
    # ------------------------------------------------------------------

    def _load_azure_client_class(self):
        """
        Lazily import Azure Document Intelligence SDK.

        This is intentionally done at runtime instead of module import
        time so that:

            from app.processing.providers.implementations import *

        does not fail when Azure OCR is not installed.
        """

        try:
            from azure.ai.documentintelligence import (
                DocumentIntelligenceClient,
            )
        except ImportError as exc:
            raise ProviderUnavailableError(
                "Azure Document Intelligence SDK is not installed. "
                "Install it with: "
                "pip install azure-ai-documentintelligence"
            ) from exc

        return DocumentIntelligenceClient

    def _load_azure_credential_class(self):
        """
        Lazily import Azure credential support.
        """

        try:
            from azure.core.credentials import (
                AzureKeyCredential,
            )
        except ImportError as exc:
            raise ProviderUnavailableError(
                "Azure Core SDK is not installed. "
                "Install it with: "
                "pip install azure-core"
            ) from exc

        return AzureKeyCredential

    def _ensure_client(self):
        """
        Create the Azure Document Intelligence client lazily.
        """

        if self._client is not None:
            return self._client

        self._validate_runtime_configuration()

        DocumentIntelligenceClient = (
            self._load_azure_client_class()
        )

        AzureKeyCredential = (
            self._load_azure_credential_class()
        )

        try:
            credential = AzureKeyCredential(
                self.api_key
            )

            self._client = (
                DocumentIntelligenceClient(
                    endpoint=self.endpoint,
                    credential=credential,
                )
            )

        except Exception as exc:
            logger.exception(
                "Failed to initialize Azure "
                "Document Intelligence client."
            )

            raise ProviderUnavailableError(
                "Failed to initialize Azure Document "
                f"Intelligence client: {exc}"
            ) from exc

        return self._client

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    async def health_check(self) -> bool:
        """
        Check whether Azure OCR can be used.

        Health checking intentionally verifies configuration and SDK
        availability without sending a billable OCR request.
        """

        try:
            self._validate_runtime_configuration()

            self._load_azure_client_class()
            self._load_azure_credential_class()

            return True

        except (
            ProviderConfigurationError,
            ProviderUnavailableError,
        ):
            return False

    # ------------------------------------------------------------------
    # Input handling
    # ------------------------------------------------------------------

    def _get_source_path(
        self,
        request: OCRRequest,
    ) -> str | None:
        """
        Extract source path from the canonical OCR request.

        The contract may provide the path using different names across
        application versions, so this method handles the common forms.
        """

        for attribute in (
            "source_path",
            "file_path",
            "path",
        ):
            value = getattr(
                request,
                attribute,
                None,
            )

            if value:
                return str(
                    value
                )

        return None

    def _get_content(
        self,
        request: OCRRequest,
    ) -> bytes | None:
        """
        Extract raw content from the canonical OCR request.
        """

        for attribute in (
            "content",
            "file_bytes",
            "data",
            "bytes",
        ):
            value = getattr(
                request,
                attribute,
                None,
            )

            if value is None:
                continue

            if isinstance(
                value,
                bytes,
            ):
                return value

            if isinstance(
                value,
                bytearray,
            ):
                return bytes(
                    value
                )

        return None

    def _get_filename(
        self,
        request: OCRRequest,
    ) -> str | None:
        value = getattr(
            request,
            "filename",
            None,
        )

        if value:
            return str(
                value
            )

        source_path = (
            self._get_source_path(
                request
            )
        )

        if source_path:
            return Path(
                source_path
            ).name

        return None

    # ------------------------------------------------------------------
    # Azure response helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _safe_float(
        value: Any,
    ) -> float | None:
        if value is None:
            return None

        try:
            return float(
                value
            )
        except (
            TypeError,
            ValueError,
        ):
            return None

    @staticmethod
    def _safe_int(
        value: Any,
    ) -> int | None:
        if value is None:
            return None

        try:
            return int(
                value
            )
        except (
            TypeError,
            ValueError,
        ):
            return None

    @staticmethod
    def _get_attr(
        obj: Any,
        name: str,
        default: Any = None,
    ) -> Any:
        """
        Safely access either object attributes or mappings.
        """

        if obj is None:
            return default

        if isinstance(
            obj,
            Mapping,
        ):
            return obj.get(
                name,
                default,
            )

        return getattr(
            obj,
            name,
            default,
        )

    def _polygon_to_bbox(
        self,
        polygon: Any,
    ) -> dict[str, float] | None:
        """
        Convert Azure polygon coordinates into a bounding box.
        """

        if not polygon:
            return None

        points: list[tuple[float, float]] = []

        try:
            values = list(
                polygon
            )
        except TypeError:
            return None

        # Azure SDK versions may expose polygon points either as:
        #
        #   [x1, y1, x2, y2, ...]
        #
        # or objects containing x/y.

        if values and all(
            isinstance(
                value,
                (int, float),
            )
            for value in values
        ):
            if len(values) < 4:
                return None

            for index in range(
                0,
                len(values) - 1,
                2,
            ):
                try:
                    points.append(
                        (
                            float(
                                values[index]
                            ),
                            float(
                                values[index + 1]
                            ),
                        )
                    )
                except (
                    TypeError,
                    ValueError,
                ):
                    continue

        else:
            for point in values:
                x = self._get_attr(
                    point,
                    "x",
                )

                y = self._get_attr(
                    point,
                    "y",
                )

                if x is None or y is None:
                    continue

                try:
                    points.append(
                        (
                            float(x),
                            float(y),
                        )
                    )
                except (
                    TypeError,
                    ValueError,
                ):
                    continue

        if not points:
            return None

        xs = [
            point[0]
            for point in points
        ]

        ys = [
            point[1]
            for point in points
        ]

        return {
            "x1": min(xs),
            "y1": min(ys),
            "x2": max(xs),
            "y2": max(ys),
        }

    def _extract_page(
        self,
        azure_page: Any,
        page_number: int,
    ) -> OCRPage:
        """
        Convert one Azure page into the canonical OCRPage.
        """

        width = self._safe_float(
            self._get_attr(
                azure_page,
                "width",
            )
        )

        height = self._safe_float(
            self._get_attr(
                azure_page,
                "height",
            )
        )

        unit = self._get_attr(
            azure_page,
            "unit",
        )

        lines = (
            self._get_attr(
                azure_page,
                "lines",
                [],
            )
            or []
        )

        blocks: list[OCRTextBlock] = []

        for index, line in enumerate(
            lines
        ):
            content = self._get_attr(
                line,
                "content",
                "",
            )

            content = str(
                content or ""
            ).strip()

            if not content:
                continue

            polygon = self._get_attr(
                line,
                "polygon",
            )

            bbox = (
                self._polygon_to_bbox(
                    polygon
                )
            )

            blocks.append(
                OCRTextBlock(
                    block_id=(
                        f"page-{page_number}"
                        f"-block-{index}"
                    ),
                    text=content,
                    confidence=None,
                    bounding_box=bbox,
                    metadata={
                        "source": "azure",
                        "type": "line",
                    },
                )
            )

        # Some Azure responses may not contain lines but can contain
        # words. We do not duplicate words when lines are available.
        if not blocks:
            words = (
                self._get_attr(
                    azure_page,
                    "words",
                    [],
                )
                or []
            )

            for index, word in enumerate(
                words
            ):
                content = self._get_attr(
                    word,
                    "content",
                    "",
                )

                content = str(
                    content or ""
                ).strip()

                if not content:
                    continue

                polygon = self._get_attr(
                    word,
                    "polygon",
                )

                confidence = (
                    self._safe_float(
                        self._get_attr(
                            word,
                            "confidence",
                        )
                    )
                )

                blocks.append(
                    OCRTextBlock(
                        block_id=(
                            f"page-{page_number}"
                            f"-word-{index}"
                        ),
                        text=content,
                        confidence=confidence,
                        bounding_box=(
                            self._polygon_to_bbox(
                                polygon
                            )
                        ),
                        metadata={
                            "source": "azure",
                            "type": "word",
                        },
                    )
                )

        page_text = "\n".join(
            block.text
            for block in blocks
            if block.text
        ).strip()

        return OCRPage(
            page_number=page_number,
            text=page_text,
            width=width,
            height=height,
            metadata={
                "unit": unit,
                "line_count": len(
                    lines
                ),
                "block_count": len(
                    blocks
                ),
            },
            blocks=blocks,
        )

    # ------------------------------------------------------------------
    # OCR
    # ------------------------------------------------------------------

    async def recognize(
        self,
        request: OCRRequest,
    ) -> OCRResult:
        """
        Run Azure Document Intelligence OCR.
        """

        request.validate()

        client = self._ensure_client()

        source_path = (
            self._get_source_path(
                request
            )
        )

        content = (
            self._get_content(
                request
            )
        )

        if not source_path and content is None:
            raise ValueError(
                "Azure OCR requires either a source path "
                "or document bytes."
            )

        filename = (
            self._get_filename(
                request
            )
        )

        try:
            if content is not None:
                poller = (
                    client.begin_analyze_document(
                        self.model,
                        body=content,
                    )
                )

            else:
                with open(
                    source_path,
                    "rb",
                ) as document_file:
                    document_bytes = (
                        document_file.read()
                    )

                poller = (
                    client.begin_analyze_document(
                        self.model,
                        body=document_bytes,
                    )
                )

            analysis = poller.result()

        except FileNotFoundError:
            raise

        except Exception as exc:
            logger.exception(
                "Azure OCR request failed."
            )

            raise ProviderUnavailableError(
                f"Azure OCR request failed: {exc}"
            ) from exc

        pages: list[OCRPage] = []

        azure_pages = (
            self._get_attr(
                analysis,
                "pages",
                [],
            )
            or []
        )

        for index, azure_page in enumerate(
            azure_pages
        ):
            pages.append(
                self._extract_page(
                    azure_page,
                    index + 1,
                )
            )

        full_text = self._get_attr(
            analysis,
            "content",
            "",
        )

        full_text = str(
            full_text or ""
        ).strip()

        if not full_text and pages:
            full_text = "\n\n".join(
                page.text
                for page in pages
                if page.text
            ).strip()

        metadata: dict[str, Any] = {
            "model": self.model,
            "provider": self.name,
            "filename": filename,
            "page_count": len(pages),
        }

        language = self._get_attr(
            analysis,
            "locale",
        )

        if language:
            metadata[
                "language"
            ] = str(
                language
            )

        return OCRResult(
            document_id=getattr(
                request,
                "document_id",
                None,
            ),
            text=full_text,
            pages=pages,
            provider=self.name,
            model=self.model,
            metadata=metadata,
            warnings=[],
        )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def startup(self) -> None:
        """
        Validate non-secret configuration.

        We intentionally do not initialize the Azure client here unless
        explicitly requested.

        Set:

            preload_client=True

        to initialize the client during application startup.
        """

        self.validate_config()

        preload = bool(
            self.get_config(
                "preload_client",
                False,
            )
        )

        if preload:
            self._ensure_client()

    async def shutdown(self) -> None:
        """
        Release the Azure client reference.
        """

        client = self._client

        self._client = None

        if client is not None:
            close_method = getattr(
                client,
                "close",
                None,
            )

            if close_method is not None:
                try:
                    result = close_method()

                    # Azure client close is normally synchronous, but
                    # tolerate async implementations as well.
                    if hasattr(
                        result,
                        "__await__",
                    ):
                        await result

                except Exception:
                    logger.debug(
                        "Failed to close Azure OCR client.",
                        exc_info=True,
                    )

