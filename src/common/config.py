"""Configuration module for Tegmen."""

import os
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""

    # OpenRouter Configuration
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    DEFAULT_MODEL: str = os.getenv(
        "DEFAULT_MODEL", "openrouter/google/gemini-2.0-flash-001"
    )
    LLM_DEFAULT_MODEL: str = os.getenv(
        "LLM_DEFAULT_MODEL", DEFAULT_MODEL
    )

    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")


    # Database Configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql+asyncpg://tegmen:tegmen@localhost:5432/tegmen"
    )

    # Semantic Router Configuration
    EMBEDDING_MODEL: str = os.getenv(
        "EMBEDDING_MODEL", "intfloat/multilingual-e5-small" #"sentence-transformers/all-MiniLM-L6-v2"
    )

    # Security Configuration
    JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-secret-keep-it-safe")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")

    # OpenTelemetry Configuration
    OTEL_ENABLED: bool = os.getenv("OTEL_ENABLED", "true").lower() == "true"
    OTEL_EXPORTER_OTLP_ENDPOINT: str = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")

    # Application Configuration
    APP_NAME: str = "tegmen"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # Agent URLs (A2A Communication)
    MAESTRO_URL: str = os.getenv("MAESTRO_URL", "http://localhost:8000")
    DEFAULT_A2A_TIMEOUT: float = float(os.getenv("DEFAULT_A2A_TIMEOUT", "30.0"))


    # Gourmet Resilience Configuration
    GOURMET_PERSISTENCE_TIMEOUT_MS: int = int(os.getenv("GOURMET_PERSISTENCE_TIMEOUT_MS", "3000"))
    GOURMET_ARTIFICIAL_DELAY_MS: int = int(os.getenv("GOURMET_ARTIFICIAL_DELAY_MS", "0"))

    # Conflict Resolution Configuration
    CONFLICT_SIMILARITY_THRESHOLD: float = float(os.getenv("CONFLICT_SIMILARITY_THRESHOLD", "0.92"))


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


config = get_settings()
