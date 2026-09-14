"""
AI Settings Configuration

Central configuration for:
- LLM providers
- Model defaults
- Embedding configuration
- AI runtime behavior
- Token limits
- Retry policies
"""

from functools import lru_cache
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AISettings(BaseSettings):
    """
    AI platform configuration.

    Loaded from environment variables:
    
    Example:
        AI_DEFAULT_PROVIDER=openai
        AI_DEFAULT_MODEL=gpt-4.1
        AI_TEMPERATURE=0.2
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


    # ==========================
    # Default AI Provider
    # ==========================

    AI_DEFAULT_PROVIDER: str = Field(
        default="openai",
        description="Default LLM provider"
    )


    # ==========================
    # Default Models
    # ==========================

    AI_DEFAULT_MODEL: str = Field(
        default="gpt-4.1",
        description="Default chat completion model"
    )


    AI_DEFAULT_EMBEDDING_MODEL: str = Field(
        default="text-embedding-3-small",
        description="Default embedding model"
    )


    AI_DEFAULT_VISION_MODEL: str = Field(
        default="gpt-4.1-mini",
        description="Default vision model"
    )


    AI_DEFAULT_OCR_MODEL: str = Field(
        default="tesseract",
        description="Default OCR engine"
    )


    # ==========================
    # Generation Parameters
    # ==========================

    AI_TEMPERATURE: float = Field(
        default=0.2,
        ge=0,
        le=2
    )


    AI_MAX_TOKENS: int = Field(
        default=4096,
        gt=0
    )


    AI_TOP_P: float = Field(
        default=1.0,
        ge=0,
        le=1
    )


    AI_FREQUENCY_PENALTY: float = Field(
        default=0.0,
        ge=0,
        le=2
    )


    AI_PRESENCE_PENALTY: float = Field(
        default=0.0,
        ge=0,
        le=2
    )


    # ==========================
    # Execution Runtime
    # ==========================

    AI_TIMEOUT_SECONDS: int = Field(
        default=120,
        gt=0
    )


    AI_MAX_RETRIES: int = Field(
        default=3,
        ge=0
    )


    AI_RETRY_DELAY_SECONDS: int = Field(
        default=5,
        ge=0
    )


    # ==========================
    # Context Window
    # ==========================

    AI_CONTEXT_WINDOW: int = Field(
        default=128000,
        description="Maximum model context size"
    )


    AI_MAX_CONVERSATION_MESSAGES: int = Field(
        default=50
    )


    # ==========================
    # Streaming
    # ==========================

    AI_ENABLE_STREAMING: bool = Field(
        default=True
    )


    # ==========================
    # Embedding / Vector Search
    # ==========================

    AI_EMBEDDING_DIMENSION: int = Field(
        default=1536
    )


    AI_CHUNK_SIZE: int = Field(
        default=800
    )


    AI_CHUNK_OVERLAP: int = Field(
        default=150
    )


    # ==========================
    # Supported Providers
    # ==========================

    AI_SUPPORTED_PROVIDERS: List[str] = Field(
        default=[
            "openai",
            "anthropic",
            "google",
            "azure_openai",
            "ollama"
        ]
    )


    # ==========================
    # Feature Flags
    # ==========================

    AI_ENABLE_MEMORY: bool = Field(
        default=True
    )


    AI_ENABLE_RAG: bool = Field(
        default=True
    )


    AI_ENABLE_TOOLS: bool = Field(
        default=True
    )


    AI_ENABLE_FUNCTION_CALLING: bool = Field(
        default=True
    )


    AI_ENABLE_AGENT_MODE: bool = Field(
        default=True
    )


    # ==========================
    # Logging
    # ==========================

    AI_LOG_PROMPTS: bool = Field(
        default=False,
        description="Store prompts for debugging"
    )


    AI_LOG_RESPONSES: bool = Field(
        default=False
    )


    # ==========================
    # Cost Control
    # ==========================

    AI_MONTHLY_TOKEN_LIMIT: int = Field(
        default=10000000
    )


    AI_ENABLE_COST_TRACKING: bool = Field(
        default=True
    )



@lru_cache()
def get_ai_settings() -> AISettings:
    """
    Singleton AI settings loader.

    Usage:

        settings = get_ai_settings()

        print(
            settings.AI_DEFAULT_MODEL
        )
    """

    return AISettings()



ai_settings = get_ai_settings()