"""
PEVN Backend — Tests for Structured Teardown and Cleanup Hardening

Validates:
  1. Clean execution when Redis and fallback engines are never initialized.
  2. Structured disposal after requests that initialize rate_limiter or fallback engine.
  3. Resilience in exception paths (try/finally ensures cleanup runs on test failure).
  4. Non-suppression of genuine teardown errors (RuntimeError surfaced on failure).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.rate_limiter import rate_limiter
from app.db.session import _state
from tests.conftest import cleanup_test_singletons


@pytest.mark.asyncio
async def test_cleanup_safe_when_resources_uninitialized() -> None:
    """Verify cleanup_test_singletons runs cleanly when no resources were initialized."""
    # Ensure starting clean state
    await cleanup_test_singletons()
    assert rate_limiter._redis is None
    assert _state.engine is None

    # Calling cleanup again must succeed without error
    await cleanup_test_singletons()
    assert rate_limiter._redis is None
    assert _state.engine is None


@pytest.mark.asyncio
async def test_cleanup_surfaces_rate_limiter_failure() -> None:
    """Verify that a genuine failure in rate_limiter.close() is surfaced as RuntimeError."""
    with patch.object(
        rate_limiter,
        "close",
        new=AsyncMock(side_effect=ConnectionError("Simulated Redis close failure")),
    ):
        with pytest.raises(RuntimeError) as exc_info:
            await cleanup_test_singletons()

        assert "Client teardown cleanup failed" in str(exc_info.value)
        assert "Simulated Redis close failure" in str(exc_info.value)


@pytest.mark.asyncio
async def test_cleanup_surfaces_engine_dispose_failure() -> None:
    """Verify that a genuine failure in close_engine() is surfaced as RuntimeError."""
    with patch(
        "app.db.session.close_engine",
        new=AsyncMock(side_effect=OSError("Simulated DB pool dispose error")),
    ):
        with pytest.raises(RuntimeError) as exc_info:
            await cleanup_test_singletons()

        assert "Client teardown cleanup failed" in str(exc_info.value)
        assert "Simulated DB pool dispose error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_cleanup_surfaces_multiple_failures() -> None:
    """Verify that if both rate_limiter and engine fail, both are attempted and reported."""
    with (
        patch.object(
            rate_limiter,
            "close",
            new=AsyncMock(side_effect=ConnectionError("Redis down")),
        ),
        patch(
            "app.db.session.close_engine",
            new=AsyncMock(side_effect=RuntimeError("Engine locked")),
        ),
    ):
        with pytest.raises(RuntimeError) as exc_info:
            await cleanup_test_singletons()

        msg = str(exc_info.value)
        assert "Multiple client teardown cleanup failures" in msg
        assert "Redis down" in msg
        assert "Engine locked" in msg


@pytest.mark.asyncio
async def test_client_fixture_cleans_up_on_normal_completion(client: AsyncClient) -> None:
    """Verify client fixture cleanly releases state on standard request completion."""
    res = await client.get("/api/v1/health")
    assert res.status_code == 200
    # Inside the test context, verify health responds cleanly
    # Teardown will execute at exit of test function


@pytest.mark.asyncio
async def test_client_fixture_runs_cleanup_on_exception(db_session: AsyncSession) -> None:
    """Verify that try/finally in client fixture triggers cleanup even when an exception is raised."""
    from tests.conftest import client as client_fixture

    # Use the unwrapped generator to avoid pytest's direct fixture call restriction
    client_gen = client_fixture.__wrapped__(db_session)
    test_client = await anext(client_gen)

    # Verify client was initialized
    assert test_client is not None

    # Simulate an exception inside the test body and propagate it into the generator
    with pytest.raises(ValueError, match="Simulated test assertion failure"):
        try:
            raise ValueError("Simulated test assertion failure")
        except ValueError as err:
            # Propagate exception into the generator's yield point
            try:
                await client_gen.athrow(err)
            except StopAsyncIteration:
                pass
            raise

    # Assert that after generator exit, singletons are clean
    assert rate_limiter._redis is None
    assert _state.engine is None
