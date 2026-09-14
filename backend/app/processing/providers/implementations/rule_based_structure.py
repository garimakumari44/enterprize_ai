
"""
app.processing.providers.implementations.rule_based_structure

Deterministic document structure detector.

Detects:
    - headings
    - sections
    - paragraphs
    - lists
    - tables
    - document root

No external dependencies are required.
"""

from __future__ import annotations

import re
from typing import Any, Mapping

from ..base import ProviderConfigurationError
from ..structure import (
    BaseStructureProvider,
    DocumentStructure,
    StructureDetectionRequest,
    StructureNode,
)


class RuleBasedStructureProvider(
    BaseStructureProvider
):
    """
    Rule-based semantic structure detector.
    """

    PROVIDER_NAME = (
        "rule_based_structure"
    )

    PROVIDER_TYPE = "structure"

    VERSION = "1.0"

    NODE_TYPES = (
        "document",
        "section",
        "heading",
        "paragraph",
        "list",
        "table",
        "unknown",
    )

    HEADING_PATTERNS = (
        re.compile(
            r"^\s*(?:\d+(?:\.\d+)*|[IVXLC]+)[\.)]?\s+\S+",
            re.IGNORECASE,
        ),
        re.compile(
            r"^\s*(?:chapter|section|appendix)"
            r"\s+\S+",
            re.IGNORECASE,
        ),
    )

    LIST_PATTERN = re.compile(
        r"^\s*(?:[-*•]|\d+[\.)]|[a-zA-Z][\.)])\s+"
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
        return True

    def supported_node_types(
        self,
    ) -> tuple[str, ...]:
        return self.NODE_TYPES

    def validate_config(self) -> None:
        max_heading_length = self.get_config(
            "max_heading_length",
            200,
        )

        try:
            value = int(
                max_heading_length
            )
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ProviderConfigurationError(
                "max_heading_length must be an integer."
            ) from exc

        if value < 1:
            raise ProviderConfigurationError(
                "max_heading_length must be >= 1."
            )

    @staticmethod
    def _clean(
        text: str,
    ) -> str:
        return re.sub(
            r"\s+",
            " ",
            text.strip(),
        )

    def _looks_like_heading(
        self,
        text: str,
    ) -> bool:
        if not text:
            return False

        max_length = int(
            self.get_config(
                "max_heading_length",
                200,
            )
        )

        if len(text) > max_length:
            return False

        for pattern in self.HEADING_PATTERNS:
            if pattern.match(text):
                return True

        # Short title-like lines.
        words = text.split()

        if 1 <= len(words) <= 10:
            if text.endswith(
                (
                    ".",
                    ",",
                    ";",
                    ":",
                    "?",
                    "!",
                )
            ):
                return False

            uppercase_words = sum(
                1
                for word in words
                if word[:1].isupper()
            )

            if uppercase_words >= max(
                1,
                len(words) // 2,
            ):
                return True

        return False

    def _looks_like_list(
        self,
        text: str,
    ) -> bool:
        return bool(
            self.LIST_PATTERN.match(
                text
            )
        )

    def _block_type(
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

            if normalized in {
                "table",
                "list",
                "heading",
                "paragraph",
                "section",
            }:
                return normalized

        text = self._clean(
            str(
                block.get(
                    "text",
                    "",
                )
                or ""
            )
        )

        if not text:
            return "unknown"

        if self._looks_like_list(
            text
        ):
            return "list"

        if self._looks_like_heading(
            text
        ):
            return "heading"

        return "paragraph"

    def _page_number(
        self,
        block: Mapping[str, Any],
    ) -> int | None:
        value = block.get(
            "page_number"
        )

        if value is None:
            return None

        try:
            value = int(
                value
            )
        except (
            TypeError,
            ValueError,
        ):
            return None

        return (
            value
            if value >= 1
            else None
        )

    async def detect_structure(
        self,
        request: StructureDetectionRequest,
    ) -> DocumentStructure:
        request.validate()

        structure = DocumentStructure(
            document_id=request.document_id
        )

        root = StructureNode(
            node_id="document-root",
            node_type="document",
            title=None,
            text="",
            level=0,
            order=0,
            metadata={
                "provider": self.name,
            },
            confidence=1.0,
        )

        structure.nodes.append(
            root
        )

        structure.root_id = (
            root.node_id
        )

        order = 1

        current_section_id: str | None = (
            None
        )

        # Prefer explicit blocks when supplied.
        blocks = list(
            request.blocks
        )

        if not blocks and request.text:
            blocks = [
                {
                    "text": line,
                    "page_number": None,
                }
                for line in request.text.splitlines()
                if line.strip()
            ]

        for raw_block in blocks:
            if not isinstance(
                raw_block,
                Mapping,
            ):
                continue

            text = self._clean(
                str(
                    raw_block.get(
                        "text",
                        "",
                    )
                    or ""
                )
            )

            if not text:
                continue

            node_type = self._block_type(
                raw_block
            )

            page_number = (
                self._page_number(
                    raw_block
                )
            )

            if node_type in {
                "heading",
                "section",
            }:
                node_id = (
                    f"section-{order}"
                )

                node = StructureNode(
                    node_id=node_id,
                    node_type="section",
                    title=text,
                    text="",
                    page_number=page_number,
                    parent_id=structure.root_id,
                    level=1,
                    order=order,
                    metadata={
                        "source_type": node_type,
                    },
                    confidence=0.90,
                )

                structure.nodes.append(
                    node
                )

                root.children.append(
                    node_id
                )

                current_section_id = (
                    node_id
                )

                order += 1

                continue

            parent_id = (
                current_section_id
                or structure.root_id
            )

            node_id = (
                f"node-{order}"
            )

            node = StructureNode(
                node_id=node_id,
                node_type=node_type,
                title=None,
                text=text,
                page_number=page_number,
                parent_id=parent_id,
                level=(
                    2
                    if current_section_id
                    else 1
                ),
                order=order,
                metadata={
                    "source_type": node_type,
                },
                confidence=0.85,
            )

            structure.nodes.append(
                node
            )

            parent = structure.get_node(
                parent_id
            )

            if parent is not None:
                parent.children.append(
                    node_id
                )

            order += 1

        if structure.node_count == 1:
            structure.warnings.append(
                "No semantic structure could be detected."
            )

        structure.metadata.update(
            {
                "provider": self.name,
                "node_count": structure.node_count,
                "section_count": structure.section_count,
            }
        )

        return structure

