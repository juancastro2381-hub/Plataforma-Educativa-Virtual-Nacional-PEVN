"""
PEVN Core — Database Safety & Fail-Closed URL Enforcement (DOC-03-R2)

Enforces strict fail-closed database target validation for integration tests
and diagnostic scripts:
  1. Only 'pevn_test_db' is permitted for test operations.
  2. 'pevn_db' is strictly forbidden in test mode.
  3. No silent fallback from TEST_DATABASE_URL to DATABASE_URL.
  4. Rigorous URL parsing (no substring-only checks).
  5. Scheme validation (only PostgreSQL drivers allowed).
  6. Credential masking in all error reporting.
  7. Strict separation of test vs. operational read-only diagnostics.
"""

from __future__ import annotations

import os
from urllib.parse import urlparse, urlunparse
from typing import Literal


ALLOWED_TEST_DATABASES: frozenset[str] = frozenset({"pevn_test_db"})
ALLOWED_OPERATIONAL_DATABASES: frozenset[str] = frozenset({"pevn_db"})

ALLOWED_POSTGRES_SCHEMES: frozenset[str] = frozenset({
    "postgresql",
    "postgresql+asyncpg",
    "postgresql+psycopg2",
    "postgres",
})


class DatabaseSecurityError(RuntimeError):
    """Raised when database target fails fail-closed security validation."""
    pass


def mask_url_credentials(url_str: str) -> str:
    """
    Mask username and password in a database connection URL.
    Never exposes raw secrets in error messages or logs.
    """
    if not url_str:
        return "<empty>"
    try:
        parsed = urlparse(url_str)
        if not parsed.netloc:
            return "<unparseable-url>"
        
        # Build masked netloc
        host = parsed.hostname or "unknown-host"
        port = f":{parsed.port}" if parsed.port else ""
        masked_user = f"{parsed.username}:***@" if parsed.username else ""
        masked_netloc = f"{masked_user}{host}{port}"
        
        return urlunparse((
            parsed.scheme,
            masked_netloc,
            parsed.path,
            parsed.params,
            "",  # strip query to avoid leaking query parameters
            "",  # strip fragment
        ))
    except Exception:
        return "<sanitized-url>"


def validate_and_sanitize_db_url(
    raw_url: str | None,
    mode: Literal["test", "operational_readonly"] = "test",
) -> str:
    """
    Parse and strictly validate a database connection URL.

    Args:
        raw_url: The connection string to validate.
        mode: 'test' (enforces pevn_test_db) or 'operational_readonly' (requires explicit opt-in).

    Returns:
        The validated connection string.

    Raises:
        DatabaseSecurityError: On any validation failure.
    """
    if not raw_url or not raw_url.strip():
        raise DatabaseSecurityError(
            f"Database URL is missing or empty for mode '{mode}'."
        )

    clean_url = raw_url.strip()

    try:
        parsed = urlparse(clean_url)
    except Exception as exc:
        raise DatabaseSecurityError(f"Malformed database connection URL: {exc}") from None

    # 1. Scheme validation
    scheme = parsed.scheme.lower()
    if not scheme or scheme not in ALLOWED_POSTGRES_SCHEMES:
        masked = mask_url_credentials(clean_url)
        raise DatabaseSecurityError(
            f"Unsupported database scheme '{scheme}'. Only PostgreSQL drivers "
            f"({', '.join(sorted(ALLOWED_POSTGRES_SCHEMES))}) are allowed. Target: {masked}"
        )

    # 2. Host validation
    if not parsed.hostname:
        masked = mask_url_credentials(clean_url)
        raise DatabaseSecurityError(
            f"Database connection URL missing valid host. Target: {masked}"
        )

    # 3. Path / Database Name Extraction (Strict, no substring matching)
    path = parsed.path.lstrip("/")
    if not path:
        masked = mask_url_credentials(clean_url)
        raise DatabaseSecurityError(
            f"Database connection URL missing database name. Target: {masked}"
        )

    # Database name is the first path segment before query, fragment, or slashes
    db_name = path.split("?")[0].split("#")[0].strip()
    if "/" in db_name or "\\" in db_name:
        masked = mask_url_credentials(clean_url)
        raise DatabaseSecurityError(
            f"Database name contains illegal path traversal characters. Target: {masked}"
        )

    masked_target = mask_url_credentials(clean_url)

    # 4. Mode Enforcement
    if mode == "test":
        if db_name == "pevn_db":
            raise DatabaseSecurityError(
                "FAIL-CLOSED REJECTION: Connection to operational database 'pevn_db' "
                "is strictly forbidden in test mode. Tests and test diagnostics must "
                f"target 'pevn_test_db'. Attempted: {masked_target}"
            )
        if db_name not in ALLOWED_TEST_DATABASES:
            raise DatabaseSecurityError(
                f"FAIL-CLOSED REJECTION: Unauthorized database target '{db_name}'. "
                f"Expected explicitly allowed test database 'pevn_test_db'. Attempted: {masked_target}"
            )

    elif mode == "operational_readonly":
        opt_in = os.environ.get("ALLOW_OPERATIONAL_DIAGNOSTICS", "").strip().lower()
        if opt_in not in ("true", "1", "yes"):
            raise DatabaseSecurityError(
                "FAIL-CLOSED REJECTION: Operational database access is disabled by default. "
                "To run legitimate read-only diagnostics against 'pevn_db', you must explicitly set "
                "ALLOW_OPERATIONAL_DIAGNOSTICS=true in the execution environment."
            )
        if db_name not in ALLOWED_OPERATIONAL_DATABASES:
            raise DatabaseSecurityError(
                f"FAIL-CLOSED REJECTION: Operational diagnostic target '{db_name}' is not allowed. "
                f"Expected 'pevn_db'. Attempted: {masked_target}"
            )

    else:
        raise DatabaseSecurityError(f"Unknown database validation mode: '{mode}'")

    return clean_url


from dotenv import load_dotenv

# Load .env once at module import
load_dotenv()


def get_safe_test_db_url(as_asyncpg: bool = False) -> str:
    """
    Resolve and validate the isolated test database URL.
    Reads exclusively from TEST_DATABASE_URL. Does NOT fall back to DATABASE_URL.

    Args:
        as_asyncpg: If True, returns 'postgresql://' URL suitable for asyncpg.connect().
                    If False, returns 'postgresql+asyncpg://' for SQLAlchemy async engine.
    """
    test_url = os.environ.get("TEST_DATABASE_URL")
    if not test_url or not test_url.strip():
        raise DatabaseSecurityError(
            "FAIL-CLOSED: TEST_DATABASE_URL environment variable is not configured. "
            "An isolated PostgreSQL test database targeting 'pevn_test_db' is required. "
            "(Example: TEST_DATABASE_URL=postgresql+asyncpg://<user>:<password>@localhost:5433/pevn_test_db)"
        )

    validated = validate_and_sanitize_db_url(test_url, mode="test")

    if as_asyncpg:
        return (
            validated.replace("postgresql+asyncpg://", "postgresql://")
                     .replace("postgresql+psycopg2://", "postgresql://")
        )
    else:
        if validated.startswith("postgresql://"):
            return validated.replace("postgresql://", "postgresql+asyncpg://", 1)
        if validated.startswith("postgres://"):
            return validated.replace("postgres://", "postgresql+asyncpg://", 1)
        return validated


def get_safe_operational_readonly_url(as_asyncpg: bool = False) -> str:
    """
    Resolve and validate operational database URL for read-only diagnostics.
    Requires ALLOW_OPERATIONAL_DIAGNOSTICS=true. Does NOT accept test database.
    """
    op_url = os.environ.get("DATABASE_URL")
    if not op_url or not op_url.strip():
        raise DatabaseSecurityError(
            "FAIL-CLOSED: DATABASE_URL environment variable is not configured."
        )

    validated = validate_and_sanitize_db_url(op_url, mode="operational_readonly")

    if as_asyncpg:
        return (
            validated.replace("postgresql+asyncpg://", "postgresql://")
                     .replace("postgresql+psycopg2://", "postgresql://")
        )
    else:
        if validated.startswith("postgresql://"):
            return validated.replace("postgresql://", "postgresql+asyncpg://", 1)
        if validated.startswith("postgres://"):
            return validated.replace("postgres://", "postgresql+asyncpg://", 1)
        return validated
