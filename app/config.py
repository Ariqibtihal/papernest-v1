from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    # DB
    database_url: str = "sqlite+aiosqlite:///./paperlens.db"

    # Polite identification
    contact_email: str = "you@example.com"
    user_agent: str = "PaperLens/0.1 (mailto:you@example.com)"

    # API keys (all optional)
    semantic_scholar_api_key: str | None = None
    core_api_key: str | None = None
    springer_api_key: str | None = None
    ieee_api_key: str | None = None
    elsevier_api_key: str | None = None
    ncbi_api_key: str | None = None

    # AI
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    google_api_key: str | None = None

    # Cache
    cache_ttl_seconds: int = Field(default=86400, ge=0)

    # JWT Authentication
    jwt_secret_key: str = Field(
        default="change-this-secret-key-in-production",
        min_length=32,
        description="JWT secret key (generate with: openssl rand -hex 32)"
    )
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    
    # CORS Configuration
    cors_origins: list[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000", "http://localhost:8000"],
        description="Allowed CORS origins"
    )
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        description="Allowed HTTP methods"
    )
    cors_allow_headers: list[str] = Field(
        default=["Content-Type", "Authorization", "Accept"],
        description="Allowed HTTP headers"
    )
    
    @field_validator('jwt_secret_key')
    @classmethod
    def validate_jwt_secret(cls, v: str, info) -> str:
        """Validate JWT secret key is secure."""
        if v == "change-this-secret-key-in-production":
            # Only raise error in production
            app_env = info.data.get('app_env', 'development')
            if app_env == "production":
                raise ValueError(
                    "JWT_SECRET_KEY must be changed from default value in production. "
                    "Generate with: openssl rand -hex 32"
                )
        if len(v) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters")
        return v
    
    @field_validator('database_url')
    @classmethod
    def validate_database_url(cls, v: str, info) -> str:
        """Validate database URL for production."""
        app_env = info.data.get('app_env', 'development')
        if app_env == "production" and v.startswith("sqlite"):
            raise ValueError(
                "SQLite is not recommended for production. "
                "Use PostgreSQL: postgresql+asyncpg://..."
            )
        return v
    
    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
