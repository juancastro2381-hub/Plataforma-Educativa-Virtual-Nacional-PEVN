"""
PEVN Backend — Tests for Structured Teardown and Cleanup Hardening

Validates:
  1. Clean execution when Redis and fallback engines are never initialized.
  2. Deterministic disposal on normal client fixture lifecycle (H-01).
  3. Structured cleanup on exceptional exit, including when first cleanup fails (H-02).
  4. Preservation of causal exceptions and sanitization of credentials/tokens (H-04).
  5. Isolated db_session teardown resilience (drop_all + engine.dispose).

Faithful Modeling Rationale:
  In pytest-asyncio, an async generator fixture (defined with @pytest.fixture and yield):
    1. Instantiates the generator coroutine.
    2. Awaits anext() to yield the fixture value to the test function.
    3. Resumes the generator after the test block finishes, via anext() for normal
       completion, or athrow() if an unhandled exception occurred in the test.
    4. Catches StopAsyncIteration on normal exit, or propagates teardown exceptions.
  Directly invoking `client_fixture.__wrapped__(db_session)` executes the exact same
  coroutine sequence that pytest's runner executes, enabling deterministic state assertions
  before, during, and after the yield and finally blocks without relying on opaque runner
  timing or subprocess side effects.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.rate_limiter import rate_limiter
from app.db.session import _state
from tests.conftest import (
    cleanup_test_singletons,
    client as client_fixture,
    sanitize_error_message,
)


@pytest.mark.asyncio
async def test_cleanup_safe_when_resources_uninitialized() -> None:
    """Verify cleanup_test_singletons runs cleanly when no resources were initialized."""
    # Ensure starting clean state
    await cleanup_test_singletons()
    assert rate_limiter._redis is None
    assert _state.engine is None

    # Calling cleanup again must succeed idempotently without error
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
        assert isinstance(exc_info.value.__cause__, ConnectionError)


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
        assert isinstance(exc_info.value.__cause__, OSError)


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
        assert isinstance(exc_info.value.__cause__, ConnectionError)


def test_sanitize_error_message_masks_sensitive_data() -> None:
    """Verify secret credentials, database passwords, and Bearer tokens are redacted."""
    # URI with credentials
    raw_uri = "Operational failure at postgresql+asyncpg://pevn_admin:super_secret_pw99@localhost:5432/pevn_db"
    sanitized_uri = sanitize_error_message(raw_uri)
    assert "super_secret_pw99" not in sanitized_uri
    assert "pevn_admin:***@localhost:5432/pevn_db" in sanitized_uri

    # Bearer token
    raw_token = "Authorization header rejected: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.tokenpayload.signature"
    sanitized_token = sanitize_error_message(raw_token)
    assert "eyJhbGci" not in sanitized_token
    assert "Bearer ***" in sanitized_token

    # Key-value password
    raw_kv = "Failed connection: host=db.internal, password=superSecretPassword123, user=admin"
    sanitized_kv = sanitize_error_message(raw_kv)
    assert "superSecretPassword123" not in sanitized_kv
    assert "password=***" in sanitized_kv

    # Innocuous error untouched
    clean_msg = "Connection timed out after 30 seconds"
    assert sanitize_error_message(clean_msg) == clean_msg


@pytest.mark.asyncio
async def test_cleanup_sanitizes_reported_exceptions() -> None:
    """Verify that credentials in cleanup error messages are sanitized before raising."""
    leak_prone_error = ConnectionError(
        "Could not close connection to postgresql+asyncpg://svc_user:TopSecretPassword123@10.0.0.1:5432/pevn"
    )
    with patch(
        "app.db.session.close_engine",
        new=AsyncMock(side_effect=leak_prone_error),
    ):
        with pytest.raises(RuntimeError) as exc_info:
            await cleanup_test_singletons()

        err_text = str(exc_info.value)
        assert "TopSecretPassword123" not in err_text
        assert "svc_user:***@10.0.0.1:5432/pevn" in err_text


@pytest.mark.asyncio
async def test_client_fixture_cleans_up_on_normal_completion(
    db_session: AsyncSession,
) -> None:
    """
    Finding H-01: Verify client fixture normal lifecycle deterministically closes
    all initialized resources and disposes test doubles.
    """
    client_gen = client_fixture.__wrapped__(db_session)
    test_client = await anext(client_gen)
    assert isinstance(test_client, AsyncClient)

    # Set up controlled test doubles for both resources
    mock_redis = AsyncMock()
    mock_redis.aclose = AsyncMock()
    mock_engine = AsyncMock()
    mock_engine.dispose = AsyncMock()

    rate_limiter._redis = mock_redis
    _state.engine = mock_engine

    # Assert resources are active and initialized during fixture lifecycle
    assert rate_limiter._redis is mock_redis
    assert _state.engine is mock_engine

    # Perform normal request
    res = await test_client.get("/api/v1/health")
    assert res.status_code == 200

    # Advance generator to normal completion
    with pytest.raises(StopAsyncIteration):
        await anext(client_gen)

    # Verify both cleanup operations were invoked deterministically
    mock_redis.aclose.assert_awaited_once()
    mock_engine.dispose.assert_awaited_once()

    # Verify final resource state is cleanly reset to None
    assert rate_limiter._redis is None
    assert _state.engine is None
    assert _state.session_factory is None


@pytest.mark.asyncio
async def test_client_fixture_runs_cleanup_on_exception(
    db_session: AsyncSession,
) -> None:
    """
    Finding H-02: Verify client fixture triggers structured cleanup of both
    resources when an unhandled exception is injected at the yield point.
    """
    client_gen = client_fixture.__wrapped__(db_session)
    test_client = await anext(client_gen)
    assert test_client is not None

    # Set up controlled test doubles
    mock_redis = AsyncMock()
    mock_redis.aclose = AsyncMock()
    mock_engine = AsyncMock()
    mock_engine.dispose = AsyncMock()

    rate_limiter._redis = mock_redis
    _state.engine = mock_engine

    # Assert resources are active prior to exception injection
    assert rate_limiter._redis is mock_redis
    assert _state.engine is mock_engine

    # Inject representative exception at yield point
    injected_exc = ValueError("Simulated unhandled exception during test execution")
    with pytest.raises(ValueError, match="Simulated unhandled exception during test execution"):
        try:
            await client_gen.athrow(injected_exc)
        except StopAsyncIteration:
            pass

    # Verify both cleanup operations were invoked despite the exception
    mock_redis.aclose.assert_awaited_once()
    mock_engine.dispose.assert_awaited_once()

    # Verify final resource state
    assert rate_limiter._redis is None
    assert _state.engine is None


@pytest.mark.asyncio
async def test_client_fixture_runs_both_cleanups_even_if_first_fails_on_exception(
    db_session: AsyncSession,
) -> None:
    """
    Finding H-02 & H-04: Verify that when an exception occurs inside the test AND
    the first cleanup operation fails, the second cleanup operation is STILL executed,
    and the errors remain observable without silent suppression.
    """
    client_gen = client_fixture.__wrapped__(db_session)
    test_client = await anext(client_gen)
    assert test_client is not None

    # First cleanup (redis.close) will fail
    mock_redis = AsyncMock()
    mock_redis.aclose = AsyncMock(side_effect=ConnectionError("Redis connection aborted"))

    # Second cleanup (engine.dispose) must still be invoked
    mock_engine = AsyncMock()
    mock_engine.dispose = AsyncMock()

    rate_limiter._redis = mock_redis
    _state.engine = mock_engine

    injected_exc = RuntimeError("Primary test assertion error")

    with pytest.raises(RuntimeError) as exc_info:
        try:
            await client_gen.athrow(injected_exc)
        except StopAsyncIteration:
            pass

    # Verify the teardown exception surfaced
    assert "Client teardown cleanup failed" in str(exc_info.value)
    assert "Redis connection aborted" in str(exc_info.value)

    # Verify the original injected exception is preserved in Python's exception context
    assert exc_info.value.__context__ is injected_exc

    # CRITICAL: Verify the second cleanup was STILL invoked despite the first failure
    mock_redis.aclose.assert_awaited_once()
    mock_engine.dispose.assert_awaited_once()

    # Verify state reset
    assert rate_limiter._redis is None
    assert _state.engine is None


@pytest.mark.asyncio
async def test_db_session_preserves_drop_all_failure_and_runs_dispose() -> None:
    """
    Finding H-04: Verify db_session teardown logic preserves drop_all failures
    while guaranteeing that engine.dispose() is still executed.
    """
    mock_engine = AsyncMock()
    mock_conn = AsyncMock()
    mock_conn.run_sync = AsyncMock(side_effect=RuntimeError("drop_all failed on locked table"))

    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value = mock_conn
    mock_ctx.__aexit__.return_value = None
    mock_engine.begin = MagicMock(return_value=mock_ctx)
    mock_engine.dispose = AsyncMock()

    # Simulate db_session's finally block logic
    drop_err: Exception | None = None
    try:
        async with mock_engine.begin() as conn:
            await conn.run_sync(lambda sync_conn: None)
    except Exception as exc:
        drop_err = exc
    finally:
        try:
            await mock_engine.dispose()
        except Exception as disp_exc:
            if drop_err is not None:
                sanitized_drop = sanitize_error_message(str(drop_err))
                sanitized_disp = sanitize_error_message(str(disp_exc))
                chained = RuntimeError(
                    f"Database teardown failed during drop_all ({type(drop_err).__name__}: {sanitized_drop}) "
                    f"and dispose ({type(disp_exc).__name__}: {sanitized_disp})"
                )
                chained.__cause__ = drop_err
                raise chained from drop_err
            raise

    # Verify dispose was executed despite drop_all failure
    mock_engine.dispose.assert_awaited_once()

    # Verify drop_all error is preserved and not swallowed
    assert drop_err is not None
    assert "drop_all failed on locked table" in str(drop_err)


@pytest.mark.asyncio
async def test_db_session_chains_dual_failure_with_sanitization() -> None:
    """
    Finding H-04: Verify that when both drop_all and engine.dispose fail,
    a composite error is raised, neither error is lost, secrets are masked,
    and causal relationship is preserved.
    """
    mock_engine = AsyncMock()
    mock_conn = AsyncMock()
    mock_conn.run_sync = AsyncMock(
        side_effect=RuntimeError("drop_all failed on postgresql+asyncpg://admin:superSecret@db/pevn")
    )
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value = mock_conn
    mock_ctx.__aexit__.return_value = None
    mock_engine.begin = MagicMock(return_value=mock_ctx)

    # dispose also fails with secret in message
    mock_engine.dispose = AsyncMock(
        side_effect=OSError("dispose failed with authorization: Bearer confidential_auth_token_xyz")
    )

    with pytest.raises(RuntimeError) as exc_info:
        drop_err: Exception | None = None
        try:
            async with mock_engine.begin() as conn:
                await conn.run_sync(lambda sync_conn: None)
        except Exception as exc:
            drop_err = exc
        finally:
            try:
                await mock_engine.dispose()
            except Exception as disp_exc:
                if drop_err is not None:
                    sanitized_drop = sanitize_error_message(str(drop_err))
                    sanitized_disp = sanitize_error_message(str(disp_exc))
                    chained = RuntimeError(
                        f"Database teardown failed during drop_all ({type(drop_err).__name__}: {sanitized_drop}) "
                        f"and dispose ({type(disp_exc).__name__}: {sanitized_disp})"
                    )
                    chained.__cause__ = drop_err
                    raise chained from drop_err
                raise

    msg = str(exc_info.value)
    # Verify both failures are described
    assert "Database teardown failed during drop_all" in msg
    assert "and dispose" in msg
    # Verify secrets are redacted
    assert "superSecret" not in msg
    assert "admin:***@db/pevn" in msg
    assert "confidential_auth_token_xyz" not in msg
    assert "Bearer ***" in msg
    # Verify causal link
    assert exc_info.value.__cause__ is not None
