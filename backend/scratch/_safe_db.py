"""
PEVN Diagnostic Safety Helper — Centralized Database Connection Safety (DOC-03-R3)

This module MUST be used by diagnostic and scratch scripts to prevent accidental
execution against operational or production databases.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# Ensure backend root is on sys.path
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.core.db_safety import (
    DatabaseSecurityError,
    get_safe_test_db_url,
    get_safe_operational_readonly_url,
    mask_url_credentials,
    sanitize_exception_message,
    validate_and_sanitize_db_url,
)

__all__ = [
    "DatabaseSecurityError",
    "get_safe_test_db_url",
    "get_safe_operational_readonly_url",
    "mask_url_credentials",
    "sanitize_exception_message",
    "validate_and_sanitize_db_url",
    "safe_asyncpg_connect",
    "create_safe_async_engine",
]


def create_safe_async_engine(mode: str = "test", **kwargs: Any):
    """
    Create a SQLAlchemy AsyncEngine with fail-closed URL and destination validation.

    Args:
        mode: 'test' (enforces pevn_test_db and destination allowlist)
              'operational_readonly' (enforces pevn_db, explicit opt-in, and read-only transaction state)
        **kwargs: Passed directly to create_async_engine.
    """
    from sqlalchemy.ext.asyncio import create_async_engine as _sa_create_async_engine

    if mode == "test":
        url = get_safe_test_db_url(as_asyncpg=False)
        return _sa_create_async_engine(url, **kwargs)

    elif mode == "operational_readonly":
        url = get_safe_operational_readonly_url(as_asyncpg=False)
        # Enforce server-side read-only transaction state via connect_args for asyncpg
        connect_args = kwargs.pop("connect_args", {})
        server_settings = connect_args.get("server_settings", {})
        server_settings["default_transaction_read_only"] = "on"
        connect_args["server_settings"] = server_settings
        return _sa_create_async_engine(url, connect_args=connect_args, **kwargs)

    else:
        raise DatabaseSecurityError(f"Unsupported engine mode '{mode}'")


async def safe_asyncpg_connect(mode: str = "test", **kwargs: Any):
    """
    Connect to the database via asyncpg with fail-closed validation.

    Args:
        mode: 'test' (connects only to pevn_test_db on approved destination)
              'operational_readonly' (requires ALLOW_OPERATIONAL_DIAGNOSTICS=true and enforces read-only)

    Returns:
        An active asyncpg connection.
    """
    import asyncpg

    if mode == "test":
        url = get_safe_test_db_url(as_asyncpg=True)
        return await asyncpg.connect(url, **kwargs)

    elif mode == "operational_readonly":
        url = get_safe_operational_readonly_url(as_asyncpg=True)
        # Pass server_settings to enforce read-only transaction state at the PostgreSQL session level
        server_settings = kwargs.pop("server_settings", {})
        server_settings["default_transaction_read_only"] = "on"
        return await asyncpg.connect(url, server_settings=server_settings, **kwargs)

    else:
        raise DatabaseSecurityError(f"Unsupported connection mode '{mode}'")
