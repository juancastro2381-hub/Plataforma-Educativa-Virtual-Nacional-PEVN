"""
Tests for GET /api/v1/health

Verifies:
  - Endpoint returns 200
  - Response has correct structure
  - No sensitive information is exposed
  - Security headers are present
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_returns_200(client: AsyncClient) -> None:
    """Health endpoint must return HTTP 200."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_response_has_status_ok(client: AsyncClient) -> None:
    """Health response must include status: ok."""
    response = await client.get("/api/v1/health")
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_health_response_has_service_name(client: AsyncClient) -> None:
    """Health response must include the service name."""
    response = await client.get("/api/v1/health")
    data = response.json()
    assert "service" in data
    assert data["service"] == "pevn-backend"


@pytest.mark.asyncio
async def test_health_does_not_expose_secrets(client: AsyncClient) -> None:
    """
    Health response must not expose any sensitive information.
    SECURITY: Verify no leakage of credentials or internal config.
    """
    response = await client.get("/api/v1/health")
    body = response.text.lower()

    sensitive_keywords = [
        "password",
        "secret",
        "token",
        "apikey",
        "api_key",
        "database_url",
        "postgresql",
        "redis://",
    ]

    for keyword in sensitive_keywords:
        assert (
            keyword not in body
        ), f"Security violation: '{keyword}' found in /health response"


@pytest.mark.asyncio
async def test_health_response_is_json(client: AsyncClient) -> None:
    """Health response Content-Type must be application/json."""
    response = await client.get("/api/v1/health")
    assert "application/json" in response.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_health_has_security_headers(client: AsyncClient) -> None:
    """
    Security headers must be present on all responses.
    These are applied by SecurityHeadersMiddleware.
    """
    response = await client.get("/api/v1/health")

    assert (
        response.headers.get("x-content-type-options") == "nosniff"
    ), "X-Content-Type-Options header missing"
    assert (
        response.headers.get("x-frame-options") == "DENY"
    ), "X-Frame-Options header missing"
    assert "referrer-policy" in response.headers, "Referrer-Policy header missing"
    assert "permissions-policy" in response.headers, "Permissions-Policy header missing"


@pytest.mark.asyncio
async def test_health_has_correlation_id_header(client: AsyncClient) -> None:
    """Every response must include a correlation ID header."""
    response = await client.get("/api/v1/health")
    assert (
        "x-correlation-id" in response.headers
    ), "X-Correlation-ID header missing from response"


@pytest.mark.asyncio
async def test_health_accepts_correlation_id_from_client(client: AsyncClient) -> None:
    """If client provides X-Correlation-ID, it must be echoed in the response."""
    client_id = "test-correlation-id-12345"
    response = await client.get(
        "/api/v1/health",
        headers={"X-Correlation-ID": client_id},
    )
    assert response.headers.get("x-correlation-id") == client_id
