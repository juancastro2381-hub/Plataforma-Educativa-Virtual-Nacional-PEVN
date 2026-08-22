"""
Tests for application configuration.

Verifies:
  - Settings load correctly from environment variables
  - Production environment enforces security constraints
  - Sensitive values are not exposed in safe accessors
  - Configuration validation catches unsafe combinations
"""

from __future__ import annotations

import pytest

from app.core.config import Environment, Settings, get_settings


class TestDefaultSettings:
    """Tests for default/development configuration."""

    def test_default_environment_is_development(self) -> None:
        """Default environment must be development (safe default)."""
        settings = Settings(_env_file=None)  # type: ignore[call-arg]
        assert settings.ENVIRONMENT == Environment.DEVELOPMENT

    def test_debug_defaults_to_false(self) -> None:
        """DEBUG should default to False — safe default."""
        settings = Settings(_env_file=None)  # type: ignore[call-arg]
        assert settings.DEBUG is False

    def test_secret_key_is_generated_if_empty(self) -> None:
        """A secret key must always be available (auto-generated if not set)."""
        settings = Settings(_env_file=None, SECRET_KEY="")  # type: ignore[call-arg]
        assert settings.SECRET_KEY
        assert len(settings.SECRET_KEY) > 32

    def test_api_v1_prefix(self) -> None:
        """API prefix must be /api/v1 by default."""
        settings = Settings(_env_file=None)  # type: ignore[call-arg]
        assert settings.API_V1_PREFIX == "/api/v1"

    def test_cors_origins_parsing_from_string(self) -> None:
        """CORS origins must be parseable from a comma-separated string."""
        settings = Settings(  # type: ignore[call-arg]
            _env_file=None,
            CORS_ORIGINS="http://localhost:3000,http://localhost:3001",
        )
        assert len(settings.CORS_ORIGINS) == 2
        assert "http://localhost:3000" in settings.CORS_ORIGINS
        assert "http://localhost:3001" in settings.CORS_ORIGINS

    def test_allowed_hosts_parsing_from_string(self) -> None:
        """ALLOWED_HOSTS must be parseable from a comma-separated string."""
        settings = Settings(  # type: ignore[call-arg]
            _env_file=None,
            ALLOWED_HOSTS="localhost,127.0.0.1",
        )
        assert "localhost" in settings.ALLOWED_HOSTS
        assert "127.0.0.1" in settings.ALLOWED_HOSTS


class TestProductionConstraints:
    """Tests that production mode enforces security constraints."""

    def test_production_rejects_debug_true(self) -> None:
        """DEBUG=True is not allowed in production."""
        with pytest.raises(ValueError, match="DEBUG must be False"):
            Settings(  # type: ignore[call-arg]
                _env_file=None,
                ENVIRONMENT="production",
                DEBUG=True,
                CORS_ORIGINS=["https://example.gov.co"],
                SECRET_KEY="a" * 128,
            )

    def test_production_rejects_wildcard_cors(self) -> None:
        """Wildcard CORS origin is not allowed in production."""
        with pytest.raises(ValueError, match="Wildcard"):
            Settings(  # type: ignore[call-arg]
                _env_file=None,
                ENVIRONMENT="production",
                DEBUG=False,
                CORS_ORIGINS=["*"],
                SECRET_KEY="a" * 128,
            )

    def test_production_disables_openapi_docs(self) -> None:
        """OpenAPI documentation endpoints must be disabled in production."""
        settings = Settings(  # type: ignore[call-arg]
            _env_file=None,
            ENVIRONMENT="production",
            DEBUG=False,
            CORS_ORIGINS=["https://example.gov.co"],
            SECRET_KEY="a" * 128,
        )
        assert settings.OPENAPI_URL is None
        assert settings.DOCS_URL is None
        assert settings.REDOC_URL is None

    def test_production_disables_db_echo(self) -> None:
        """DB SQL echo must be disabled in production."""
        settings = Settings(  # type: ignore[call-arg]
            _env_file=None,
            ENVIRONMENT="production",
            DEBUG=False,
            CORS_ORIGINS=["https://example.gov.co"],
            SECRET_KEY="a" * 128,
            DB_ECHO=True,  # Attempted override
        )
        assert settings.DB_ECHO is False


class TestSafeDatabaseUrl:
    """Tests for the safe database URL masker."""

    def test_password_is_masked_in_safe_url(self) -> None:
        """get_safe_database_url() must mask the database password."""
        settings = Settings(  # type: ignore[call-arg]
            _env_file=None,
            DATABASE_URL=(
                "postgresql+asyncpg://pevn_app:supersecret@localhost:5432/pevn_db"
            ),
        )
        safe_url = settings.get_safe_database_url()
        assert "supersecret" not in safe_url
        assert "***" in safe_url

    def test_username_is_preserved_in_safe_url(self) -> None:
        """The username should be visible in the safe URL (not sensitive)."""
        settings = Settings(  # type: ignore[call-arg]
            _env_file=None,
            DATABASE_URL=(
                "postgresql+asyncpg://pevn_app:supersecret@localhost:5432/pevn_db"
            ),
        )
        safe_url = settings.get_safe_database_url()
        assert "pevn_app" in safe_url


class TestSettingsCaching:
    """Tests for the settings singleton cache."""

    def test_get_settings_returns_same_instance(self) -> None:
        """get_settings() must return the same cached instance."""
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2

    def test_cache_can_be_cleared(self) -> None:
        """Cache can be cleared (needed in tests)."""
        get_settings.cache_clear()
        s1 = get_settings()
        get_settings.cache_clear()
        s2 = get_settings()
        # They are separate instances after cache clear
        assert s1 is not s2
