
"""
app.processing.providers.implementations.tesseract_ocr

Tesseract OCR implementation.

The Python pytesseract package and the Tesseract executable are both
optional dependencies. They are loaded/checked only when this provider
is actually used.
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
)

logger = logging.getLogger(__name__)


class TesseractOCRProvider(BaseOCRProvider):
    """
    OCR provider backed by Tesseract.

    Configuration example:

        {
            "language": "eng",
            "tesseract_cmd": "C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
            "config": "--psm 3"
        }
    """

    PROVIDER_NAME = "tesseract_ocr"
    PROVIDER_TYPE = "ocr"
    VERSION = "1.0"

    def __init__(
        self,
        *,
        config: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(config=config)

        self._pytesseract: Any = None

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    @property
    def language(self) -> str:
        value = self.get_config(
            "language",
            self.get_config(
                "lang",
                "eng",
            ),
        )

        return str(
            value or "eng"
        ).strip()

    @property
    def tesseract_cmd(self) -> str | None:
        value = self.get_config(
            "tesseract_cmd"
        )

        if value is None:
            value = os.getenv(
                "TESSERACT_CMD"
            )

        if value is None:
            return None

        value = str(
            value
        ).strip()

        return value or None

    @property
    def tesseract_config(self) -> str:
        value = self.get_config(
            "config",
            "",
        )

        return str(
            value or ""
        )

    def validate_config(self) -> None:
        if not self.language:
            raise ProviderConfigurationError(
                "Tesseract language cannot be empty."
            )

    # ------------------------------------------------------------------
    # Capabilities
    # ------------------------------------------------------------------

    def supported_mime_types(
        self,
    ) -> tuple[str, ...]:
        return (
            "image/png",
            "image/jpeg",
            "image/jpg",
            "image/tiff",
            "image/bmp",
            "image/webp",
        )

    # ------------------------------------------------------------------
    # Dependency
    # ------------------------------------------------------------------

    def _load_pytesseract(self):
        try:
            import pytesseract
        except ImportError as exc:
            raise ProviderUnavailableError(
                "pytesseract is not installed. "
                "Install it with: pip install pytesseract"
            ) from exc

        return pytesseract

    def _configure_pytesseract(self) -> Any:
        pytesseract = self._load_pytesseract()

        command = self.tesseract_cmd

        if command:
            pytesseract.pytesseract.tesseract_cmd = (
                command
            )

        self._pytesseract = pytesseract

        return pytesseract

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    async def health_check(self) -> bool:
        try:
            self.validate_config()

            pytesseract = (
                self._configure_pytesseract()
            )

            # get_tesseract_version() verifies that the executable
            # can actually be launched.
            pytesseract.get_tesseract_version()

            return True

        except (
            ProviderConfigurationError,
            ProviderUnavailableError,
        ):
            return False

        except Exception:
            logger.debug(
                "Tesseract health check failed.",
                exc_info=True,
            )

            return False

    # ------------------------------------------------------------------
    # Request helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _source_path(
        request: OCRRequest,
    ) -> str | None:
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

    @staticmethod
    def _content(
        request: OCRRequest,
    ) -> bytes | None:
        for attribute in (
            "content",
            "file_bytes",
            "data",
        ):
            value = getattr(
                request,
                attribute,
                None,
            )

            if isinstance(
                value,
                bytes,
            ):
                return value

        return None

    # ------------------------------------------------------------------
    # OCR
    # ------------------------------------------------------------------

    async def recognize(
        self,
        request: OCRRequest,
    ) -> OCRResult:
        request.validate()

        pytesseract = (
            self._configure_pytesseract()
        )

        source_path = (
            self._source_path(
                request
            )
        )

        content = (
            self._content(
                request
            )
        )

        if not source_path and content is None:
            raise ValueError(
                "Tesseract OCR requires a source_path/file_path "
                "or document content."
            )

        try:
            if content is not None:
                from PIL import Image
                from io import BytesIO

                image = Image.open(
                    BytesIO(content)
                )

                text = pytesseract.image_to_string(
                    image,
                    lang=self.language,
                    config=self.tesseract_config,
                )

            else:
                path = Path(
                    source_path
                )

                if not path.exists():
                    raise FileNotFoundError(
                        f"OCR source file does not exist: {path}"
                    )

                text = pytesseract.image_to_string(
                    str(path),
                    lang=self.language,
                    config=self.tesseract_config,
                )

        except FileNotFoundError:
            raise

        except ImportError as exc:
            raise ProviderUnavailableError(
                "Pillow is required when Tesseract OCR "
                "processes in-memory image bytes. "
                "Install it with: pip install Pillow"
            ) from exc

        except Exception as exc:
            logger.exception(
                "Tesseract OCR execution failed."
            )

            raise ProviderUnavailableError(
                f"Tesseract OCR execution failed: {exc}"
            ) from exc

        text = str(
            text or ""
        ).strip()

        return OCRResult(
            document_id=getattr(
                request,
                "document_id",
                None,
            ),
            text=text,
            provider=self.name,
            model="tesseract",
            metadata={
                "language": self.language,
                "tesseract_config": (
                    self.tesseract_config
                ),
            },
            warnings=[],
        )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def startup(self) -> None:
        self.validate_config()

        if self.get_config(
            "verify_on_startup",
            False,
        ):
            healthy = await self.health_check()

            if not healthy:
                raise ProviderUnavailableError(
                    "Tesseract is not available."
                )

    async def shutdown(self) -> None:
        self._pytesseract = None

