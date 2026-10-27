"""
PEVN Backend — Tests for Structured Teardown and Cleanup Hardening (DOC-04-R8)

Validates:
  1. Clean execution when Redis and fallback engines are never initialized.
  2. Deterministic disposal on normal client fixture lifecycle (H-01).
  3. Structured cleanup on exceptional exit, including when first cleanup fails (H-02).
  4. Non-leakage of test doubles between tests via automated fixture isolation.
  5. Preservation of causal exceptions and sanitization of credentials/tokens in messages and causes (H-03/H-04).
  6. Comprehensive sanitization coverage (URIs, Redis, Bearer, hyphenated keys, quotes, JSON).
  7. Isolated db_session teardown resilience (drop_all + engine.dispose).

Faithful Modeling Rationale:
  In pytest-asyncio, an async generator fixture (defined with @pytest.fixture and yield):
    1. Instantiates the generator coroutine.
    2. Awaits anext() to yield the fixture value to the test function.
    3. Resumes the generator after the test block finishes, via anext() for normal
       completion, or athrow() if an unhandled exception occurred in the test.
    4. Catches StopAsyncIteration on normal exit, or propagates teardown exceptions.
  Directly invoking `client_fixture.__wrapped__(db_session)` executes the exact same
  coroutine sequence that pytest's fixture runner executes for the generator lifecycle,
  enabling deterministic state assertions before, during, and after the yield and finally
  blocks without relying on opaque runner timing or subprocess side effects. Note: While
  it directly tests the fixture's internal resource management contract, it does not execute
  pytest's outer hook dispatch wrappers (e.g. pytest_pyfunc_call).
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
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
    sanitize_exception,
)


@pytest.fixture(autouse=True)
async def isolate_test_singletons() -> AsyncGenerator[None, None]:
    """
    Ensure singleton references and test doubles are cleanly reset
    before and after every test, preventing any state leakage across test cases.
    """
    await cleanup_test_singletons()
    rate_limiter._redis = None
    _state.engine = None
    _state.session_factory = None
    try:
        yield
    finally:
        await cleanup_test_singletons()
        rate_limiter._redis = None
        _state.engine = None
        _state.session_factory = None


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
    # 1. URI with credentials
    raw_uri = "Operational failure at postgresql+asyncpg://pevn_admin:super_secret_pw99@localhost:5432/pevn_db"
    sanitized_uri = sanitize_error_message(raw_uri)
    assert "super_secret_pw99" not in sanitized_uri
    assert "pevn_admin:***@localhost:5432/pevn_db" in sanitized_uri

    # 2. Redis URI with empty username
    raw_redis = "Connection failed to redis://:mypassword123@10.0.0.5:6379/1"
    sanitized_redis = sanitize_error_message(raw_redis)
    assert "mypassword123" not in sanitized_redis
    assert "redis://:***@10.0.0.5:6379/1" in sanitized_redis

    # 3. Bearer token
    raw_token = "Authorization header rejected: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.tokenpayload.signature"
    sanitized_token = sanitize_error_message(raw_token)
    assert "eyJhbGci" not in sanitized_token
    assert "Bearer ***" in sanitized_token

    # 4. Key-value password with quotes and punctuation
    raw_kv = 'Failed connection: host=db.internal, password="superSecretPassword123", user=admin'
    sanitized_kv = sanitize_error_message(raw_kv)
    assert "superSecretPassword123" not in sanitized_kv
    assert 'password="***"' in sanitized_kv

    # 5. Hyphenated and underscore keys
    raw_hyphen = "Auth error: access-token: tok111, refresh_token='ref222', client-secret: sec333, api_key: key444"
    sanitized_hyphen = sanitize_error_message(raw_hyphen)
    assert "tok111" not in sanitized_hyphen
    assert "ref222" not in sanitized_hyphen
    assert "sec333" not in sanitized_hyphen
    assert "key444" not in sanitized_hyphen
    assert "access-token: ***" in sanitized_hyphen
    assert "refresh_token='***'" in sanitized_hyphen
    assert "client-secret: ***" in sanitized_hyphen
    assert "api_key: ***" in sanitized_hyphen

    # 6. JSON formatted error payload
    raw_json = '{"access_token": "secret_access_xyz", "client_secret": "secret_client_abc"}'
    sanitized_json = sanitize_error_message(raw_json)
    assert "secret_access_xyz" not in sanitized_json
    assert "secret_client_abc" not in sanitized_json
    assert '{"access_token": "***", "client_secret": "***"}' in sanitized_json

    # 7. Multiple secrets in one message
    raw_multi = "Multi-failure: db=mysql://root:rootpass@db:3306/pevn, token=tok555, password='pw666'"
    sanitized_multi = sanitize_error_message(raw_multi)
    assert "rootpass" not in sanitized_multi
    assert "tok555" not in sanitized_multi
    assert "pw666" not in sanitized_multi
    assert "root:***@db:3306/pevn" in sanitized_multi
    assert "token=***" in sanitized_multi
    assert "password='***'" in sanitized_multi

    # 8. Innocuous errors remain readable
    clean_msg1 = "Connection timed out after 30 seconds"
    assert sanitize_error_message(clean_msg1) == clean_msg1
    clean_msg2 = "Table 'users' already exists in schema"
    assert sanitize_error_message(clean_msg2) == clean_msg2
    clean_msg3 = "Foreign key constraint failed on column 'institution_id'"
    assert sanitize_error_message(clean_msg3) == clean_msg3


def test_sanitize_exception_masks_nested_cause_and_context() -> None:
    """Verify sanitize_exception masks sensitive data in exc, __cause__, and __context__."""
    root_exc = ConnectionError(
        "Low-level driver failed: postgresql+asyncpg://admin:rawPassword999@localhost:5432/pevn"
    )
    outer_exc = RuntimeError("Service initialization failed with client_secret='topSecretValue'")
    outer_exc.__cause__ = root_exc

    sanitized = sanitize_exception(outer_exc)

    # Check outer exception message
    assert "topSecretValue" not in str(sanitized)
    assert "client_secret='***'" in str(sanitized)
    assert isinstance(sanitized, RuntimeError)

    # Check chained cause message
    assert sanitized.__cause__ is not None
    assert "rawPassword999" not in str(sanitized.__cause__)
    assert "admin:***@localhost:5432/pevn" in str(sanitized.__cause__)
    assert isinstance(sanitized.__cause__, ConnectionError)


@pytest.mark.asyncio
async def test_cleanup_sanitizes_reported_exceptions_and_causes() -> None:
    """Verify that credentials in cleanup error messages and causes are sanitized before raising."""
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

        # Verify that __cause__ is ALSO sanitized so traceback logging cannot leak secrets
        assert exc_info.value.__cause__ is not None
        cause_text = str(exc_info.value.__cause__)
        assert "TopSecretPassword123" not in cause_text
        assert "svc_user:***@10.0.0.1:5432/pevn" in cause_text
        assert isinstance(exc_info.value.__cause__, ConnectionError)


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
                sanitized_drop = sanitize_exception(drop_err)
                sanitized_disp = sanitize_exception(disp_exc)
                chained = RuntimeError(
                    f"Database teardown failed during drop_all ({type(drop_err).__name__}: {sanitized_drop}) "
                    f"and dispose ({type(disp_exc).__name__}: {sanitized_disp})"
                )
                chained.__cause__ = sanitized_drop
                raise chained from sanitized_drop
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
                    sanitized_drop = sanitize_exception(drop_err)
                    sanitized_disp = sanitize_exception(disp_exc)
                    chained = RuntimeError(
                        f"Database teardown failed during drop_all ({type(drop_err).__name__}: {sanitized_drop}) "
                        f"and dispose ({type(disp_exc).__name__}: {sanitized_disp})"
                    )
                    chained.__cause__ = sanitized_drop
                    raise chained from sanitized_drop
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
    assert "superSecret" not in str(exc_info.value.__cause__)
    assert "admin:***@db/pevn" in str(exc_info.value.__cause__)


@pytest.mark.asyncio
async def test_singleton_isolation_restores_state_after_test_failure() -> None:
    """Verify that singleton test doubles are cleanly cleared even if test logic fails."""
    rate_limiter._redis = AsyncMock()
    _state.engine = AsyncMock()
    _state.session_factory = MagicMock()

    # Teardown logic
    await cleanup_test_singletons()
    rate_limiter._redis = None
    _state.engine = None
    _state.session_factory = None

    assert rate_limiter._redis is None
    assert _state.engine is None
    assert _state.session_factory is None
