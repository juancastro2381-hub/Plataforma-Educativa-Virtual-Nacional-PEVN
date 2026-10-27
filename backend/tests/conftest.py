"""
PEVN Backend — Test Configuration & Fixtures

Provides fixtures for async HTTP client and isolated in-memory test database sessions.
"""

from __future__ import annotations

import os
import re
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

# ---------------------------------------------------------------------------
# Set default test environment variables
# ---------------------------------------------------------------------------
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("LOG_LEVEL", "WARNING")
os.environ.setdefault("LOG_FORMAT", "console")
os.environ.setdefault(
    "SECRET_KEY",
    "test-secret-key-pevn-phase1-not-for-production-" + "0" * 80,
)
os.environ.setdefault(
    "DATABASE_URL",
    "sqlite+aiosqlite:///:memory:",
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")
os.environ.setdefault("ALLOWED_HOSTS", "localhost,127.0.0.1,testserver")

from app.core.config import get_settings
from app.core.security.interfaces import SystemRole
from app.db.base import Base
from app.db.session import get_async_session
from app.main import create_application
from app.models.grade import EducationalLevel, Grade
from app.models.role import Permission, Role


from app.core.db_safety import DatabaseSecurityError, get_safe_test_db_url


def get_test_postgres_url() -> str:
    """
    Return the isolated PostgreSQL test database connection URL.

    Enforces strict fail-closed validation targeting 'pevn_test_db'
    via app.core.db_safety.get_safe_test_db_url.
    """
    return get_safe_test_db_url(as_asyncpg=False)


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """Use asyncio as the anyio backend for async tests."""
    return "asyncio"


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide an isolated in-memory SQLite database session for tests.
    """
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create all tables in SQLite
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    try:
        async with session_maker() as session:
            # Seed canonical roles, permissions, and role_permissions via RbacBootstrapService
            from app.services.rbac_bootstrap_service import RbacBootstrapService
            bootstrap = RbacBootstrapService(session=session)
            await bootstrap.seed_canonical_rbac_if_needed()

            # Seed standard national grades
            grades_data = [
                ("TRANSICION", "Transición", EducationalLevel.PREESCOLAR, 0),
                ("G01", "Primero", EducationalLevel.PRIMARIA, 1),
                ("G02", "Segundo", EducationalLevel.PRIMARIA, 2),
                ("G03", "Tercero", EducationalLevel.PRIMARIA, 3),
                ("G04", "Cuarto", EducationalLevel.PRIMARIA, 4),
                ("G05", "Quinto", EducationalLevel.PRIMARIA, 5),
                ("G06", "Sexto", EducationalLevel.SECUNDARIA, 6),
                ("G07", "Séptimo", EducationalLevel.SECUNDARIA, 7),
                ("G08", "Octavo", EducationalLevel.SECUNDARIA, 8),
                ("G09", "Noveno", EducationalLevel.SECUNDARIA, 9),
                ("G10", "Décimo", EducationalLevel.MEDIA, 10),
                ("G11", "Undécimo", EducationalLevel.MEDIA, 11),
            ]
            for code, gname, ed_level, order in grades_data:
                grade = Grade(
                    code=code,
                    name=gname,
                    level=ed_level,
                    ordinal_order=order,
                )
                session.add(grade)

            await session.commit()
            yield session
    finally:
        drop_err: Exception | None = None
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
        except Exception as exc:
            drop_err = exc
        finally:
            try:
                await engine.dispose()
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
                sanitized_disp = sanitize_error_message(str(disp_exc))
                raise RuntimeError(
                    f"Database engine dispose failed: {type(disp_exc).__name__}: {sanitized_disp}"
                ) from disp_exc

        if drop_err is not None:
            sanitized_drop = sanitize_error_message(str(drop_err))
            err = RuntimeError(
                f"Database metadata drop_all failed: {type(drop_err).__name__}: {sanitized_drop}"
            )
            err.__cause__ = drop_err
            raise err from drop_err


def sanitize_error_message(msg: str) -> str:
    """
    Sanitize exception details that might contain database connection URLs,
    usernames, passwords, tokens, or other sensitive secrets.
    """
    # 1. Mask URI credentials: scheme://user:password@host -> scheme://user:***@host
    cleaned = re.sub(r"(://[^:\s/@]+):([^@\s/]+)@", r"\1:***@", str(msg))
    # 2. Mask Authorization Bearer tokens
    cleaned = re.sub(r"(?i)\bbearer\s+[A-Za-z0-9_\-\.=]+", "Bearer ***", cleaned)
    # 3. Mask key=value or key: value secrets (avoiding re-masking ***)
    cleaned = re.sub(r"(?i)\b(password|passwd|secret|token|api_key)\s*[:=]\s*(?!\*\*)([^\s,;'\"]+)", r"\1=***", cleaned)
    return cleaned


async def cleanup_test_singletons() -> None:
    """
    Safely and strictly release singleton connection pools and background
    engines initialized during ASGI test client requests.

    Guarantees:
      - Always attempts cleanup of both rate_limiter and close_engine.
      - Safe when Redis or engine was never initialized (both check internally for None).
      - Surfaces genuine cleanup failures instead of silently swallowing them.
      - Sanitizes credentials, passwords, and tokens from exception reporting.
    """
    from app.core.security.rate_limiter import rate_limiter
    from app.db.session import _state, close_engine

    errors: list[Exception] = []

    try:
        await rate_limiter.close()
    except Exception as exc:
        errors.append(exc)
    finally:
        rate_limiter._redis = None

    try:
        await close_engine()
    except Exception as exc:
        errors.append(exc)
    finally:
        _state.engine = None
        _state.session_factory = None

    if errors:
        if len(errors) == 1:
            sanitized = sanitize_error_message(str(errors[0]))
            err = RuntimeError(
                f"Client teardown cleanup failed: {type(errors[0]).__name__}: {sanitized}"
            )
            err.__cause__ = errors[0]
            raise err from errors[0]

        messages = "; ".join(f"{type(e).__name__}: {sanitize_error_message(str(e))}" for e in errors)
        err = RuntimeError(f"Multiple client teardown cleanup failures: {messages}")
        err.__cause__ = errors[0]
        raise err


@pytest.fixture(scope="function")
async def client(
    db_session: AsyncSession,
) -> AsyncGenerator[AsyncClient, None]:
    """
    Provide an async HTTP test client with database session override.
    Guarantees structured teardown and singleton resource disposal.
    """
    get_settings.cache_clear()

    test_app = create_application()

    # Override get_async_session dependency to use the isolated test db_session
    async def _override_get_async_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    test_app.dependency_overrides[get_async_session] = _override_get_async_session

    try:
        async with AsyncClient(
            transport=ASGITransport(app=test_app),  # type: ignore[arg-type]
            base_url="http://testserver",
            headers={"Host": "localhost"},
        ) as test_client:
            yield test_client
    finally:
        get_settings.cache_clear()
        await cleanup_test_singletons()
