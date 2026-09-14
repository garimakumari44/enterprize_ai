"""
app/assistant/prompt_builder.py

Prompt construction layer for the conversational assistant.

Responsibilities
----------------
- Build system instructions.
- Normalize conversation history.
- Incorporate application context.
- Produce a clean message structure for LLMManager.
- Provide explicit grounding rules for operational application data.
- Keep prompt policy separate from orchestration and provider logic.

The PromptBuilder must NOT:
- call an LLM
- access the database
- access FastAPI request objects
- know about OpenRouter
- select a provider
- contain repository/business logic
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional


# ============================================================================
# PROMPT MESSAGE
# ============================================================================


@dataclass
class PromptMessage:
    """
    A normalized message passed to the LLM layer.
    """

    role: str
    content: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "role": self.role,
            "content": self.content,
        }


# ============================================================================
# ASSISTANT PROMPT
# ============================================================================


@dataclass
class AssistantPrompt:
    """
    Complete prompt representation.

    `messages` follows the standard chat-completion structure.
    """

    messages: List[PromptMessage]

    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "messages": [
                message.to_dict()
                for message in self.messages
            ],
            "metadata": self.metadata,
        }

    def as_messages(self) -> List[Dict[str, str]]:
        """
        Return the prompt in the format expected by LLMManager/provider.
        """

        return [
            message.to_dict()
            for message in self.messages
        ]


# ============================================================================
# PROMPT BUILDER
# ============================================================================


class PromptBuilder:
    """
    Builds prompts for the enterprise assistant.

    The builder is deliberately independent from:
    - databases
    - repositories
    - LLM providers
    - FastAPI
    - OpenRouter
    """

    DEFAULT_SYSTEM_PROMPT = """
You are the AI assistant for an intelligent enterprise AI platform.

You operate as a grounded enterprise application assistant.

GENERAL RULES
-------------
1. Understand the user's request accurately.
2. Give direct, useful, and concise answers.
3. Use application-provided context whenever it is relevant.
4. Never invent facts, records, documents, jobs, dates, statuses, or results.
5. Distinguish application data from general knowledge.
6. Ask for clarification only when genuinely necessary.
7. Maintain continuity with the conversation.
8. If required information is not present in the supplied application context,
   clearly state that the information is unavailable.
9. Do not pretend that you performed an action that you did not perform.
10. Do not claim that a database, application, or system is inaccessible when
    the required data has been supplied in application context.

OPERATIONAL DATA RULES
----------------------
The application may provide authoritative operational data from its database.

Operational data includes information such as:
- documents
- document versions
- processing jobs
- processing status
- processing progress
- processing completion times
- pipeline execution
- workflow execution
- review records
- application metadata

When answering an operational question:

1. Treat the supplied operational application context as the authoritative
   source for the answer.
2. Answer directly from the records supplied in that context.
3. Do not substitute general knowledge for supplied application data.
4. Do not say that you "need database access" if database-derived records
   are already present in the application context.
5. Do not invent additional records simply because the user requested more
   records than are available.
6. If fewer records are available than requested, report the records that
   were found and clearly state that fewer matching records were available.
7. Preserve the ordering supplied by the application.
8. When a timestamp is supplied, use it rather than inventing a date/time.
9. When a status is supplied, use that status exactly unless explaining it.
10. If no matching records are supplied, say that no matching records were
    found.

RECENCY QUESTIONS
-----------------
For questions such as:
- "most recently processed documents"
- "latest processed documents"
- "recent processing jobs"
- "last completed jobs"

use the application's supplied processing completion ordering.

Do NOT infer recency from your own knowledge.

IMPORTANT
---------
The absence of a record is meaningful.

If the application provides one matching record for a request for five
records, answer using that one record. Do not fabricate four additional
records.

Your job is to interpret and explain the supplied application data, not to
pretend that the data does not exist.
""".strip()

    # ========================================================================
    # INITIALIZATION
    # ========================================================================

    def __init__(
        self,
        *,
        system_prompt: Optional[str] = None,
        max_history_messages: int = 30,
        include_context: bool = True,
    ) -> None:

        if max_history_messages <= 0:
            raise ValueError(
                "max_history_messages must be greater than zero."
            )

        self.system_prompt = (
            system_prompt.strip()
            if system_prompt
            else self.DEFAULT_SYSTEM_PROMPT
        )

        self.max_history_messages = max_history_messages
        self.include_context = include_context

    # ========================================================================
    # PUBLIC API
    # ========================================================================

    def build(
        self,
        *,
        history: Optional[List[Dict[str, Any]]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> AssistantPrompt:
        """
        Build a complete assistant prompt.
        """

        normalized_history = self._normalize_history(
            history or []
        )

        normalized_context = self._normalize_context(
            context or {}
        )

        messages: List[PromptMessage] = []

        # --------------------------------------------------------------------
        # 1. SYSTEM INSTRUCTIONS
        # --------------------------------------------------------------------

        messages.append(
            PromptMessage(
                role="system",
                content=self.system_prompt,
            )
        )

        # --------------------------------------------------------------------
        # 2. APPLICATION CONTEXT
        # --------------------------------------------------------------------

        if (
            self.include_context
            and normalized_context
        ):
            context_prompt = self._build_context_prompt(
                normalized_context
            )

            messages.append(
                PromptMessage(
                    role="system",
                    content=context_prompt,
                )
            )

        # --------------------------------------------------------------------
        # 3. CONVERSATION HISTORY
        # --------------------------------------------------------------------

        messages.extend(
            PromptMessage(
                role=item["role"],
                content=item["content"],
            )
            for item in normalized_history[
                -self.max_history_messages:
            ]
        )

        return AssistantPrompt(
            messages=messages,
            metadata={
                "history_messages": len(normalized_history),
                "included_history_messages": min(
                    len(normalized_history),
                    self.max_history_messages,
                ),
                "context_included": bool(
                    self.include_context
                    and normalized_context
                ),
                "context_keys": list(
                    normalized_context.keys()
                ),
                "operational_context_present": (
                    "processing" in normalized_context
                ),
            },
        )

    # ========================================================================
    # CONVENIENCE API
    # ========================================================================

    def build_messages(
        self,
        *,
        history: Optional[List[Dict[str, Any]]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, str]]:
        """
        Convenience method returning only the message list.
        """

        prompt = self.build(
            history=history,
            context=context,
        )

        return prompt.as_messages()

    def build_system_prompt(
        self,
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Build only the system prompt.
        """

        normalized_context = self._normalize_context(
            context or {}
        )

        if (
            not self.include_context
            or not normalized_context
        ):
            return self.system_prompt

        context_prompt = self._build_context_prompt(
            normalized_context
        )

        return (
            f"{self.system_prompt}\n\n"
            f"{context_prompt}"
        )

    # ========================================================================
    # HISTORY NORMALIZATION
    # ========================================================================

    def _normalize_history(
        self,
        history: List[Dict[str, Any]],
    ) -> List[Dict[str, str]]:
        """
        Normalize conversation history.

        Invalid messages are ignored.
        """

        normalized: List[Dict[str, str]] = []

        for message in history:

            if not isinstance(message, Mapping):
                continue

            role = message.get("role")
            content = message.get("content")

            if not isinstance(role, str):
                continue

            if not isinstance(content, str):
                continue

            role = role.strip().lower()
            content = content.strip()

            if role not in {
                "system",
                "user",
                "assistant",
            }:
                continue

            if not content:
                continue

            normalized.append(
                {
                    "role": role,
                    "content": content,
                }
            )

        return normalized

    # ========================================================================
    # CONTEXT NORMALIZATION
    # ========================================================================

    @staticmethod
    def _normalize_context(
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Normalize application context.

        None values are removed.
        """

        if not isinstance(context, Mapping):
            return {}

        normalized: Dict[str, Any] = {}

        for key, value in context.items():

            if value is None:
                continue

            if not isinstance(key, str):
                continue

            clean_key = key.strip()

            if not clean_key:
                continue

            normalized[clean_key] = value

        return normalized

    # ========================================================================
    # CONTEXT PROMPT
    # ========================================================================

    def _build_context_prompt(
        self,
        context: Dict[str, Any],
    ) -> str:
        """
        Convert application context into a controlled system message.

        Operational application data receives explicit grounding
        instructions.
        """

        lines: List[str] = [
            "APPLICATION DATA CONTEXT",
            "========================",
            "",
            "The following information was supplied by the enterprise "
            "application.",
            "",
            "IMPORTANT:",
            "- Treat supplied operational records as authoritative.",
            "- Answer operational questions directly from these records.",
            "- Do not claim that database access is unavailable when records "
            "are present below.",
            "- Do not invent missing records.",
            "- Preserve supplied ordering.",
            "- If the requested number of records exceeds the available "
            "records, report only the records that actually exist.",
            "",
            "<application_context>",
        ]

        # --------------------------------------------------------------------
        # Explicit operational processing instructions
        # --------------------------------------------------------------------

        processing = context.get("processing")

        if isinstance(processing, Mapping):

            lines.extend(
                [
                    "<operational_processing>",
                    "The following processing information is authoritative "
                    "application data.",
                    "",
                    "For questions about processed documents, processing "
                    "jobs, completion, status, or recency, use these records "
                    "as the source of truth.",
                    "",
                ]
            )

            query_type = processing.get(
                "query_type"
            )

            if query_type is not None:
                lines.append(
                    f"query_type: {query_type}"
                )

            requested_limit = processing.get(
                "requested_limit"
            )

            if requested_limit is not None:
                lines.append(
                    f"requested_limit: {requested_limit}"
                )

            result_count = processing.get(
                "result_count"
            )

            if result_count is not None:
                lines.append(
                    f"result_count: {result_count}"
                )

            available = processing.get(
                "available"
            )

            if available is not None:
                lines.append(
                    f"available: {available}"
                )

            source = processing.get(
                "source"
            )

            if source is not None:
                lines.append(
                    f"source: {source}"
                )

            documents = processing.get(
                "documents"
            )

            if documents:
                lines.extend(
                    [
                        "",
                        "PROCESSED DOCUMENTS",
                        "-------------------",
                    ]
                )

                self._append_structured_value(
                    lines,
                    documents,
                    indent=0,
                )

            jobs = processing.get(
                "jobs"
            )

            if jobs:
                lines.extend(
                    [
                        "",
                        "PROCESSING JOBS",
                        "----------------",
                    ]
                )

                self._append_structured_value(
                    lines,
                    jobs,
                    indent=0,
                )

            lines.extend(
                [
                    "",
                    "</operational_processing>",
                    "",
                ]
            )

        # --------------------------------------------------------------------
        # Other context
        # --------------------------------------------------------------------

        for key, value in context.items():

            if key == "processing":
                continue

            formatted_value = self._format_context_value(
                value
            )

            safe_key = self._safe_tag_name(
                key
            )

            lines.extend(
                [
                    f"<{safe_key}>",
                    formatted_value,
                    f"</{safe_key}>",
                ]
            )

        lines.append(
            "</application_context>"
        )

        return "\n".join(lines)

    # ========================================================================
    # STRUCTURED VALUE
    # ========================================================================

    def _append_structured_value(
        self,
        lines: List[str],
        value: Any,
        *,
        indent: int = 0,
    ) -> None:
        """
        Append structured application data in an LLM-readable form.
        """

        prefix = "  " * indent

        if isinstance(value, Mapping):

            for key, item in value.items():

                if isinstance(
                    item,
                    (
                        Mapping,
                        list,
                        tuple,
                    ),
                ):
                    lines.append(
                        f"{prefix}{key}:"
                    )

                    self._append_structured_value(
                        lines,
                        item,
                        indent=indent + 1,
                    )

                else:
                    lines.append(
                        f"{prefix}{key}: {item}"
                    )

            return

        if isinstance(
            value,
            (
                list,
                tuple,
                set,
            ),
        ):

            for index, item in enumerate(value, start=1):

                if isinstance(
                    item,
                    Mapping,
                ):
                    lines.append(
                        f"{prefix}Record {index}:"
                    )

                    self._append_structured_value(
                        lines,
                        item,
                        indent=indent + 1,
                    )

                else:
                    lines.append(
                        f"{prefix}- {item}"
                    )

            return

        lines.append(
            f"{prefix}{value}"
        )

    # ========================================================================
    # GENERIC CONTEXT VALUE
    # ========================================================================

    def _format_context_value(
        self,
        value: Any,
    ) -> str:
        """
        Convert arbitrary context values into readable text.
        """

        if isinstance(value, str):
            return value.strip()

        if isinstance(value, Mapping):

            lines: List[str] = []

            for key, item in value.items():

                lines.append(
                    f"{key}: "
                    f"{self._format_context_value(item)}"
                )

            return "\n".join(lines)

        if isinstance(
            value,
            (
                list,
                tuple,
                set,
            ),
        ):

            return "\n".join(
                f"- {self._format_context_value(item)}"
                for item in value
            )

        return str(value)

    # ========================================================================
    # SAFETY / FORMATTING
    # ========================================================================

    @staticmethod
    def _safe_tag_name(
        value: str,
    ) -> str:
        """
        Convert arbitrary context keys into safe XML-like tag names.
        """

        normalized = "".join(
            character
            if character.isalnum()
            or character in "_-"
            else "_"
            for character in value
        )

        normalized = normalized.strip("_")

        return normalized or "context"