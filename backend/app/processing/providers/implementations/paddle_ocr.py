
"""
app.processing.providers.implementations.paddle_ocr

PaddleOCR implementation of the canonical OCR provider.

PaddleOCR is imported lazily so the provider module itself remains
importable when PaddleOCR is not installed.
"""

from __future__ import annotations

import logging
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


class PaddleOCRProvider(BaseOCRProvider):
    """
    OCR provider backed by PaddleOCR.

    Configuration example:

        {
            "lang": "en",
            "use_doc_orientation_classify": False,
            "use_doc_unwarping": False,
            "use_textline_orientation": False
        }

    The implementation intentionally keeps PaddleOCR-specific objects
    out of the canonical provider contract.
    """

    PROVIDER_NAME = "paddle_ocr"
    PROVIDER_TYPE = "ocr"
    VERSION = "1.0"

    def __init__(
        self,
        *,
        config: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(config=config)

        self._engine: Any = None

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    @property
    def language(self) -> str:
        value = self.get_config(
            "lang",
            "en",
        )

        return str(value or "en").strip()

    def validate_config(self) -> None:
        if not self.language:
            raise ProviderConfigurationError(
                "PaddleOCR language cannot be empty."
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
    # Lazy dependency loading
    # ------------------------------------------------------------------

    def _load_paddleocr(self):
        try:
            from paddleocr import PaddleOCR
        except ImportError as exc:
            raise ProviderUnavailableError(
                "PaddleOCR is not installed. "
                "Install PaddleOCR and its required PaddlePaddle "
                "runtime before using this provider."
            ) from exc

        return PaddleOCR

    def _ensure_engine(self) -> Any:
        if self._engine is not None:
            return self._engine

        self.validate_config()

        PaddleOCR = self._load_paddleocr()

        kwargs: dict[str, Any] = {
            "lang": self.language,
        }

        optional_keys = (
            "use_doc_orientation_classify",
            "use_doc_unwarping",
            "use_textline_orientation",
            "use_angle_cls",
            "det_model_dir",
            "rec_model_dir",
            "cls_model_dir",
            "device",
        )

        for key in optional_keys:
            value = self.get_config(key)

            if value is not None:
                kwargs[key] = value

        try:
            self._engine = PaddleOCR(
                **kwargs
            )

        except TypeError:
            # Older PaddleOCR versions may not support newer options.
            # Retry with the universally useful language option.
            logger.warning(
                "PaddleOCR rejected extended configuration; "
                "retrying with basic configuration.",
                exc_info=True,
            )

            try:
                self._engine = PaddleOCR(
                    lang=self.language
                )
            except Exception as exc:
                raise ProviderUnavailableError(
                    f"Failed to initialize PaddleOCR: {exc}"
                ) from exc

        except Exception as exc:
            raise ProviderUnavailableError(
                f"Failed to initialize PaddleOCR: {exc}"
            ) from exc

        return self._engine

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    async def health_check(self) -> bool:
        try:
            self.validate_config()
            self._load_paddleocr()
            return True

        except (
            ProviderConfigurationError,
            ProviderUnavailableError,
        ):
            return False

    # ------------------------------------------------------------------
    # Request helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get(
        obj: Any,
        name: str,
        default: Any = None,
    ) -> Any:
        if obj is None:
            return default

        if isinstance(obj, Mapping):
            return obj.get(
                name,
                default,
            )

        return getattr(
            obj,
            name,
            default,
        )

    def _source(
        self,
        request: OCRRequest,
    ) -> str | bytes | None:
        source_path = getattr(
            request,
            "source_path",
            None,
        )

        if source_path:
            return str(source_path)

        content = getattr(
            request,
            "content",
            None,
        )

        if content is not None:
            return content

        file_path = getattr(
            request,
            "file_path",
            None,
        )

        if file_path:
            return str(file_path)

        return None

    # ------------------------------------------------------------------
    # Result normalization
    # ------------------------------------------------------------------

    def _normalize_result(
        self,
        raw: Any,
        request: OCRRequest,
    ) -> OCRResult:
        """
        Normalize PaddleOCR output into the project's OCRResult.

        This method intentionally uses the existing OCRResult constructor
        dynamically because PaddleOCR output differs between versions.
        """

        text_parts: list[str] = []

        def collect(
            value: Any,
        ) -> None:
            if value is None:
                return

            if isinstance(
                value,
                str,
            ):
                value = value.strip()

                if value:
                    text_parts.append(value)

                return

            if isinstance(
                value,
                Mapping,
            ):
                for key in (
                    "text",
                    "rec_text",
                    "content",
                ):
                    if key in value:
                        collect(
                            value[key]
                        )

                return

            if isinstance(
                value,
                (list, tuple),
            ):
                for item in value:
                    collect(item)

                return

            # PaddleOCR objects may expose text through attributes.
            for key in (
                "text",
                "rec_text",
                "content",
            ):
                attr = getattr(
                    value,
                    key,
                    None,
                )

                if attr:
                    collect(attr)

        collect(raw)

        # Deduplicate consecutive duplicate text while preserving order.
        normalized: list[str] = []

        for item in text_parts:
            if not normalized or normalized[-1] != item:
                normalized.append(item)

        text = "\n".join(
            normalized
        ).strip()

        document_id = getattr(
            request,
            "document_id",
            None,
        )

        return OCRResult(
            document_id=document_id,
            text=text,
            provider=self.name,
            model="paddleocr",
            metadata={
                "language": self.language,
                "raw_result_type": type(raw).__name__,
            },
            warnings=[],
        )

    # ------------------------------------------------------------------
    # OCR
    # ------------------------------------------------------------------

    async def recognize(
        self,
        request: OCRRequest,
    ) -> OCRResult:
        request.validate()

        engine = self._ensure_engine()

        source = self._source(
            request
        )

        if source is None:
            raise ValueError(
                "PaddleOCR requires a source_path, file_path, "
                "or document content."
            )

        try:
            # PaddleOCR has had several API generations.
            if hasattr(
                engine,
                "predict",
            ):
                raw = engine.predict(
                    source
                )

            elif hasattr(
                engine,
                "ocr",
            ):
                raw = engine.ocr(
                    source,
                    cls=True,
                )

            else:
                raise ProviderUnavailableError(
                    "Installed PaddleOCR object does not expose "
                    "a supported OCR method."
                )

        except ProviderUnavailableError:
            raise

        except Exception as exc:
            logger.exception(
                "PaddleOCR execution failed."
            )

            raise ProviderUnavailableError(
                f"PaddleOCR execution failed: {exc}"
            ) from exc

        return self._normalize_result(
            raw,
            request,
        )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def startup(self) -> None:
        self.validate_config()

        if self.get_config(
            "preload",
            False,
        ):
            self._ensure_engine()

    async def shutdown(self) -> None:
        self._engine = None

