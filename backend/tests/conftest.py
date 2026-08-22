"""
PEVN Backend — Test Configuration

Provides fixtures and configuration for the test suite.

Test database:
  Tests use environment variables for database configuration.
  Set DATABASE_URL to a test database (not the development database).
  Tests that require a real database are marked @pytest.mark.integration.

Environment:
  The test environment is set to 'development' to enable detailed
  error responses and disable production-only restrictions.
"""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

# ---------------------------------------------------------------------------
# Set default test environment variables
# These are overridden by actual environment variables if present.
# ---------------------------------------------------------------------------
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("LOG_LEVEL", "WARNING")  # Reduce test noise
os.environ.setdefault("LOG_FORMAT", "console")
os.environ.setdefault(
    "SECRET_KEY",
    "test-secret-key-pevn-phase1-not-for-production-" + "0" * 80,
)
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://pevn_test:test_password@localhost:5432/pevn_test",
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")
os.environ.setdefault("ALLOWED_HOSTS", "localhost,127.0.0.1,testserver")

from app.core.config import get_settings
from app.main import create_application


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """Use asyncio as the anyio backend for async tests."""
    return "asyncio"


@pytest.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, None]:
    """
    Provide an async HTTP test client.

    Uses ASGI transport to call the FastAPI app directly without
    starting an actual HTTP server. Fast and isolated.

    Note: Each test function gets a fresh client to prevent state leakage.
    The settings cache is cleared between tests to allow configuration overrides.
    """
    # Clear the settings cache so test env vars take effect
    get_settings.cache_clear()

    test_app = create_application()

    async with AsyncClient(
        transport=ASGITransport(app=test_app),  # type: ignore[arg-type]
        base_url="http://testserver",
        headers={"Host": "localhost"},
    ) as test_client:
        yield test_client

    # Reset after each test
    get_settings.cache_clear()
