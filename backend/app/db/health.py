"""
PEVN Backend — Database Health Check

Provides functions to verify database connectivity and availability.
Used by the readiness endpoint to determine if the application
is ready to serve traffic.

Security:
  - Error messages returned to callers are safe for API exposure.
  - Internal exception details are logged server-side only.
  - The database URL is never included in error responses.
"""

from __future__ import annotations

from sqlalchemy import text

from app.core.logging import get_logger
from app.db.session import get_engine

logger = get_logger(__name__)


async def check_database_connectivity() -> tuple[bool, str]:
    """
    Verify that the database is reachable and responding.

    Performs a lightweight query (SELECT 1) to confirm the connection
    is alive and the database is accepting queries.

    Returns:
        A tuple of (is_healthy: bool, message: str).
        The message is safe to include in API responses.

    Note:
        This does NOT verify that migrations are up to date.
        That responsibility belongs to the deployment process.
    """
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True, "ok"

    except Exception as exc:
        # Log the full exception server-side for debugging
        logger.error(
            "Database connectivity check failed",
            error_type=type(exc).__name__,
            # Do NOT log exc_info here as it may contain connection details
        )
        # Return a safe, generic message to the caller
        return False, "error"
