
"""
app.processing.providers.implementations.basic_layout

Lightweight deterministic layout provider.

The provider converts page/block information produced by extraction
into the canonical layout representation.

It does not require a machine-learning model.

This makes it useful as the default local layout implementation while
leaving the architecture open for more advanced layout models later.
"""

from __future__ import annotations

import logging
from typing import Any, Mapping

from ..base import (
    ProviderConfigurationError,
)
from ..layout import (
    BaseLayoutProvider,
    BoundingBox,
    LayoutAnalysisRequest,
    LayoutAnalysisResult,
    LayoutBlock,
    LayoutPage,
)


logger = logging.getLogger(__name__)


class BasicLayoutProvider(
    BaseLayoutProvider
):
    """
    Deterministic layout provider based on extracted page/block data.

    Supported block types include:

        text
        paragraph
        heading
        table
        image
        list
        header
        footer
        signature
        unknown
    """

    PROVIDER_NAME = "basic_layout"

    PROVIDER_TYPE = "layout"

    VERSION = "1.0"

    BLOCK_TYPES = (
        "text",
        "paragraph",
        "heading",
        "table",
        "image",
        "list",
        "header",
        "footer",
        "signature",
        "unknown",
    )

    def __init__(
        self,
        *,
        config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            config=config
        )

    async def health_check(self) -> bool:
        """
        Basic layout analysis has no external runtime dependency.
        """

        return True

    def validate_config(self) -> None:
        confidence_threshold = self.get_config(
            "confidence_threshold"
        )

        if confidence_threshold is not None:
            try:
                value = float(
                    confidence_threshold
                )
            except (
                TypeError,
                ValueError,
            ) as exc:
                raise ProviderConfigurationError(
                    "confidence_threshold must be numeric."
                ) from exc

            if not 0.0 <= value <= 1.0:
                raise ProviderConfigurationError(
                    "confidence_threshold must be between 0 and 1."
                )

    def supported_block_types(
        self,
    ) -> tuple[str, ...]:
        return self.BLOCK_TYPES

    @staticmethod
    def _safe_text(
        value: Any,
    ) -> str:
        if value is None:
            return ""

        return str(
            value
        ).strip()

    @staticmethod
    def _bbox_from_mapping(
        value: Any,
    ) -> BoundingBox | None:
        if value is None:
            return None

        if isinstance(
            value,
            BoundingBox,
        ):
            return value

        if isinstance(
            value,
            Mapping,
        ):
            try:
                return BoundingBox(
                    x1=float(
                        value.get(
                            "x1",
                            value.get(
                                "left",
                                0,
                            ),
                        )
                    ),
                    y1=float(
                        value.get(
                            "y1",
                            value.get(
                                "top",
                                0,
                            ),
                        )
                    ),
                    x2=float(
                        value.get(
                            "x2",
                            value.get(
                                "right",
                                0,
                            ),
                        )
                    ),
                    y2=float(
                        value.get(
                            "y2",
                            value.get(
                                "bottom",
                                0,
                            ),
                        )
                    ),
                )
            except (
                TypeError,
                ValueError,
            ):
                return None

        if isinstance(
            value,
            (list, tuple),
        ) and len(value) >= 4:
            try:
                return BoundingBox(
                    x1=float(value[0]),
                    y1=float(value[1]),
                    x2=float(value[2]),
                    y2=float(value[3]),
                )
            except (
                TypeError,
                ValueError,
            ):
                return None

        return None

    def _detect_block_type(
        self,
        block: Mapping[str, Any],
    ) -> str:
        explicit_type = block.get(
            "block_type",
            block.get(
                "type"
            ),
        )

        if explicit_type:
            normalized = str(
                explicit_type
            ).strip().lower()

            if normalized in self.BLOCK_TYPES:
                return normalized

        text = self._safe_text(
            block.get("text")
        )

        metadata = block.get(
            "metadata"
        )

        if isinstance(
            metadata,
            Mapping,
        ):
            metadata_type = metadata.get(
                "type"
            )

            if metadata_type:
                normalized = str(
                    metadata_type
                ).strip().lower()

                if normalized in self.BLOCK_TYPES:
                    return normalized

        if not text:
            if block.get(
                "image"
            ) or block.get(
                "image_index"
            ):
                return "image"

            return "unknown"

        return "text"

    def _convert_block(
        self,
        block: Mapping[str, Any],
        *,
        page_number: int,
        reading_order: int,
    ) -> LayoutBlock:
        block_id = str(
            block.get(
                "block_id",
                f"page-{page_number}-block-{reading_order}",
            )
        )

        block_type = self._detect_block_type(
            block
        )

        text = self._safe_text(
            block.get(
                "text"
            )
        )

        bbox = self._bbox_from_mapping(
            block.get(
                "bbox",
                block.get(
                    "bounding_box"
                ),
            )
        )

        confidence = block.get(
            "confidence"
        )

        if confidence is not None:
            try:
                confidence = float(
                    confidence
                )
            except (
                TypeError,
                ValueError,
            ):
                confidence = None

        metadata = block.get(
            "metadata"
        )

        if not isinstance(
            metadata,
            Mapping,
        ):
            metadata = {}

        return LayoutBlock(
            block_id=block_id,
            block_type=block_type,
            page_number=page_number,
            bounding_box=bbox,
            text=text,
            confidence=confidence,
            reading_order=reading_order,
            metadata=dict(
                metadata
            ),
        )

    def _page_blocks(
        self,
        page: Mapping[str, Any],
    ) -> list[Mapping[str, Any]]:
        raw_blocks = page.get(
            "blocks",
            []
        )

        if not isinstance(
            raw_blocks,
            (list, tuple),
        ):
            return []

        result: list[Mapping[str, Any]] = []

        for block in raw_blocks:
            if isinstance(
                block,
                Mapping,
            ):
                result.append(
                    block
                )

        return result

    async def analyze(
        self,
        request: LayoutAnalysisRequest,
    ) -> LayoutAnalysisResult:
        """
        Analyze layout using existing extraction geometry.
        """

        request.validate()

        result = LayoutAnalysisResult(
            document_id=request.document_id,
            model="basic-layout",
        )

        pages = list(
            request.pages
        )

        # If page information is unavailable, create a single
        # logical page from the supplied text.
        if not pages and request.text.strip():
            pages = [
                {
                    "page_number": 1,
                    "text": request.text,
                    "blocks": [],
                }
            ]

        for page_index, raw_page in enumerate(
            pages
        ):
            if not isinstance(
                raw_page,
                Mapping,
            ):
                result.warnings.append(
                    f"Page {page_index + 1} "
                    "was not a mapping and was skipped."
                )
                continue

            page_number_value = raw_page.get(
                "page_number",
                page_index + 1,
            )

            try:
                page_number = int(
                    page_number_value
                )
            except (
                TypeError,
                ValueError,
            ):
                page_number = (
                    page_index + 1
                )

            width = raw_page.get(
                "width"
            )

            height = raw_page.get(
                "height"
            )

            try:
                width = (
                    float(width)
                    if width is not None
                    else None
                )
            except (
                TypeError,
                ValueError,
            ):
                width = None

            try:
                height = (
                    float(height)
                    if height is not None
                    else None
                )
            except (
                TypeError,
                ValueError,
            ):
                height = None

            layout_page = LayoutPage(
                page_number=page_number,
                width=width,
                height=height,
            )

            raw_blocks = self._page_blocks(
                raw_page
            )

            # If extraction didn't provide blocks, create one logical
            # text block for the page.
            if not raw_blocks:
                page_text = self._safe_text(
                    raw_page.get(
                        "text"
                    )
                )

                if page_text:
                    raw_blocks = [
                        {
                            "block_id": (
                                f"page-{page_number}-text"
                            ),
                            "block_type": "text",
                            "text": page_text,
                        }
                    ]

            for reading_order, raw_block in enumerate(
                raw_blocks
            ):
                block = self._convert_block(
                    raw_block,
                    page_number=page_number,
                    reading_order=reading_order,
                )

                layout_page.blocks.append(
                    block
                )

                result.blocks.append(
                    block
                )

            result.pages.append(
                layout_page
            )

        result.metadata.update(
            {
                "provider": self.name,
                "page_count": result.page_count,
                "block_count": result.block_count,
            }
        )

        return result

