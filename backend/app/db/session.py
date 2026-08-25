"""
PEVN Backend — Async Database Session Factory

Provides an async SQLAlchemy engine and session factory.
All database I/O uses async/await to avoid blocking the event loop.

Security:
  - The DATABASE_URL is never logged (use settings.get_safe_database_url() for logging).
  - Connection pooling is configured with safe timeouts.
  - DB_POOL_PRE_PING ensures stale connections are detected before use.

Usage as FastAPI dependency:
    from app.db.session import get_async_session
    from sqlalchemy.ext.asyncio import AsyncSession
    from fastapi import Depends

    async def my_endpoint(db: AsyncSession = Depends(get_async_session)):
        result = await db.execute(select(MyModel))
        ...
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.core.logging import get_logger

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine

logger = get_logger(__name__)


class _DBSessionState:
    """Encapsulates database engine and session factory singleton state."""

    engine: AsyncEngine | None = None
    session_factory: async_sessionmaker[AsyncSession] | None = None


_state = _DBSessionState()


def get_engine() -> AsyncEngine:
    """
    Return the module-level async database engine, creating it if needed.

    The engine is a connection pool — it is created once and reused.
    """
    if _state.engine is None:
        _state.engine = _create_engine()
    return _state.engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the module-level async session factory."""
    if _state.session_factory is None:
        _state.session_factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,  # Allows accessing attributes after commit
            autoflush=False,  # Explicit control over flushes
            autocommit=False,  # Always use explicit transactions
        )
    return _state.session_factory


def _create_engine() -> AsyncEngine:
    """Create and configure the async SQLAlchemy engine."""
    settings = get_settings()

    # Log the database connection (with password masked — never log raw URL)
    logger.info(
        "Initializing database connection pool",
        database_url=settings.get_safe_database_url(),
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_recycle=settings.DB_POOL_RECYCLE,
    )

    if settings.DATABASE_URL.startswith("sqlite"):
        return create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DB_ECHO,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

    return create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DB_ECHO,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_recycle=settings.DB_POOL_RECYCLE,
        pool_pre_ping=settings.DB_POOL_PRE_PING,
        # Connection arguments passed directly to asyncpg
        connect_args={
            "server_settings": {
                # Set a reasonable application name for DB monitoring
                "application_name": "pevn-backend",
            },
            "command_timeout": 60,  # seconds — hard timeout for individual queries
        },
    )


async def close_engine() -> None:
    """
    Dispose of the database engine and all pooled connections.
    Must be called during application shutdown.
    """
    if _state.engine is not None:
        logger.info("Closing database connection pool")
        await _state.engine.dispose()
        _state.engine = None
        _state.session_factory = None


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields a database session per request.

    The session is automatically closed after the request completes.
    Transactions must be explicitly committed by the caller.

    Example:
        async def my_endpoint(db: AsyncSession = Depends(get_async_session)):
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            ...
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
