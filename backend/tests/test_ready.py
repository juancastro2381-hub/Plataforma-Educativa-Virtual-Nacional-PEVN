"""
Tests for GET /api/v1/ready

Verifies:
  - Endpoint returns a valid HTTP status code (200 or 503)
  - Response has the correct structure
  - No sensitive information is exposed
  - Response accurately represents dependency check results
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_ready_returns_valid_status_code(client: AsyncClient) -> None:
    """Readiness endpoint must return 200 (ready) or 503 (not ready)."""
    response = await client.get("/api/v1/ready")
    assert response.status_code in (
        200,
        503,
    ), f"Expected 200 or 503, got {response.status_code}"


@pytest.mark.asyncio
async def test_ready_response_structure(client: AsyncClient) -> None:
    """Readiness response must include 'status' and 'checks' fields."""
    response = await client.get("/api/v1/ready")
    data = response.json()

    assert "status" in data, "Response missing 'status' field"
    assert "checks" in data, "Response missing 'checks' field"
    assert isinstance(data["checks"], dict), "'checks' must be a dictionary"


@pytest.mark.asyncio
async def test_ready_status_matches_http_code(client: AsyncClient) -> None:
    """HTTP status code must be consistent with status in body."""
    response = await client.get("/api/v1/ready")
    data = response.json()

    if response.status_code == 200:
        assert data["status"] == "ready", "HTTP 200 must correspond to status: ready"
    elif response.status_code == 503:
        assert (
            data["status"] == "not_ready"
        ), "HTTP 503 must correspond to status: not_ready"


@pytest.mark.asyncio
async def test_ready_checks_contain_database(client: AsyncClient) -> None:
    """Readiness response must include a 'database' check."""
    response = await client.get("/api/v1/ready")
    data = response.json()
    checks = data.get("checks", {})

    assert "database" in checks, "Missing 'database' check in response"
    assert checks["database"] in (
        "ok",
        "error",
    ), f"Database check status must be 'ok' or 'error', got: {checks['database']!r}"


@pytest.mark.asyncio
async def test_ready_checks_contain_redis(client: AsyncClient) -> None:
    """Readiness response must include a 'redis' check."""
    response = await client.get("/api/v1/ready")
    data = response.json()
    checks = data.get("checks", {})

    assert "redis" in checks, "Missing 'redis' check in response"
    assert checks["redis"] in (
        "ok",
        "error",
    ), f"Redis check status must be 'ok' or 'error', got: {checks['redis']!r}"


@pytest.mark.asyncio
async def test_ready_does_not_expose_internal_details(client: AsyncClient) -> None:
    """
    Readiness response must not expose connection strings or credentials.
    SECURITY: Check values must only be 'ok' or 'error'.
    """
    response = await client.get("/api/v1/ready")
    body = response.text.lower()

    # Verify check values do not contain connection details
    sensitive_patterns = [
        "postgresql",
        "asyncpg",
        "password",
        "redis://",
        "localhost",
        "exception",
        "traceback",
        "error message",
    ]

    # The word 'error' is allowed as a check status value
    # but detailed error messages must not appear
    body_without_ok_error = (
        body.replace('"ok"', "")
        .replace('"error"', "")
        .replace('"not_ready"', "")
        .replace('"ready"', "")
    )

    for pattern in sensitive_patterns:
        assert (
            pattern not in body_without_ok_error
        ), f"Security: Internal detail '{pattern}' found in /ready response"


@pytest.mark.asyncio
async def test_ready_has_correlation_id_header(client: AsyncClient) -> None:
    """Every response must include a correlation ID header."""
    response = await client.get("/api/v1/ready")
    assert "x-correlation-id" in response.headers
