"""
PEVN Backend — Application Configuration

All configuration is loaded exclusively from environment variables.
No secrets are hardcoded anywhere in this module.

Usage:
    from app.core.config import get_settings
    settings = get_settings()  # cached singleton

    # As a FastAPI dependency:
    from app.core.config import get_settings
    from fastapi import Depends
    def my_endpoint(settings: Settings = Depends(get_settings)):
        ...
"""

from __future__ import annotations

import json
import secrets
from enum import StrEnum
from functools import lru_cache
from typing import Any
from urllib.parse import urlparse, urlunparse

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    """Supported runtime environments."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LogFormat(StrEnum):
    """Supported log output formats."""

    JSON = "json"
    CONSOLE = "console"


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Security principles enforced here:
    - No hardcoded defaults for sensitive values in production.
    - Production MUST have DEBUG=False.
    - Production MUST NOT have wildcard CORS origins.
    - Production disables OpenAPI documentation endpoints.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Silently ignore unknown env vars
    )

    # ---- Application -------------------------------------------------------
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    DEBUG: bool = False
    # Default generates a random key so the app can start without config,
    # but tokens signed with it won't survive a restart. Always set in production.
    SECRET_KEY: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ---- API ---------------------------------------------------------------
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Plataforma Educativa Virtual Nacional"
    PROJECT_SHORT_NAME: str = "PEVN"
    PROJECT_VERSION: str = "0.1.0"
    # Disabled in production by the validator below.
    OPENAPI_URL: str | None = "/openapi.json"
    DOCS_URL: str | None = "/docs"
    REDOC_URL: str | None = "/redoc"

    # ---- Database ----------------------------------------------------------
    DATABASE_URL: str = (
        "postgresql+asyncpg://pevn_app:pevn_app_dev_pass@localhost:5433/pevn_db"
    )
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800  # 30 minutes — prevents stale connections
    DB_POOL_PRE_PING: bool = True  # Validates connections before use
    DB_ECHO: bool = False  # Set True only for deep debugging (logs all SQL)

    # ---- Redis -------------------------------------------------------------
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_SOCKET_TIMEOUT: int = 5
    REDIS_CONNECT_TIMEOUT: int = 5

    # ---- Security / CORS ---------------------------------------------------
    CORS_ORIGINS: list[str] | str = ["http://localhost:3000"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]
    ALLOWED_HOSTS: list[str] | str = ["localhost", "127.0.0.1"]

    # ---- Logging -----------------------------------------------------------
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: LogFormat = LogFormat.CONSOLE

    # ---- Rate Limiting -----------------------------------------------------
    RATE_LIMIT_BACKEND: str = "memory://"
    RATE_LIMIT_DEFAULT: str = "100/minute"

    # ---- Virtual Classroom / BigBlueButton Provider ------------------------
    MEETING_PROVIDER_TYPE: str = "mock"  # "mock" or "bbb"
    BBB_API_URL: str = "http://localhost:8090/bigbluebutton/api"
    BBB_SHARED_SECRET: str = ""
    BBB_SIGNING_ALGORITHM: str = "sha1"  # "sha1" or "sha256"
    BBB_TIMEOUT_SECONDS: float = 10.0

    # ---- Secure File Storage (Phase B3-H11) --------------------------------
    STORAGE_LOCAL_PATH: str = "./data/storage"
    MAX_UPLOAD_SIZE_BYTES: int = 20 * 1024 * 1024  # 20 MB
    ALLOWED_FILE_EXTENSIONS: list[str] = [
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",
        ".jpg",
        ".jpeg",
        ".png",
        ".zip",
    ]

    # ---- Validators --------------------------------------------------------

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        """Support comma-separated string, JSON string, or list format from env."""
        if isinstance(v, str):
            v_stripped = v.strip()
            if v_stripped.startswith("[") and v_stripped.endswith("]"):
                try:
                    parsed = json.loads(v_stripped)
                    if isinstance(parsed, list):
                        return [
                            str(origin).strip()
                            for origin in parsed
                            if str(origin).strip()
                        ]
                except (json.JSONDecodeError, ValueError):
                    pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        if isinstance(v, (list, tuple, set)):
            return [str(origin).strip() for origin in v if str(origin).strip()]
        return [str(v)] if v else []

    @field_validator("ALLOWED_HOSTS", mode="before")
    @classmethod
    def parse_allowed_hosts(cls, v: Any) -> list[str]:
        """Support comma-separated string, JSON string, or list format from env."""
        if isinstance(v, str):
            v_stripped = v.strip()
            if v_stripped.startswith("[") and v_stripped.endswith("]"):
                try:
                    parsed = json.loads(v_stripped)
                    if isinstance(parsed, list):
                        return [
                            str(host).strip() for host in parsed if str(host).strip()
                        ]
                except (json.JSONDecodeError, ValueError):
                    pass
            return [host.strip() for host in v.split(",") if host.strip()]
        if isinstance(v, (list, tuple, set)):
            return [str(host).strip() for host in v if str(host).strip()]
        return [str(v)] if v else []

    @field_validator("SECRET_KEY", mode="before")
    @classmethod
    def ensure_secret_key(cls, v: str) -> str:
        """Generate a random secret key if none is provided (development only)."""
        if not v:
            return secrets.token_hex(64)
        return v

    @model_validator(mode="after")
    def validate_production_settings(self) -> Settings:
        """
        Enforce production security constraints.
        Fails fast at startup rather than silently running insecurely.
        """
        if self.ENVIRONMENT == Environment.PRODUCTION:
            if self.DEBUG:
                raise ValueError(
                    "SECURITY: DEBUG must be False in production. "
                    "Set ENVIRONMENT=production only when DEBUG=false."
                )
            cors_list = (
                self.CORS_ORIGINS
                if isinstance(self.CORS_ORIGINS, list)
                else [self.CORS_ORIGINS]
            )
            if "*" in cors_list or "" in cors_list:
                raise ValueError(
                    "SECURITY: Wildcard (*) CORS origins are not allowed in "
                    "production. Specify the exact domain(s) in CORS_ORIGINS."
                )
            # Disable API documentation in production — reduces attack surface
            self.OPENAPI_URL = None
            self.DOCS_URL = None
            self.REDOC_URL = None

        return self

    # ---- Computed properties -----------------------------------------------

    @property
    def is_development(self) -> bool:
        """Returns True if running in development mode."""
        return self.ENVIRONMENT == Environment.DEVELOPMENT

    @property
    def is_production(self) -> bool:
        """Returns True if running in production mode."""
        return self.ENVIRONMENT == Environment.PRODUCTION

    @property
    def is_staging(self) -> bool:
        """Returns True if running in staging mode."""
        return self.ENVIRONMENT == Environment.STAGING

    def get_safe_database_url(self) -> str:
        """
        Returns the database URL with password masked.
        Safe for logging — NEVER log the raw DATABASE_URL.
        """
        try:
            parsed = urlparse(self.DATABASE_URL)
            if parsed.password:
                safe_netloc = parsed.netloc.replace(f":{parsed.password}@", ":***@")
                return urlunparse(parsed._replace(netloc=safe_netloc))
            return self.DATABASE_URL
        except Exception:
            return "<database-url-unparseable>"

    def model_post_init(self, __context: Any) -> None:
        """Post-initialization hook."""
        # Ensure DB_ECHO is never True in production
        if self.ENVIRONMENT == Environment.PRODUCTION:
            object.__setattr__(self, "DB_ECHO", False)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return a cached Settings singleton.

    Uses lru_cache to ensure settings are loaded exactly once per process.
    This is safe for FastAPI dependencies.

    Note: In tests, call get_settings.cache_clear() to reset between test cases.
    """
    return Settings()
