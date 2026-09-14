
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ProcessingStage
from app.processing.pipeline.context import ProcessingContext
from app.processing.pipeline.pipeline import DocumentProcessingStage


class LayoutAnalysisStage(DocumentProcessingStage):
    """
    Analyze basic document layout.

    Produces layout blocks and stores them in stage_results.

    The stage accepts the shared pipeline contract:
        process(context, session)

    The database session is currently not required by this stage, but it is
    accepted so that all processing stages can be invoked consistently by
    the pipeline.
    """

    @property
    def name(self) -> str:
        return ProcessingStage.LAYOUT_ANALYSIS.value

    async def process(
        self,
        context: ProcessingContext,
        session: AsyncSession | None = None,
    ) -> ProcessingContext:
        """
        Analyze the extracted document text and identify basic layout blocks.

        Parameters
        ----------
        context:
            Current document processing context.

        session:
            Optional database session supplied by the processing pipeline.
            Layout analysis does not currently require database access.
        """
        text = context.raw_text or ""

        blocks: list[dict[str, object]] = []

        for index, line in enumerate(text.splitlines()):
            stripped = line.strip()

            if not stripped:
                continue

            blocks.append(
                {
                    "index": index,
                    "type": self._detect_block_type(stripped),
                    "text": stripped,
                }
            )

        context.stage_results[self.name] = {
            "block_count": len(blocks),
            "blocks": blocks,
        }

        context.set_metadata(
            "layout_block_count",
            len(blocks),
        )

        return context

    @staticmethod
    def _detect_block_type(line: str) -> str:
        if line.startswith(
            ("# ", "## ", "### "),
        ):
            return "heading"

        if line.startswith(
            ("-", "*", "•"),
        ):
            return "list_item"

        if (
            len(line) < 120
            and line.isupper()
        ):
            return "heading"

        return "paragraph"


__all__ = [
    "LayoutAnalysisStage",
]

