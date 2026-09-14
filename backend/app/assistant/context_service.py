"""
app/assistant/context_service.py

Application context retrieval for the Assistant.

Responsibilities
----------------
- Build application-backed context for Assistant queries.
- Retrieve operational processing information from PostgreSQL.
- Retrieve recently completed documents using ProcessingJob.completed_at.
- Preserve deterministic ordering for recency-based queries.
- Serialize SQLAlchemy models into LLM-safe dictionaries.
- Keep database access isolated from PromptBuilder and LLM providers.

Architecture

    AssistantOrchestrator
            |
            v
      ContextService
            |
            v
       PostgreSQL
            |
            +--------------------+
            |                    |
            v                    v
    ProcessingJob       DocumentVersion
                              |
                              v
                          Document

Operational queries are answered from persisted application data.
The LLM is responsible only for explaining the retrieved data.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.document import Document
from app.db.models.document_version import DocumentVersion
from app.db.models.processing_job import ProcessingJob


class ContextService:
    """
    Builds authoritative application context for Assistant queries.

    Operational processing queries are answered directly from
    persisted PostgreSQL records.

    The LLM must never be responsible for discovering or inventing
    operational application data.
    """

    # ======================================================================
    # INITIALIZATION
    # ======================================================================

    def __init__(
        self,
        db: AsyncSession,
        processing_repository: Any | None = None,
        search_service: Any | None = None,
        review_service: Any | None = None,
        intelligence_service: Any | None = None,
    ) -> None:
        self.db = db
        self.processing_repository = processing_repository
        self.search_service = search_service
        self.review_service = review_service
        self.intelligence_service = intelligence_service

    # ======================================================================
    # PUBLIC API
    # ======================================================================

    async def build_context(
        self,
        query: str,
        *,
        route: Any | None = None,
        context: Mapping[str, Any] | None = None,
        session_id: Any | None = None,
        history: Sequence[Any] | None = None,
        **_: Any,
    ) -> dict[str, Any]:
        """
        Build application-backed context for an Assistant query.

        The additional `session_id` and `history` parameters are accepted
        intentionally because AssistantOrchestrator may provide them.

        ContextService does not currently need them for operational
        PostgreSQL retrieval, but accepting them keeps the service
        compatible with the orchestrator contract and prevents the
        operational route from being lost through fallback invocation.

        Parameters
        ----------
        query:
            Original user query.

        route:
            QueryRouter result.

        context:
            Existing caller/application context.

        session_id:
            Optional Assistant session identifier.

        history:
            Optional conversation history.

        Returns
        -------
        dict[str, Any]
            Application context consumed by AssistantOrchestrator and
            PromptBuilder.
        """

        # ------------------------------------------------------------------
        # Preserve caller context.
        # ------------------------------------------------------------------

        result: dict[str, Any] = dict(context or {})

        # ------------------------------------------------------------------
        # Normalize the route.
        #
        # Important:
        # If the orchestrator/fallback does not explicitly provide route,
        # recover it from context["query_route"].
        # ------------------------------------------------------------------

        normalized_route = self._normalize_route(route)

        if normalized_route == "general":
            context_route = result.get("query_route")

            recovered_route = self._normalize_route(
                context_route
            )

            if recovered_route != "general":
                normalized_route = recovered_route

        # ------------------------------------------------------------------
        # Application context metadata.
        # ------------------------------------------------------------------

        result["context_source"] = "application"
        result["context_route"] = normalized_route

        # Preserve the existing query route explicitly.
        #
        # This is useful for diagnostics and prevents route information
        # from disappearing between QueryRouter and ContextService.
        if "query_route" not in result:
            result["query_route"] = normalized_route

        # ------------------------------------------------------------------
        # Operational database-backed context.
        # ------------------------------------------------------------------

        if normalized_route in {
            "operational_processing",
            "operational_documents",
            "hybrid",
        }:
            processing_context = await self._get_processing_context(
                query=query,
            )

            result.update(processing_context)

        return result

    # ======================================================================
    # PROCESSING CONTEXT
    # ======================================================================

    async def _get_processing_context(
        self,
        query: str,
    ) -> dict[str, Any]:
        """
        Retrieve authoritative database-backed processing context.

        The retrieval strategy is deterministic and based on the user's
        query.

        Supported specialized intent:

            recently_processed_documents

        Generic processing queries fall back to recent processing jobs.
        """

        intent = self._detect_processing_intent(query)

        # ------------------------------------------------------------------
        # Recently processed documents
        # ------------------------------------------------------------------

        if intent == "recently_processed_documents":

            requested_limit = self._extract_limit(
                query=query,
                default=5,
                maximum=50,
            )

            jobs = await self._get_recently_completed_jobs(
                limit=requested_limit,
            )

            documents = self._serialize_unique_documents(
                jobs
            )

            return {
                "processing": {
                    "available": True,
                    "authoritative": True,
                    "source": "postgresql",
                    "query_type": "recently_processed_documents",
                    "requested_limit": requested_limit,
                    "result_count": len(documents),
                    "documents": documents,
                    "jobs": [
                        self._serialize_processing_job(job)
                        for job in jobs
                    ],
                }
            }

        # ------------------------------------------------------------------
        # Generic processing query
        # ------------------------------------------------------------------

        jobs = await self._list_processing_jobs_with_documents(
            limit=10,
        )

        documents = self._serialize_unique_documents(
            jobs
        )

        return {
            "processing": {
                "available": True,
                "authoritative": True,
                "source": "postgresql",
                "query_type": "processing_jobs",
                "requested_limit": 10,
                "result_count": len(jobs),
                "jobs": [
                    self._serialize_processing_job(job)
                    for job in jobs
                ],
                "documents": documents,
            }
        }

    # ======================================================================
    # RECENTLY COMPLETED JOBS
    # ======================================================================

    async def _get_recently_completed_jobs(
        self,
        limit: int = 5,
    ) -> list[ProcessingJob]:
        """
        Return the most recently completed processing jobs.

        IMPORTANT
        ---------
        Recency is based on `completed_at`, not `created_at`.

        This means the result represents documents that were actually
        processed most recently, rather than jobs that were merely created
        most recently.
        """

        safe_limit = max(
            1,
            min(int(limit), 50),
        )

        statement = (
            select(ProcessingJob)
            .options(
                selectinload(
                    ProcessingJob.document_version
                ).selectinload(
                    DocumentVersion.document
                )
            )
            .where(
                ProcessingJob.status == "completed",
                ProcessingJob.completed_at.is_not(None),
            )
            .order_by(
                ProcessingJob.completed_at.desc(),
                ProcessingJob.created_at.desc(),
            )
            .limit(safe_limit)
        )

        result = await self.db.execute(
            statement
        )

        return list(
            result.scalars().unique().all()
        )

    # ======================================================================
    # GENERIC PROCESSING JOBS
    # ======================================================================

    async def _list_processing_jobs_with_documents(
        self,
        limit: int = 10,
    ) -> list[ProcessingJob]:
        """
        Return recent processing jobs with document relationships.

        Used for generic processing questions such as:

            - What processing jobs exist?
            - Show processing history.
            - What is the processing status?
            - Show recent processing jobs.
        """

        safe_limit = max(
            1,
            min(int(limit), 50),
        )

        statement = (
            select(ProcessingJob)
            .options(
                selectinload(
                    ProcessingJob.document_version
                ).selectinload(
                    DocumentVersion.document
                )
            )
            .order_by(
                ProcessingJob.created_at.desc(),
            )
            .limit(safe_limit)
        )

        result = await self.db.execute(
            statement
        )

        return list(
            result.scalars().unique().all()
        )

    # ======================================================================
    # QUERY INTENT
    # ======================================================================

    @staticmethod
    def _detect_processing_intent(
        query: str,
    ) -> str:
        """
        Detect operational processing intent deterministically.

        Examples
        --------
        "What are the 5 most recently processed documents?"
            -> recently_processed_documents

        "Show the latest processed files"
            -> recently_processed_documents

        "What processing jobs exist?"
            -> processing_jobs
        """

        normalized = re.sub(
            r"\s+",
            " ",
            str(query or "").strip().lower(),
        )

        # ------------------------------------------------------------------
        # Recency vocabulary.
        # ------------------------------------------------------------------

        recent_terms = (
            "recent",
            "recently",
            "latest",
            "newest",
            "most recent",
            "processed recently",
            "recently processed",
            "last processed",
            "latest processed",
        )

        # ------------------------------------------------------------------
        # Processing vocabulary.
        # ------------------------------------------------------------------

        processing_terms = (
            "processed",
            "processing",
            "completed",
            "processing job",
            "processing jobs",
            "processing status",
            "processing history",
            "completed processing",
            "processed documents",
            "processed files",
        )

        # ------------------------------------------------------------------
        # Document vocabulary.
        # ------------------------------------------------------------------

        document_terms = (
            "document",
            "documents",
            "file",
            "files",
            "filename",
            "file name",
            "document version",
            "document versions",
        )

        has_recent = any(
            term in normalized
            for term in recent_terms
        )

        has_processing = any(
            term in normalized
            for term in processing_terms
        )

        has_document = any(
            term in normalized
            for term in document_terms
        )

        if (
            has_recent
            and has_processing
            and has_document
        ):
            return "recently_processed_documents"

        return "processing_jobs"

    # ======================================================================
    # LIMIT EXTRACTION
    # ======================================================================

    @staticmethod
    def _extract_limit(
        query: str,
        default: int = 5,
        maximum: int = 50,
    ) -> int:
        """
        Extract a requested result count from the user's query.
        """

        normalized = str(
            query or ""
        ).lower()

        match = re.search(
            r"\b(\d+)\b",
            normalized,
        )

        if not match:
            return default

        try:
            value = int(
                match.group(1)
            )
        except (TypeError, ValueError):
            return default

        return max(
            1,
            min(
                value,
                maximum,
            ),
        )

    # ======================================================================
    # PROCESSING JOB SERIALIZATION
    # ======================================================================

    @staticmethod
    def _serialize_processing_job(
        job: ProcessingJob,
    ) -> dict[str, Any]:
        """
        Serialize a ProcessingJob and its related document data.
        """

        version = getattr(
            job,
            "document_version",
            None,
        )

        document = (
            getattr(
                version,
                "document",
                None,
            )
            if version is not None
            else None
        )

        return {
            "processing_job_id": str(
                job.id
            ),
            "document_version_id": (
                str(job.document_version_id)
                if job.document_version_id
                else None
            ),
            "status": job.status,
            "job_type": job.job_type,
            "progress": job.progress,
            "current_step": job.current_step,
            "created_at": (
                job.created_at.isoformat()
                if job.created_at
                else None
            ),
            "started_at": (
                job.started_at.isoformat()
                if job.started_at
                else None
            ),
            "completed_at": (
                job.completed_at.isoformat()
                if job.completed_at
                else None
            ),
            "processed_at": (
                job.completed_at.isoformat()
                if job.completed_at
                else None
            ),
            "document_version": (
                ContextService._serialize_document_version(
                    version
                )
                if version is not None
                else None
            ),
            "document": (
                ContextService._serialize_document(
                    document
                )
                if document is not None
                else None
            ),
        }

    # ======================================================================
    # DOCUMENT VERSION SERIALIZATION
    # ======================================================================

    @staticmethod
    def _serialize_document_version(
        version: DocumentVersion,
    ) -> dict[str, Any]:
        """
        Serialize a DocumentVersion into an LLM-safe dictionary.
        """

        return {
            "id": str(
                version.id
            ),
            "document_id": str(
                version.document_id
            ),
            "version_number": version.version_number,
            "original_filename": (
                version.original_filename
            ),
            "mime_type": version.mime_type,
            "file_size": version.file_size,
            "status": version.status,
            "page_count": version.page_count,
            "detected_language": (
                version.detected_language
            ),
            "created_at": (
                version.created_at.isoformat()
                if version.created_at
                else None
            ),
            "updated_at": (
                version.updated_at.isoformat()
                if version.updated_at
                else None
            ),
        }

    # ======================================================================
    # DOCUMENT SERIALIZATION
    # ======================================================================

    @staticmethod
    def _serialize_document(
        document: Document,
    ) -> dict[str, Any]:
        """
        Serialize a Document into an LLM-safe dictionary.
        """

        return {
            "id": str(
                document.id
            ),
            "name": document.name,
            "description": document.description,
            "document_type": document.document_type,
            "status": document.status,
            "current_version_id": (
                str(
                    document.current_version_id
                )
                if document.current_version_id
                else None
            ),
            "created_at": (
                document.created_at.isoformat()
                if document.created_at
                else None
            ),
            "updated_at": (
                document.updated_at.isoformat()
                if document.updated_at
                else None
            ),
        }

    # ======================================================================
    # UNIQUE DOCUMENTS
    # ======================================================================

    @staticmethod
    def _serialize_unique_documents(
        jobs: list[ProcessingJob],
    ) -> list[dict[str, Any]]:
        """
        Serialize unique documents from processing jobs.

        The first occurrence wins, preserving the ordering of the
        supplied jobs.

        For recently-completed queries, jobs are already ordered by
        ProcessingJob.completed_at DESC.
        """

        documents: list[dict[str, Any]] = []

        seen: set[str] = set()

        for job in jobs:

            version = getattr(
                job,
                "document_version",
                None,
            )

            if version is None:
                continue

            document = getattr(
                version,
                "document",
                None,
            )

            if document is None:
                continue

            document_id = str(
                document.id
            )

            if document_id in seen:
                continue

            seen.add(
                document_id
            )

            documents.append(
                {
                    "document_id": document_id,
                    "name": document.name,
                    "description": document.description,
                    "document_type": (
                        document.document_type
                    ),
                    "status": document.status,
                    "document_version_id": (
                        str(version.id)
                    ),
                    "version_number": (
                        version.version_number
                    ),
                    "original_filename": (
                        version.original_filename
                    ),
                    "mime_type": (
                        version.mime_type
                    ),
                    "file_size": (
                        version.file_size
                    ),
                    "page_count": (
                        version.page_count
                    ),
                    "processing_job_id": (
                        str(job.id)
                    ),
                    "processing_status": (
                        job.status
                    ),
                    "progress": job.progress,
                    "processed_at": (
                        job.completed_at.isoformat()
                        if job.completed_at
                        else None
                    ),
                    "created_at": (
                        document.created_at.isoformat()
                        if document.created_at
                        else None
                    ),
                    "updated_at": (
                        document.updated_at.isoformat()
                        if document.updated_at
                        else None
                    ),
                }
            )

        return documents

    # ======================================================================
    # ROUTE NORMALIZATION
    # ======================================================================

    @staticmethod
    def _normalize_route(
        route: Any,
    ) -> str:
        """
        Normalize QueryRouter output.

        Supports:

            - None
            - string routes
            - dictionaries/mappings
            - QueryRoute-like objects
            - objects exposing `.route`
            - Pydantic-like objects exposing `.model_dump()`
            - objects exposing `.to_dict()`
        """

        if route is None:
            return "general"

        # ------------------------------------------------------------------
        # Plain string.
        # ------------------------------------------------------------------

        if isinstance(
            route,
            str,
        ):
            normalized = route.strip()

            return normalized or "general"

        # ------------------------------------------------------------------
        # Mapping.
        # ------------------------------------------------------------------

        if isinstance(
            route,
            Mapping,
        ):
            value = route.get(
                "route"
            )

            normalized = str(
                value or "general"
            ).strip()

            return normalized or "general"

        # ------------------------------------------------------------------
        # Direct `.route` attribute.
        # ------------------------------------------------------------------

        value = getattr(
            route,
            "route",
            None,
        )

        if value is not None:
            normalized = str(
                value
            ).strip()

            if normalized:
                return normalized

        # ------------------------------------------------------------------
        # Pydantic-style model_dump().
        # ------------------------------------------------------------------

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
                    value = dumped.get(
                        "route"
                    )

                    normalized = str(
                        value or "general"
                    ).strip()

                    return normalized or "general"

            except Exception:
                pass

        # ------------------------------------------------------------------
        # Generic to_dict().
        # ------------------------------------------------------------------

        to_dict = getattr(
            route,
            "to_dict",
            None,
        )

        if callable(to_dict):
            try:
                converted = to_dict()

                if isinstance(
                    converted,
                    Mapping,
                ):
                    value = converted.get(
                        "route"
                    )

                    normalized = str(
                        value or "general"
                    ).strip()

                    return normalized or "general"

            except Exception:
                pass

        return "general"