"""
PEVN Diagnostic Safety Helper — Centralized Database Connection Safety (DOC-03-R2)

This module MUST be used by diagnostic and scratch scripts to prevent accidental
execution against operational or production databases.
"""

from __future__ import annotations

import sys
from pathlib import Path
from contextlib import asynccontextmanager

# Ensure backend root is on sys.path
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from app.core.db_safety import (
    DatabaseSecurityError,
    get_safe_test_db_url,
    get_safe_operational_readonly_url,
    mask_url_credentials,
    validate_and_sanitize_db_url,
)

__all__ = [
    "DatabaseSecurityError",
    "get_safe_test_db_url",
    "get_safe_operational_readonly_url",
    "mask_url_credentials",
    "validate_and_sanitize_db_url",
    "safe_asyncpg_connect",
    "create_safe_async_engine",
]


def create_safe_async_engine(mode: str = "test", **kwargs):
    """
    Create a SQLAlchemy AsyncEngine with fail-closed URL validation.

    Args:
        mode: 'test' (enforces pevn_test_db)
              'operational_readonly' (enforces pevn_db with explicit opt-in)
        **kwargs: Passed directly to create_async_engine.
    """
    from sqlalchemy.ext.asyncio import create_async_engine as _sa_create_async_engine

    if mode == "test":
        url = get_safe_test_db_url(as_asyncpg=False)
    elif mode == "operational_readonly":
        url = get_safe_operational_readonly_url(as_asyncpg=False)
    else:
        raise DatabaseSecurityError(f"Unsupported engine mode '{mode}'")

    return _sa_create_async_engine(url, **kwargs)



async def safe_asyncpg_connect(mode: str = "test"):
    """
    Connect to the database via asyncpg with fail-closed validation.

    Args:
        mode: 'test' (connects only to pevn_test_db)
              'operational_readonly' (requires ALLOW_OPERATIONAL_DIAGNOSTICS=true)

    Returns:
        An active asyncpg connection.
    """
    import asyncpg

    if mode == "test":
        url = get_safe_test_db_url(as_asyncpg=True)
    elif mode == "operational_readonly":
        url = get_safe_operational_readonly_url(as_asyncpg=True)
    else:
        raise DatabaseSecurityError(f"Unsupported connection mode '{mode}'")

    return await asyncpg.connect(url)
