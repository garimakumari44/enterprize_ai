"""
app/main.py

Main FastAPI application.

Responsibilities
----------------
- Create the FastAPI application.
- Load application environment configuration.
- Initialize application-wide runtime dependencies.
- Initialize the document-processing StageRegistry.
- Initialize application-scoped conversational infrastructure.
- Expose shared infrastructure through app.state.
- Configure middleware.
- Register API routers.
- Manage application startup and shutdown.

Assistant dependency scopes
----------------------------
Application-scoped:
    PromptBuilder
    LLMManager
    QueryRouter

Request-scoped:
    AsyncSession
    AssistantRepository
    ConversationManager
    ContextService
    AssistantOrchestrator
    AssistantService
"""

from __future__ import annotations

# ============================================================================
# ENVIRONMENT
# ============================================================================

from dotenv import load_dotenv

# IMPORTANT:
# Load backend/.env before importing/initializing application infrastructure
# that reads environment variables.
load_dotenv()


# ============================================================================
# STANDARD LIBRARY
# ============================================================================

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator


# ============================================================================
# FASTAPI
# ============================================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


# ============================================================================
# API ROUTER
# ============================================================================

from app.api.v1.router import router as api_v1_router


# ============================================================================
# PROCESSING
# ============================================================================















# ============================================================================
# ASSISTANT APPLICATION-SCOPED INFRASTRUCTURE
# ============================================================================

from app.assistant.prompt_builder import (
    PromptBuilder,
)

from app.assistant.query_router import (
    QueryRouter,
)

from app.services.llm_manager import (
    LLMManager,
)


# ============================================================================
# LOGGING
# ============================================================================

logger = logging.getLogger(__name__)


# ============================================================================
# APPLICATION CONSTANTS
# ============================================================================

APP_TITLE = (
    "Enterprise AI Workflow Orchestration Platform"
)

APP_VERSION = "2.0.0"

API_PREFIX = "/api/v1"


# ============================================================================
# EMBEDDING CONFIGURATION
# ============================================================================


# ============================================================================
# INDEX PROVIDER
# ============================================================================


# ============================================================================
# STAGE REGISTRY
# ============================================================================


# ============================================================================
# ASSISTANT APPLICATION INFRASTRUCTURE
# ============================================================================


def create_assistant_infrastructure() -> tuple[
    PromptBuilder,
    LLMManager,
    QueryRouter,
]:
    """
    Create application-scoped Assistant infrastructure.

    Application-scoped:
        PromptBuilder
        LLMManager
        QueryRouter

    Request-scoped objects are created by:

        app.api.v1.assistant.dependencies.get_assistant_service

    ContextService is intentionally NOT created here because it requires
    the request-scoped AsyncSession.
    """

    # ------------------------------------------------------------------------
    # Prompt builder
    # ------------------------------------------------------------------------

    prompt_builder = PromptBuilder()

    # ------------------------------------------------------------------------
    # Canonical LLM manager
    # ------------------------------------------------------------------------

    llm_manager = LLMManager(
        prompt_builder=prompt_builder,
    )

    # ------------------------------------------------------------------------
    # Query router
    # ------------------------------------------------------------------------

    query_router = QueryRouter()

    # ------------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------------

    logger.info(
        "Assistant PromptBuilder initialized."
    )

    logger.info(
        "Assistant LLM provider: %s",
        llm_manager.provider_name,
    )

    logger.info(
        "Assistant default model: %s",
        llm_manager.default_model,
    )

    # IMPORTANT:
    # This confirms that LLMManager actually registered its provider.
    # Never log the API key itself.
    logger.info(
        "Assistant configured providers: %s",
        list(llm_manager.providers.keys()),
    )

    logger.info(
        "Assistant QueryRouter initialized."
    )

    return (
        prompt_builder,
        llm_manager,
        query_router,
    )


# ============================================================================
# APPLICATION LIFESPAN
# ============================================================================


@asynccontextmanager
async def lifespan(
    app: FastAPI,
) -> AsyncIterator[None]:
    """
    Application startup/shutdown lifecycle.
    """

    logger.info(
        "Starting %s v%s",
        APP_TITLE,
        APP_VERSION,
    )

    assistant_llm_manager: LLMManager | None = None

    try:
        # ====================================================================
        # STARTUP
        # ====================================================================

        # --------------------------------------------------------------------
        # Assistant application-scoped infrastructure
        # --------------------------------------------------------------------

        (
            assistant_prompt_builder,
            assistant_llm_manager,
            assistant_query_router,
        ) = create_assistant_infrastructure()

        # --------------------------------------------------------------------
        # Store PromptBuilder in application state
        # --------------------------------------------------------------------

        app.state.assistant_prompt_builder = (
            assistant_prompt_builder
        )

        # --------------------------------------------------------------------
        # Store LLMManager in application state
        # --------------------------------------------------------------------

        app.state.assistant_llm_manager = (
            assistant_llm_manager
        )

        # --------------------------------------------------------------------
        # Store QueryRouter in application state
        # --------------------------------------------------------------------

        app.state.assistant_query_router = (
            assistant_query_router
        )

        logger.info(
            "Application Assistant infrastructure registered."
        )

        logger.info(
            "Assistant PromptBuilder is ready."
        )

        logger.info(
            "Assistant LLMManager is ready."
        )

        logger.info(
            "Assistant QueryRouter is ready."
        )

        logger.info(
            "Assistant ContextService will be created "
            "request-scoped with the request AsyncSession."
        )

        logger.info(
            "Assistant request-scoped dependency wiring is ready."
        )

        # --------------------------------------------------------------------
        # Application ready
        # --------------------------------------------------------------------

        logger.info(
            "%s startup complete.",
            APP_TITLE,
        )

        yield

    except Exception:
        logger.exception(
            "Application startup failed."
        )
        raise

    finally:
        # ====================================================================
        # SHUTDOWN
        # ====================================================================

        logger.info(
            "Shutting down %s...",
            APP_TITLE,
        )

        # --------------------------------------------------------------------
        # Close LLM manager
        # --------------------------------------------------------------------

        if assistant_llm_manager is not None:
            try:
                await assistant_llm_manager.close()

                logger.info(
                    "Assistant LLM manager closed."
                )

            except Exception:
                logger.exception(
                    "Failed to close Assistant LLM manager."
                )

        # --------------------------------------------------------------------
        # Remove Assistant application state
        # --------------------------------------------------------------------

        if hasattr(
            app.state,
            "assistant_prompt_builder",
        ):
            del app.state.assistant_prompt_builder

        if hasattr(
            app.state,
            "assistant_llm_manager",
        ):
            del app.state.assistant_llm_manager

        if hasattr(
            app.state,
            "assistant_query_router",
        ):
            del app.state.assistant_query_router

        logger.info(
            "Application shutdown complete."
        )


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================


app = FastAPI(
    title=APP_TITLE,
    description="""
Enterprise-grade AI Workflow Orchestration Platform.

Core Features
-------------
- Authentication & Authorization
- User Management
- Document Management
- Document Processing
- OCR & Document Intelligence
- Workflow Builder
- Workflow Nodes
- Workflow Versioning
- Workflow Validation
- Document Processing Pipeline
- Processing Stage Registry
- Vector Search
- AI Assistant
- Conversational Sessions
- LLM Orchestration

Processing Architecture
-----------------------

1. Classification
2. Layout Analysis
3. Text Extraction
4. OCR
5. Structure Detection
6. Cleaning / Normalization
7. Chunking
8. Metadata Enrichment
9. Embeddings
10. Indexing

Assistant Architecture
----------------------

Application Startup
        |
        +--> PromptBuilder
        |
        +--> LLMManager
        |
        +--> QueryRouter
                 |
                 v
             app.state

Request
   |
   +--> AsyncSession
   |
   +--> AssistantRepository
   |
   +--> ConversationManager
   |
   +--> ContextService(db)
   |
   v
AssistantOrchestrator
   |
   v
AssistantService

ContextService uses the request-scoped database session to retrieve
application context such as documents, document versions, and processing
jobs before the final assistant prompt is generated.

Embedding Configuration
-----------------------

Provider:
    local

Model:
    BAAI/bge-small-en-v1.5

Device:
    CPU

Batch size:
    32

Vector Index
------------

Provider:
    PostgreSQL + pgvector

Canonical Chunk Table:
    document_chunks

Vector Collection:
    document_chunk_vectors
""",
    version=APP_VERSION,
    lifespan=lifespan,
)


# ============================================================================
# CORS
# ============================================================================


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# API V1
# ============================================================================


app.include_router(
    api_v1_router,
    prefix=API_PREFIX,
)


# ============================================================================
# ROOT ENDPOINT
# ============================================================================


@app.get(
    "/",
    tags=["Root"],
)
async def root() -> dict[str, str]:
    """
    Root application endpoint.
    """

    return {
        "name": APP_TITLE,
        "version": APP_VERSION,
        "status": "ok",
    }


# ============================================================================
# HEALTH
# ============================================================================


@app.get(
    "/health",
    tags=["Health"],
)
async def health() -> dict[str, str]:
    """
    Basic application health endpoint.
    """

    return {
        "status": "healthy",
    }