"""
app/assistant/orchestrator.py

Central orchestration layer for the conversational assistant.

Responsibilities
----------------
- Receive an assistant request.
- Manage conversation/session state.
- Route the user query.
- Retrieve application context.
- Build the LLM prompt.
- Verify the application context is present in the final prompt.
- Call the canonical LLMManager.
- Return a normalized assistant response.

Architecture
------------

    API
     |
     v
AssistantService
     |
     v
AssistantOrchestrator
     |
     +------------------------+
     |                        |
     v                        v
 QueryRouter             ContextService
     |                        |
     |                 +------+-------+
     |                 |              |
     |                 v              v
     |             Operational      Knowledge
     |                Data            /RAG
     |                 |              |
     +-----------------+--------------+
                       |
                       v
                 PromptBuilder
                       |
                       v
                   LLMManager
                       |
                       v
                  ModelRouter
                       |
                       v
                LLM Provider

Important
---------
The orchestrator does NOT:

- access FastAPI request objects
- directly call OpenRouter
- directly access database sessions
- contain repository implementation details
- contain HTTP response logic
- know which LLM provider is being used

The orchestrator DOES verify that application context retrieved by
ContextService survives the PromptBuilder -> LLMManager boundary.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional
from uuid import UUID


# =====================================================================
# NORMALIZED ASSISTANT MESSAGE
# =====================================================================


@dataclass
class AssistantMessage:
    """Normalized message returned by the assistant."""

    role: str
    content: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
        }


# =====================================================================
# NORMALIZED ASSISTANT RESULT
# =====================================================================


@dataclass
class AssistantResult:
    """Normalized result returned by AssistantOrchestrator."""

    session_id: UUID
    message: AssistantMessage

    model: Optional[str] = None
    usage: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": str(self.session_id),
            "message": self.message.to_dict(),
            "model": self.model,
            "usage": self.usage,
            "metadata": self.metadata,
        }


# =====================================================================
# ORCHESTRATOR
# =====================================================================


class AssistantOrchestrator:
    """
    Coordinates the complete assistant execution flow.
    """

    def __init__(
        self,
        conversation_manager: Any,
        prompt_builder: Any,
        llm_manager: Any,
        query_router: Any | None = None,
        context_service: Any | None = None,
    ) -> None:

        if conversation_manager is None:
            raise ValueError(
                "AssistantOrchestrator requires a ConversationManager."
            )

        if prompt_builder is None:
            raise ValueError(
                "AssistantOrchestrator requires a PromptBuilder."
            )

        if llm_manager is None:
            raise ValueError(
                "AssistantOrchestrator requires an LLMManager."
            )

        self.conversation_manager = conversation_manager
        self.prompt_builder = prompt_builder
        self.llm_manager = llm_manager
        self.query_router = query_router
        self.context_service = context_service

    # =================================================================
    # PUBLIC EXECUTION API
    # =================================================================

    async def run(
        self,
        *,
        session_id: Optional[UUID],
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> AssistantResult:

        normalized_message = self._validate_message(message)

        caller_context = self._normalize_context(context)

        # -------------------------------------------------------------
        # 1. Resolve/create session
        # -------------------------------------------------------------

        resolved_session_id = await self._resolve_session(
            session_id=session_id,
            context=caller_context,
        )

        # -------------------------------------------------------------
        # 2. Load history
        # -------------------------------------------------------------

        history = await self._get_history(
            session_id=resolved_session_id,
        )

        # -------------------------------------------------------------
        # 3. Persist user message
        # -------------------------------------------------------------

        await self._append_message(
            session_id=resolved_session_id,
            role="user",
            content=normalized_message,
        )

        # -------------------------------------------------------------
        # 4. Add current message to prompt history
        # -------------------------------------------------------------

        history_for_prompt = [
            *history,
            {
                "role": "user",
                "content": normalized_message,
            },
        ]

        # -------------------------------------------------------------
        # 5. Build application context
        # -------------------------------------------------------------

        application_context = await self._build_application_context(
            message=normalized_message,
            context=caller_context,
            session_id=resolved_session_id,
            history=history_for_prompt,
        )

        # -------------------------------------------------------------
        # 6. Build prompt
        # -------------------------------------------------------------

        prompt = await self._build_prompt(
            history=history_for_prompt,
            context=application_context,
        )

        # -------------------------------------------------------------
        # 7. Extract final messages
        # -------------------------------------------------------------

        messages = self._extract_prompt_messages(prompt)

        if not messages:
            raise RuntimeError(
                "PromptBuilder produced an empty prompt."
            )

        # -------------------------------------------------------------
        # 8. CRITICAL CONTEXT HANDOFF VALIDATION
        # -------------------------------------------------------------

        prompt_context_validation = (
            self._validate_application_context_handoff(
                application_context=application_context,
                messages=messages,
            )
        )

        # -------------------------------------------------------------
        # 9. Execute LLM
        # -------------------------------------------------------------

        llm_result = await self._generate(
            messages=messages,
        )

        # -------------------------------------------------------------
        # 10. Extract response
        # -------------------------------------------------------------

        assistant_content = self._extract_content(
            llm_result
        )

        if not assistant_content:
            raise RuntimeError(
                "LLM returned an empty assistant response."
            )

        # -------------------------------------------------------------
        # 11. Persist assistant response
        # -------------------------------------------------------------

        await self._append_message(
            session_id=resolved_session_id,
            role="assistant",
            content=assistant_content,
        )

        # -------------------------------------------------------------
        # 12. Return normalized result
        # -------------------------------------------------------------

        return AssistantResult(
            session_id=resolved_session_id,
            message=AssistantMessage(
                role="assistant",
                content=assistant_content,
            ),
            model=self._extract_model(llm_result),
            usage=self._extract_usage(llm_result),
            metadata=self._build_response_metadata(
                llm_result=llm_result,
                application_context=application_context,
                prompt_context_validation=prompt_context_validation,
                prompt_messages=messages,
            ),
        )

    # =================================================================
    # APPLICATION CONTEXT
    # =================================================================

    async def _build_application_context(
        self,
        *,
        message: str,
        context: Dict[str, Any],
        session_id: UUID,
        history: List[Dict[str, Any]],
    ) -> Dict[str, Any]:

        base_context = dict(context)

        # -------------------------------------------------------------
        # 1. Route query
        # -------------------------------------------------------------

        route = await self._route_query(
            message=message,
            context=base_context,
        )

        if route is not None:
            base_context["query_route"] = route

        # -------------------------------------------------------------
        # 2. Retrieve application context
        # -------------------------------------------------------------

        if self.context_service is None:
            return base_context

        enriched_context = await self._retrieve_context(
            message=message,
            context=base_context,
            route=route,
            session_id=session_id,
            history=history,
        )

        # -------------------------------------------------------------
        # 3. Normalize returned context
        # -------------------------------------------------------------

        enriched_context = self._normalize_mapping_result(
            enriched_context
        )

        if enriched_context is None:
            return base_context

        # -------------------------------------------------------------
        # 4. Merge application context
        # -------------------------------------------------------------

        merged_context = dict(base_context)

        merged_context.update(
            enriched_context
        )

        # -------------------------------------------------------------
        # 5. Preserve route
        #
        # ContextService should not accidentally overwrite the
        # canonical normalized route with another representation.
        # -------------------------------------------------------------

        if route is not None:
            merged_context["query_route"] = route

        return merged_context

    # =================================================================
    # QUERY ROUTING
    # =================================================================

    async def _route_query(
        self,
        *,
        message: str,
        context: Dict[str, Any],
    ) -> Any:

        router = self.query_router

        if router is None:
            return None

        for method_name in (
            "route",
            "classify",
            "resolve",
            "route_query",
        ):

            method = getattr(
                router,
                method_name,
                None,
            )

            if not callable(method):
                continue

            # ---------------------------------------------------------
            # Preferred interface
            # ---------------------------------------------------------

            try:

                result = method(
                    query=message,
                    context=context,
                )

            except TypeError:

                # -----------------------------------------------------
                # Compatibility interface
                # -----------------------------------------------------

                try:

                    result = method(
                        message
                    )

                except TypeError:
                    continue

            if inspect.isawaitable(result):
                result = await result

            normalized_route = self._normalize_route(
                result
            )

            if normalized_route is not None:
                return normalized_route

        return None

    @staticmethod
    def _normalize_route(route: Any) -> Any:
        """
        Normalize QueryRouter output into a ContextService-friendly
        representation.

        This is critical.

        QueryRouter may return:

            "operational_processing"

        or:

            {
                "route": "operational_processing",
                "confidence": 0.97,
                ...
            }

        or a QueryRoute object:

            QueryRoute(
                route="operational_processing",
                confidence=0.97,
                ...
            )

        The previous implementation did not inspect `.route`, causing
        QueryRoute objects to fall through to str(route), producing:

            "QueryRoute(route='operational_processing', ...)"

        ContextService then could not reliably recognize the route.

        The canonical normalized route returned by this method is
        preferably the actual route string, while preserving structured
        routing information separately through context metadata when
        available.
        """

        if route is None:
            return None

        # -------------------------------------------------------------
        # Already primitive
        # -------------------------------------------------------------

        if isinstance(
            route,
            str,
        ):
            return route.strip() or None

        if isinstance(
            route,
            (int, float, bool),
        ):
            return route

        # -------------------------------------------------------------
        # Mapping / dictionary
        # -------------------------------------------------------------

        if isinstance(
            route,
            Mapping,
        ):

            route_value = (
                route.get("route")
                or route.get("name")
                or route.get("type")
                or route.get("value")
            )

            if isinstance(
                route_value,
                str,
            ):
                return route_value.strip() or None

            if route_value is not None:
                return route_value

            # If no route field exists, preserve the mapping.
            return dict(route)

        # -------------------------------------------------------------
        # CRITICAL:
        # QueryRoute-like object with `.route`
        # -------------------------------------------------------------

        route_attribute = getattr(
            route,
            "route",
            None,
        )

        if route_attribute is not None:

            if isinstance(
                route_attribute,
                str,
            ):
                return route_attribute.strip() or None

            if isinstance(
                route_attribute,
                Mapping,
            ):
                return dict(route_attribute)

            if isinstance(
                route_attribute,
                (int, float, bool),
            ):
                return route_attribute

        # -------------------------------------------------------------
        # Enum-like `.value`
        # -------------------------------------------------------------

        value = getattr(
            route,
            "value",
            None,
        )

        if value is not None:

            if isinstance(
                value,
                str,
            ):
                return value.strip() or None

            if isinstance(
                value,
                Mapping,
            ):

                nested_route = (
                    value.get("route")
                    or value.get("name")
                    or value.get("type")
                    or value.get("value")
                )

                if nested_route is not None:
                    return nested_route

                return dict(value)

            return value

        # -------------------------------------------------------------
        # Pydantic model
        # -------------------------------------------------------------

        model_dump = getattr(
            route,
            "model_dump",
            None,
        )

        if callable(model_dump):

            try:

                dumped = model_dump()

                if isinstance(
                    dumped,
                    Mapping,
                ):

                    route_value = (
                        dumped.get("route")
                        or dumped.get("name")
                        or dumped.get("type")
                        or dumped.get("value")
                    )

                    if route_value is not None:
                        return route_value

                    return dict(dumped)

            except Exception:
                pass

        # -------------------------------------------------------------
        # Legacy object -> dict
        # -------------------------------------------------------------

        to_dict = getattr(
            route,
            "to_dict",
            None,
        )

        if callable(to_dict):

            try:

                dumped = to_dict()

                if isinstance(
                    dumped,
                    Mapping,
                ):

                    route_value = (
                        dumped.get("route")
                        or dumped.get("name")
                        or dumped.get("type")
                        or dumped.get("value")
                    )

                    if route_value is not None:
                        return route_value

                    return dict(dumped)

            except Exception:
                pass

        # -------------------------------------------------------------
        # Last resort
        # -------------------------------------------------------------

        return str(route)

    # =================================================================
    # CONTEXT SERVICE
    # =================================================================

    async def _retrieve_context(
        self,
        *,
        message: str,
        context: Dict[str, Any],
        route: Any,
        session_id: UUID,
        history: List[Dict[str, Any]],
    ) -> Any:
        """
        Retrieve authoritative application context from ContextService.

        ContextService is request-scoped and owns database/service
        access. The orchestrator only supplies the query and execution
        metadata.

        The preferred interface is:

            build_context(
                query=...,
                context=...,
                route=...,
                session_id=...,
                history=...,
            )

        Compatibility fallbacks are retained for older service
        implementations.
        """

        service = self.context_service

        if service is None:
            return None

        methods = (
            "build_context",
            "get_context",
            "retrieve_context",
            "resolve",
        )

        for method_name in methods:

            method = getattr(
                service,
                method_name,
                None,
            )

            if not callable(method):
                continue

            result = None
            method_called = False

            # ---------------------------------------------------------
            # Preferred rich interface
            # ---------------------------------------------------------

            try:

                result = method(
                    query=message,
                    context=context,
                    route=route,
                    session_id=session_id,
                    history=history,
                )

                method_called = True

            except TypeError:

                # -----------------------------------------------------
                # Compatibility interface
                # -----------------------------------------------------

                try:

                    result = method(
                        query=message,
                        context=context,
                    )

                    method_called = True

                except TypeError:

                    try:

                        result = method(
                            message
                        )

                        method_called = True

                    except TypeError:
                        continue

            if not method_called:
                continue

            if inspect.isawaitable(result):
                result = await result

            return self._normalize_mapping_result(
                result
            )

        return None

    # =================================================================
    # CONTEXT RESULT NORMALIZATION
    # =================================================================

    @staticmethod
    def _normalize_mapping_result(
        result: Any,
    ) -> Optional[Dict[str, Any]]:
        """
        Normalize ContextService output.

        Supports:

        - dict
        - Mapping
        - Pydantic models
        - objects exposing to_dict()

        This prevents a valid ContextService result from being silently
        discarded because it is not literally a dict.
        """

        if result is None:
            return None

        if isinstance(
            result,
            Mapping,
        ):
            return dict(result)

        model_dump = getattr(
            result,
            "model_dump",
            None,
        )

        if callable(model_dump):

            try:

                dumped = model_dump()

                if isinstance(
                    dumped,
                    Mapping,
                ):
                    return dict(dumped)

            except Exception:
                pass

        to_dict = getattr(
            result,
            "to_dict",
            None,
        )

        if callable(to_dict):

            try:

                dumped = to_dict()

                if isinstance(
                    dumped,
                    Mapping,
                ):
                    return dict(dumped)

            except Exception:
                pass

        return None

    # =================================================================
    # CONTEXT HANDOFF VALIDATION
    # =================================================================

    @staticmethod
    def _validate_application_context_handoff(
        *,
        application_context: Dict[str, Any],
        messages: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        """
        Verify that operational application context exists and that
        PromptBuilder actually placed it into the final LLM messages.

        This is deliberately done at the orchestration boundary.

        ContextService owns retrieval.
        PromptBuilder owns formatting.
        This method verifies the two components are actually connected.
        """

        processing = application_context.get(
            "processing"
        )

        operational_context_present = (
            isinstance(
                processing,
                Mapping,
            )
            and bool(
                processing.get("available")
            )
        )

        document_count = 0

        if isinstance(
            processing,
            Mapping,
        ):

            documents = processing.get(
                "documents"
            )

            if isinstance(
                documents,
                list,
            ):
                document_count = len(documents)

        # -------------------------------------------------------------
        # Inspect final messages
        # -------------------------------------------------------------

        combined_prompt = "\n\n".join(
            str(
                item.get(
                    "content",
                    "",
                )
            )
            for item in messages
            if isinstance(
                item,
                Mapping,
            )
        )

        processing_context_in_prompt = (
            "operational_processing" in combined_prompt
            or "<operational_processing>" in combined_prompt
            or "APPLICATION DATA CONTEXT" in combined_prompt
            or "recently_processed_documents" in combined_prompt
        )

        result = {
            "application_context_present": bool(
                application_context
            ),
            "operational_context_present": (
                operational_context_present
            ),
            "operational_document_count": document_count,
            "processing_context_in_prompt": (
                processing_context_in_prompt
            ),
            "prompt_message_count": len(
                messages
            ),
        }

        # -------------------------------------------------------------
        # Stronger validation:
        #
        # If authoritative operational context exists with actual
        # records, the prompt must contain the records/context section.
        # -------------------------------------------------------------

        if (
            operational_context_present
            and not processing_context_in_prompt
        ):
            raise RuntimeError(
                "Application processing context was retrieved "
                "successfully but was not included in the final "
                "LLM prompt. "
                f"Retrieved {document_count} operational document(s). "
                "Check PromptBuilder.build() and context formatting."
            )

        return result

    # =================================================================
    # SESSION HANDLING
    # =================================================================

    async def _resolve_session(
        self,
        *,
        session_id: Optional[UUID],
        context: Dict[str, Any],
    ) -> UUID:

        if session_id is not None:
            return session_id

        manager = self.conversation_manager

        create_session = getattr(
            manager,
            "create_session",
            None,
        )

        if callable(create_session):

            result = create_session(
                context=context
            )

            if inspect.isawaitable(result):
                result = await result

            resolved = self._extract_session_id(
                result
            )

            if resolved is not None:
                return resolved

        raise RuntimeError(
            "ConversationManager could not create a new session."
        )

    async def _get_history(
        self,
        *,
        session_id: UUID,
    ) -> List[Dict[str, Any]]:

        manager = self.conversation_manager

        get_history = getattr(
            manager,
            "get_history",
            None,
        )

        if callable(get_history):

            result = get_history(
                session_id
            )

            if inspect.isawaitable(result):
                result = await result

            return self._normalize_history(
                result
            )

        get_messages = getattr(
            manager,
            "get_messages",
            None,
        )

        if callable(get_messages):

            result = get_messages(
                session_id
            )

            if inspect.isawaitable(result):
                result = await result

            return self._normalize_history(
                result
            )

        return []

    async def _append_message(
        self,
        *,
        session_id: UUID,
        role: str,
        content: str,
    ) -> None:

        manager = self.conversation_manager

        add_message = getattr(
            manager,
            "add_message",
            None,
        )

        if callable(add_message):

            result = add_message(
                session_id=session_id,
                role=role,
                content=content,
            )

            if inspect.isawaitable(result):
                await result

            return

        append_message = getattr(
            manager,
            "append_message",
            None,
        )

        if callable(append_message):

            result = append_message(
                session_id=session_id,
                role=role,
                content=content,
            )

            if inspect.isawaitable(result):
                await result

            return

        raise RuntimeError(
            "ConversationManager does not implement "
            "add_message() or append_message()."
        )

    # =================================================================
    # PROMPT CONSTRUCTION
    # =================================================================

    async def _build_prompt(
        self,
        *,
        history: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> Any:

        builder = self.prompt_builder

        build = getattr(
            builder,
            "build",
            None,
        )

        if not callable(build):
            raise RuntimeError(
                "PromptBuilder does not implement build()."
            )

        result = build(
            history=history,
            context=context,
        )

        if inspect.isawaitable(result):
            result = await result

        if result is None:
            raise RuntimeError(
                "PromptBuilder returned None."
            )

        return result

    # =================================================================
    # PROMPT NORMALIZATION
    # =================================================================

    @classmethod
    def _extract_prompt_messages(
        cls,
        prompt: Any,
    ) -> List[Dict[str, str]]:

        if prompt is None:
            return []

        as_messages = getattr(
            prompt,
            "as_messages",
            None,
        )

        if callable(as_messages):

            result = as_messages()

            if inspect.isawaitable(result):
                # Prompt objects should normally expose a synchronous
                # as_messages(), but don't silently mishandle an
                # awaitable implementation.
                raise RuntimeError(
                    "PromptBuilder.as_messages() returned an awaitable. "
                    "Use an async prompt-building interface instead."
                )

            if result is None:
                return []

            return cls._normalize_prompt_messages(
                result
            )

        if isinstance(
            prompt,
            Mapping,
        ):

            messages = prompt.get(
                "messages"
            )

            if messages is not None:
                return cls._normalize_prompt_messages(
                    messages
                )

        if isinstance(
            prompt,
            list,
        ):
            return cls._normalize_prompt_messages(
                prompt
            )

        messages = getattr(
            prompt,
            "messages",
            None,
        )

        if messages is not None:
            return cls._normalize_prompt_messages(
                messages
            )

        raise RuntimeError(
            "PromptBuilder returned an unsupported prompt format."
        )

    @staticmethod
    def _normalize_prompt_messages(
        messages: Any,
    ) -> List[Dict[str, str]]:

        if not messages:
            return []

        normalized: List[
            Dict[str, str]
        ] = []

        for item in messages:

            if isinstance(
                item,
                Mapping,
            ):

                role = item.get(
                    "role"
                )

                content = item.get(
                    "content"
                )

            else:

                role = getattr(
                    item,
                    "role",
                    None,
                )

                content = getattr(
                    item,
                    "content",
                    None,
                )

            if role is None:
                continue

            if content is None:
                continue

            role = str(
                role
            ).strip()

            content = str(
                content
            ).strip()

            if not role or not content:
                continue

            normalized.append(
                {
                    "role": role,
                    "content": content,
                }
            )

        return normalized

    # =================================================================
    # LLM EXECUTION
    # =================================================================

    async def _generate(
        self,
        *,
        messages: List[Dict[str, str]],
    ) -> Any:

        if not messages:
            raise ValueError(
                "Cannot execute LLM request with empty messages."
            )

        manager = self.llm_manager

        generate = getattr(
            manager,
            "generate",
            None,
        )

        if callable(generate):

            result = generate(
                messages=messages,
            )

            if inspect.isawaitable(result):
                result = await result

            return result

        chat = getattr(
            manager,
            "chat",
            None,
        )

        if callable(chat):

            result = chat(
                messages=messages,
            )

            if inspect.isawaitable(result):
                result = await result

            return result

        raise RuntimeError(
            "LLMManager does not implement generate() or chat()."
        )

    # =================================================================
    # RESPONSE NORMALIZATION
    # =================================================================

    @staticmethod
    def _extract_content(
        result: Any,
    ) -> str:

        if result is None:
            return ""

        if isinstance(
            result,
            str,
        ):
            return result.strip()

        if isinstance(
            result,
            Mapping,
        ):

            for key in (
                "content",
                "text",
                "response",
                "output",
            ):

                value = result.get(
                    key
                )

                if isinstance(
                    value,
                    str,
                ):
                    return value.strip()

            message = result.get(
                "message"
            )

            if isinstance(
                message,
                Mapping,
            ):

                content = message.get(
                    "content"
                )

                if isinstance(
                    content,
                    str,
                ):
                    return content.strip()

            choices = result.get(
                "choices"
            )

            if isinstance(
                choices,
                list,
            ) and choices:

                first_choice = choices[0]

                if isinstance(
                    first_choice,
                    Mapping,
                ):

                    message = first_choice.get(
                        "message"
                    )

                    if isinstance(
                        message,
                        Mapping,
                    ):

                        content = message.get(
                            "content"
                        )

                        if isinstance(
                            content,
                            str,
                        ):
                            return content.strip()

        for attribute in (
            "content",
            "text",
            "response",
            "output",
        ):

            value = getattr(
                result,
                attribute,
                None,
            )

            if isinstance(
                value,
                str,
            ):
                return value.strip()

        choices = getattr(
            result,
            "choices",
            None,
        )

        if choices:

            try:

                first_choice = choices[0]

                message = getattr(
                    first_choice,
                    "message",
                    None,
                )

                if message is not None:

                    content = getattr(
                        message,
                        "content",
                        None,
                    )

                    if isinstance(
                        content,
                        str,
                    ):
                        return content.strip()

            except (
                IndexError,
                TypeError,
            ):
                pass

        return ""

    @staticmethod
    def _extract_model(
        result: Any,
    ) -> Optional[str]:

        if result is None:
            return None

        if isinstance(
            result,
            Mapping,
        ):

            model = result.get(
                "model"
            )

            if isinstance(
                model,
                str,
            ):
                return model

        model = getattr(
            result,
            "model",
            None,
        )

        if isinstance(
            model,
            str,
        ):
            return model

        return None

    @staticmethod
    def _extract_usage(
        result: Any,
    ) -> Optional[Dict[str, Any]]:

        if result is None:
            return None

        if isinstance(
            result,
            Mapping,
        ):

            usage = result.get(
                "usage"
            )

            if isinstance(
                usage,
                Mapping,
            ):
                return dict(
                    usage
                )

        usage = getattr(
            result,
            "usage",
            None,
        )

        if usage is None:
            return None

        if isinstance(
            usage,
            Mapping,
        ):
            return dict(
                usage
            )

        model_dump = getattr(
            usage,
            "model_dump",
            None,
        )

        if callable(model_dump):

            try:

                dumped = model_dump()

                if isinstance(
                    dumped,
                    Mapping,
                ):
                    return dict(
                        dumped
                    )

            except Exception:
                pass

        if hasattr(
            usage,
            "__dict__",
        ):

            try:
                return dict(
                    usage.__dict__
                )

            except Exception:
                pass

        return None

    @staticmethod
    def _extract_metadata(
        result: Any,
    ) -> Dict[str, Any]:

        if result is None:
            return {}

        if isinstance(
            result,
            Mapping,
        ):

            metadata = result.get(
                "metadata"
            )

            if isinstance(
                metadata,
                Mapping,
            ):
                return dict(
                    metadata
                )

        metadata = getattr(
            result,
            "metadata",
            None,
        )

        if isinstance(
            metadata,
            Mapping,
        ):
            return dict(
                metadata
            )

        return {}

    def _build_response_metadata(
        self,
        *,
        llm_result: Any,
        application_context: Dict[str, Any],
        prompt_context_validation: Dict[str, Any],
        prompt_messages: List[Dict[str, str]],
    ) -> Dict[str, Any]:

        metadata = self._extract_metadata(
            llm_result
        )

        route = application_context.get(
            "query_route"
        )

        if route is not None:
            metadata["query_route"] = route

        # -------------------------------------------------------------
        # Context diagnostics
        # -------------------------------------------------------------

        processing = application_context.get(
            "processing"
        )

        if isinstance(
            processing,
            Mapping,
        ):

            metadata["context_source"] = processing.get(
                "source"
            )

            metadata["context_authoritative"] = processing.get(
                "authoritative"
            )

            metadata["context_query_type"] = processing.get(
                "query_type"
            )

            metadata["context_result_count"] = processing.get(
                "result_count"
            )

        metadata["prompt_message_count"] = len(
            prompt_messages
        )

        metadata["application_context_present"] = (
            prompt_context_validation.get(
                "application_context_present",
                False,
            )
        )

        metadata["operational_context_present"] = (
            prompt_context_validation.get(
                "operational_context_present",
                False,
            )
        )

        metadata["operational_document_count"] = (
            prompt_context_validation.get(
                "operational_document_count",
                0,
            )
        )

        metadata["processing_context_in_prompt"] = (
            prompt_context_validation.get(
                "processing_context_in_prompt",
                False,
            )
        )

        return metadata

    # =================================================================
    # VALIDATION / NORMALIZATION
    # =================================================================

    @staticmethod
    def _validate_message(
        message: str,
    ) -> str:

        if not isinstance(
            message,
            str,
        ):
            raise TypeError(
                "Assistant message must be a string."
            )

        normalized = message.strip()

        if not normalized:
            raise ValueError(
                "Assistant message cannot be empty."
            )

        return normalized

    @staticmethod
    def _normalize_context(
        context: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:

        if context is None:
            return {}

        if not isinstance(
            context,
            dict,
        ):
            raise TypeError(
                "Assistant context must be a dictionary."
            )

        return dict(
            context
        )

    @staticmethod
    def _extract_session_id(
        result: Any,
    ) -> Optional[UUID]:

        if result is None:
            return None

        if isinstance(
            result,
            UUID,
        ):
            return result

        if isinstance(
            result,
            Mapping,
        ):

            value = (
                result.get(
                    "session_id"
                )
                or result.get(
                    "id"
                )
            )

            if value is not None:

                try:

                    return UUID(
                        str(value)
                    )

                except (
                    ValueError,
                    TypeError,
                ):
                    return None

        for attribute in (
            "session_id",
            "id",
        ):

            value = getattr(
                result,
                attribute,
                None,
            )

            if value is not None:

                try:

                    return UUID(
                        str(value)
                    )

                except (
                    ValueError,
                    TypeError,
                ):
                    return None

        return None

    @staticmethod
    def _normalize_history(
        history: Any,
    ) -> List[Dict[str, Any]]:

        if not history:
            return []

        normalized: List[
            Dict[str, Any]
        ] = []

        for item in history:

            if isinstance(
                item,
                Mapping,
            ):

                role = item.get(
                    "role"
                )

                content = item.get(
                    "content"
                )

            else:

                role = getattr(
                    item,
                    "role",
                    None,
                )

                content = getattr(
                    item,
                    "content",
                    None,
                )

            if not role:
                continue

            if content is None:
                continue

            role = str(
                role
            ).strip()

            content = str(
                content
            ).strip()

            if not role or not content:
                continue

            normalized.append(
                {
                    "role": role,
                    "content": content,
                }
            )

        return normalized


# =====================================================================
# PUBLIC API
# =====================================================================


__all__ = [
    "AssistantMessage",
    "AssistantResult",
    "AssistantOrchestrator",
]