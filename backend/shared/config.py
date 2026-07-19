"""Application configuration using Pydantic Settings."""
from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://ielts:ielts_secret@localhost:5432/ieltsdb",
        alias="DATABASE_URL",
    )
    database_url_sync: str = Field(
        default="postgresql+psycopg2://ielts:ielts_secret@localhost:5432/ieltsdb",
        alias="DATABASE_URL_SYNC",
    )

    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        alias="REDIS_URL",
    )

    # Qdrant
    qdrant_url: str = Field(
        default="http://localhost:6333",
        alias="QDRANT_URL",
    )

    # LLM (LM Studio / OpenAI compatible) — kept as fallback
    llm_base_url: str = Field(
        default="http://localhost:1234/v1",
        alias="LLM_BASE_URL",
    )
    llm_model: str = Field(
        default="MiniMax-M2.5",
        alias="LLM_MODEL",
    )
    llm_api_key: str = Field(
        default="lm-studio",
        alias="LLM_API_KEY",
    )
    llm_temperature: float = Field(default=0.7)
    llm_max_tokens: int = Field(default=2048)

    # OpenRouter (cloud — multi-model router)
    openrouter_api_key: str = Field(
        default="",
        alias="OPENROUTER_API_KEY",
    )
    openrouter_model: str = Field(
        default="google/gemma-3-27b-it",
        alias="OPENROUTER_MODEL",
    )
    openrouter_max_tokens: int = Field(
        default=4096,
        alias="OPENROUTER_MAX_TOKENS",
    )

    # Gemma 4 via Google AI SDK
    gemini_api_key: str = Field(
        default="",
        alias="GEMINI_API_KEY",
    )
    gemma_model: str = Field(
        default="gemma-4-27b-it",
        alias="GEMMA_MODEL",
    )

    # LM Studio (local inference)
    lmstudio_model: str = Field(
        default="local-model",
        alias="LMSTUDIO_MODEL",
    )
    lmstudio_max_tokens: int = Field(
        default=4096,
        alias="LMSTUDIO_MAX_TOKENS",
    )

    # Service ports
    profile_service_port: int = Field(default=8001, alias="PROFILE_SERVICE_PORT")
    reading_service_port: int = Field(default=8002, alias="READING_SERVICE_PORT")
    listening_service_port: int = Field(default=8003, alias="LISTENING_SERVICE_PORT")
    writing_service_port: int = Field(default=8004, alias="WRITING_SERVICE_PORT")
    vocabulary_service_port: int = Field(default=8005, alias="VOCABULARY_SERVICE_PORT")
    grammar_service_port: int = Field(default=8006, alias="GRAMMAR_SERVICE_PORT")
    import_service_port: int = Field(default=8007, alias="IMPORT_SERVICE_PORT")
    analytics_service_port: int = Field(default=8008, alias="ANALYTICS_SERVICE_PORT")
    ai_agent_service_port: int = Field(default=8009, alias="AI_AGENT_SERVICE_PORT")

    # Gateway
    gateway_host: str = Field(default="0.0.0.0", alias="GATEWAY_HOST")
    gateway_port: int = Field(default=8000, alias="GATEWAY_PORT")

    # CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
    )

    # Import service storage
    import_storage_path: str = "/app/imports"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()