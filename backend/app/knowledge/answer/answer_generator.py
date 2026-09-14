from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence

from app.knowledge.answer.citation_builder import Citation
from app.knowledge.answer.context_builder import ContextItem


class LLMClient(Protocol):
    """
    Provider-independent interface for an LLM.
    """

    def generate(
        self,
        prompt: str,
    ) -> str:
        ...


@dataclass
class GeneratedAnswer:
    """
    Final answer produced by the answer-generation layer.
    """

    answer: str
    citations: list[Citation]


class AnswerGenerator:
    """
    Generate grounded answers from retrieved knowledge.

    The generator itself does not perform retrieval.
    """

    SYSTEM_INSTRUCTION = """
You are an enterprise knowledge assistant.

Answer the user's question using only the supplied context.

Rules:
1. Do not invent facts.
2. If the context does not contain enough information, say so.
3. Keep the answer concise and useful.
4. Cite relevant sources using their source identifiers.
5. Never expose internal implementation details unless asked.
""".strip()

    def __init__(self, llm_client: LLMClient) -> None:
        self.llm_client = llm_client

    def generate(
        self,
        query: str,
        context: Sequence[ContextItem],
        citations: list[Citation],
    ) -> GeneratedAnswer:

        context_text = self._build_context(context)

        prompt = (
            f"{self.SYSTEM_INSTRUCTION}\n\n"
            f"USER QUESTION:\n"
            f"{query}\n\n"
            f"CONTEXT:\n"
            f"{context_text}\n\n"
            f"Provide a grounded answer."
        )

        answer = self.llm_client.generate(prompt)

        return GeneratedAnswer(
            answer=answer.strip(),
            citations=citations,
        )

    @staticmethod
    def _build_context(
        context: Sequence[ContextItem],
    ) -> str:
        if not context:
            return "No relevant context was retrieved."

        sections = []

        for index, item in enumerate(context, start=1):
            sections.append(
                f"[Source {index}]\n"
                f"{item.content.strip()}"
            )

        return "\n\n".join(sections)