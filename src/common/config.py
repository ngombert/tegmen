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

    # Database Configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql+asyncpg://tegmen:tegmen@localhost:5432/tegmen"
    )

    # Semantic Router Configuration
    EMBEDDING_MODEL: str = os.getenv(
        "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
    )

    # Application Configuration
    APP_NAME: str = "tegmen"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # Agent URLs (A2A Communication)
    MAESTRO_URL: str = os.getenv("MAESTRO_URL", "http://localhost:8000")
    GOURMET_URL: str = os.getenv("GOURMET_URL", "http://localhost:8000")
    ACADOMIE_URL: str = os.getenv("ACADOMIE_URL", "http://localhost:8000")
    EXPLORER_URL: str = os.getenv("EXPLORER_URL", "http://localhost:8000")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


config = get_settings()
