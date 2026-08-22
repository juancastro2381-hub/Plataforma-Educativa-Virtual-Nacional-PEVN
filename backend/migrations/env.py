"""
Alembic migration environment configuration.

Supports async SQLAlchemy (asyncpg driver).
DATABASE_URL is loaded from application settings — not from alembic.ini.

Run from the backend/ directory:
    alembic upgrade head
    alembic revision --autogenerate -m "description"
    alembic downgrade -1
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Import the application settings to get DATABASE_URL
from app.core.config import get_settings

# Import the declarative base so Alembic can detect model changes.
# All domain models must be imported in app.db.base (via the model registry)
# for autogenerate to work correctly.
from app.db.base import Base

# ---------------------------------------------------------------------------
# Alembic configuration
# ---------------------------------------------------------------------------
config = context.config

# Configure Python logging from alembic.ini [loggers] section
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata object that Alembic uses for autogenerate
target_metadata = Base.metadata


def get_url() -> str:
    """Get the database URL from application settings."""
    settings = get_settings()
    return settings.DATABASE_URL


# ---------------------------------------------------------------------------
# Offline migrations (no live DB connection)
# ---------------------------------------------------------------------------


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    Generates SQL scripts without a live database connection.
    Useful for generating migration scripts for review before applying.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online migrations (async with live DB connection)
# ---------------------------------------------------------------------------


def do_run_migrations(connection: Connection) -> None:
    """Run migrations synchronously within an async connection context."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        # Include schema name for multi-schema support in the future
        include_schemas=False,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' async mode using asyncpg."""
    settings = get_settings()

    # Build configuration for the async engine
    configuration = {
        "sqlalchemy.url": settings.DATABASE_URL,
    }

    # Use NullPool for migrations — we don't want connection pooling here
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry point for online migration mode."""
    asyncio.run(run_async_migrations())


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
