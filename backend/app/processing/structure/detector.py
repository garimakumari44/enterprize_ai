
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ProcessingStage
from app.processing.pipeline.context import ProcessingContext
from app.processing.pipeline.pipeline import DocumentProcessingStage


class StructureDetectionStage(DocumentProcessingStage):
    """
    Detect the logical section structure of a document.

    The processing pipeline may provide a database session to every stage.
    This stage does not currently require database access, but accepts the
    session to remain compatible with the shared stage contract.
    """

    @property
    def name(self) -> str:
        return ProcessingStage.STRUCTURE_DETECTION.value

    async def process(
        self,
        data: ProcessingContext,
        session: AsyncSession | None = None,
    ) -> ProcessingContext:
        layout = data.stage_results.get(
            ProcessingStage.LAYOUT_ANALYSIS.value,
            {},
        )

        blocks = layout.get(
            "blocks",
            [],
        )

        sections: list[dict] = []

        current_section: dict | None = None

        for block in blocks:
            if block.get("type") == "heading":
                current_section = {
                    "title": block.get("text"),
                    "level": self._heading_level(
                        block.get("text", "")
                    ),
                    "content": [],
                }

                sections.append(current_section)

                continue

            if current_section is None:
                current_section = {
                    "title": None,
                    "level": 0,
                    "content": [],
                }

                sections.append(current_section)

            current_section["content"].append(
                block.get("text", "")
            )

        data.stage_results[self.name] = {
            "sections": sections,
            "section_count": len(sections),
        }

        data.set_metadata(
            "section_count",
            len(sections),
        )

        return data

    @staticmethod
    def _heading_level(text: str) -> int:
        if text.startswith("###"):
            return 3

        if text.startswith("##"):
            return 2

        return 1


__all__ = [
    "StructureDetectionStage",
]

