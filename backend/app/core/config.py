"""
app/core/config.py

Central application configuration.

Configuration is loaded from environment variables
and the local .env file.

Architecture:

    .env / Environment
            |
            v
        Settings
            |
            v
    Application Services
"""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ==========================================================
    # Application
    # ==========================================================

    APP_NAME: str = "AI Workflow Orchestration Platform"

    APP_VERSION: str = "0.1.0"

    ENVIRONMENT: str = "development"

    DEBUG: bool = True

    # ==========================================================
    # API
    # ==========================================================

    API_V1_PREFIX: str = "/api/v1"

    BACKEND_URL: str = "http://localhost:8000"

    FRONTEND_URL: str = "http://localhost:3000"

    # ==========================================================
    # Security
    # ==========================================================

    SECRET_KEY: str

    ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ==========================================================
    # Database
    # ==========================================================

    DATABASE_URL: str

    DATABASE_ECHO: bool = False

    DATABASE_POOL_SIZE: int = 10

    DATABASE_MAX_OVERFLOW: int = 20

    # ==========================================================
    # CORS
    # ==========================================================

    BACKEND_CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
        ]
    )

    # ==========================================================
    # Redis
    # ==========================================================

    REDIS_HOST: str = "localhost"

    REDIS_PORT: int = 6379

    REDIS_DB: int = 0

    REDIS_PASSWORD: str | None = None

    # ==========================================================
    # Object Storage
    # ==========================================================

    STORAGE_BACKEND: str = "minio"

    STORAGE_BUCKET: str = "enterprise-ai"

    STORAGE_BASE_PATH: str = "./storage"

    # ==========================================================
    # MinIO / S3-Compatible Storage
    # ==========================================================

    MINIO_ENDPOINT: str = "http://localhost:9000"

    MINIO_ACCESS_KEY: str = "minioadmin"

    MINIO_SECRET_KEY: str = "minioadmin"

    MINIO_REGION: str = "us-east-1"

    MINIO_SECURE: bool = False

    # ==========================================================
    # Document Processing
    # ==========================================================

    MAX_FILE_SIZE_MB: int = 100

    # ==========================================================
    # Chunking
    # ==========================================================

    CHUNK_SIZE: int = 800

    CHUNK_OVERLAP: int = 120

    # ==========================================================
    # Embeddings
    # ==========================================================

    # Provider:
    #   local       -> local BGE-small model
    #   cohere      -> Cohere remote API
    #   huggingface -> Hugging Face remote inference
    #   auto        -> automatic provider selection
    EMBEDDING_PROVIDER: str = "local"

    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"

    EMBEDDING_DEVICE: str = "cpu"

    EMBEDDING_DIMENSION: int = 384

    EMBEDDING_BATCH_SIZE: int = 32

    # Hugging Face remote inference
    HUGGINGFACE_API_KEY: str | None = None

    # ==========================================================
    # LLM
    # ==========================================================

    LLM_PROVIDER: str = "openrouter"

    LLM_MODEL: str = "openrouter/free"

    # ----------------------------------------------------------
    # OpenRouter
    # ----------------------------------------------------------

    LLM_OPENROUTER_API_KEY: str | None = None

    LLM_OPENROUTER_MODEL: str = "openrouter/free"

    LLM_OPENROUTER_BASE_URL: str = (
        "https://openrouter.ai/api/v1" 
    ) 
 
    LLM_OPENROUTER_HTTP_REFERER: str | None = None 
 
    LLM_OPENROUTER_APP_NAME: str = ( 
        "AI Workflow Orchestration Platform" 
    ) 
 
    # ---------------------------------------------------------- 
    # Generation 
    # ---------------------------------------------------------- 
 
    LLM_TEMPERATURE: float = 0.2 
 
    LLM_MAX_TOKENS: int = 1024 
 
    LLM_TOP_P: float = 1.0 
 
    LLM_FREQUENCY_PENALTY: float = 0.0 
 
    LLM_PRESENCE_PENALTY: float = 0.0 
 
    # ---------------------------------------------------------- 
    # Runtime 
    # ---------------------------------------------------------- 
 
    LLM_TIMEOUT: float = 120.0 
 
    LLM_MAX_RETRIES: int = 3 
 
    LLM_STREAM: bool = True 
 
    LLM_VERIFY_SSL: bool = True 
 
    # ---------------------------------------------------------- 
    # Optional OpenAI 
    # ---------------------------------------------------------- 
 
    OPENAI_API_KEY: str | None = None 
 
    # ========================================================== 
    # OCR 
    # ========================================================== 
 
    OCR_PROVIDER: str = "tesseract" 
 
    # ========================================================== 
    # Retrieval 
    # ========================================================== 
 
    RETRIEVAL_TOP_K: int = 10 
 
    RETRIEVAL_SCORE_THRESHOLD: float = 0.0 
 
    # ========================================================== 
    # Logging 
    # ========================================================== 
 
    LOG_LEVEL: str = "INFO" 
 
    LOG_JSON: bool = False 
 
    # ========================================================== 
    # Validation 
    # ========================================================== 
 
    @field_validator("REDIS_PORT") 
    @classmethod 
    def validate_redis_port(cls, value: int) -> int: 
        if not 1 <= value <= 65535: 
            raise ValueError( 
                "REDIS_PORT must be between 1 and 65535." 
            ) 
 
        return value 
 
    @field_validator("MAX_FILE_SIZE_MB") 
    @classmethod 
    def validate_max_file_size(cls, value: int) -> int: 
        if value <= 0: 
            raise ValueError( 
                "MAX_FILE_SIZE_MB must be greater than 0." 
            ) 
 
        return value 
 
    @field_validator("CHUNK_SIZE") 
    @classmethod 
    def validate_chunk_size(cls, value: int) -> int: 
        if value <= 0: 
            raise ValueError( 
                "CHUNK_SIZE must be greater than 0." 
            ) 
 
        return value 
 
    @field_validator("CHUNK_OVERLAP") 
    @classmethod 
    def validate_chunk_overlap(cls, value: int) -> int: 
        if value < 0: 
            raise ValueError( 
                "CHUNK_OVERLAP cannot be negative." 
            ) 
 
        return value 
 
    @field_validator("CHUNK_OVERLAP") 
    @classmethod 
    def validate_chunk_overlap_less_than_chunk_size( 
        cls, 
        value: int, 
        info, 
    ) -> int: 
        chunk_size = info.data.get("CHUNK_SIZE") 
 
        if chunk_size is not None and value >= chunk_size: 
            raise ValueError( 
                "CHUNK_OVERLAP must be smaller than CHUNK_SIZE." 
            ) 
 
        return value 
 
    @field_validator("EMBEDDING_DIMENSION") 
    @classmethod 
    def validate_embedding_dimension( 
        cls, 
        value: int, 
    ) -> int: 
        if value <= 0: 
            raise ValueError( 
                "EMBEDDING_DIMENSION must be greater than 0." 
            ) 
 
        return value 
 
    @field_validator("RETRIEVAL_TOP_K") 
    @classmethod 
    def validate_retrieval_top_k( 
        cls, 
        value: int, 
    ) -> int: 
        if value <= 0: 
            raise ValueError( 
                "RETRIEVAL_TOP_K must be greater than 0." 
            ) 
 
        return value 
 
 
@lru_cache 
def get_settings() -> Settings: 
    """ 
    Returns cached application settings. 
 
    The Settings object is created once per process 
    and reused throughout the application. 
    """ 
 
    return Settings() 
 
 
settings = get_settings()  