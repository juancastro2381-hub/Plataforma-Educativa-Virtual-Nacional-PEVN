"""
PEVN Core — Database Safety & Fail-Closed Destination Allowlisting (DOC-03-R3)

Enforces strict fail-closed database target validation for integration tests
and diagnostic scripts:
  1. Only 'pevn_test_db' is permitted for test operations.
  2. 'pevn_db' is strictly forbidden in test mode.
  3. No silent fallback from TEST_DATABASE_URL to DATABASE_URL.
  4. Rigorous URL parsing and destination allowlisting (host, port, scheme).
  5. Configurable destination allowlist for local Docker and approved CI/CD.
  6. Disallow dangerous query parameters that could alter destination.
  7. Genuine read-only operational diagnostics enforcement.
  8. Credential masking and centralized exception sanitization.
"""

from __future__ import annotations

import os
import re
from typing import Literal
from urllib.parse import parse_qs, urlparse, urlunparse
from dotenv import load_dotenv

# Load .env once at module import
load_dotenv()


ALLOWED_TEST_DATABASES: frozenset[str] = frozenset({"pevn_test_db"})
ALLOWED_OPERATIONAL_DATABASES: frozenset[str] = frozenset({"pevn_db"})

ALLOWED_POSTGRES_SCHEMES: frozenset[str] = frozenset({
    "postgresql",
    "postgresql+asyncpg",
    "postgresql+psycopg2",
    "postgres",
})

# Default permitted destinations for local Docker and standard container environments
DEFAULT_ALLOWED_TEST_HOSTS: frozenset[str] = frozenset({
    "localhost",
    "127.0.0.1",
    "::1",
    "db",
    "pevn-db",
    "postgres",
})

DEFAULT_ALLOWED_TEST_PORTS: frozenset[int] = frozenset({
    5432,
    5433,
    5434,
})

# Connection query parameters that could alter the effective destination or security context
DISALLOWED_QUERY_PARAMS: frozenset[str] = frozenset({
    "host",
    "hostaddr",
    "port",
    "dbname",
    "service",
    "passfile",
    "target_session_attrs",
})

# Regular expressions for credential sanitization
PASSWORD_PATTERN = re.compile(
    r'(password|passwd|pwd|secret|token|auth_token)\s*[:=]\s*([^\s,;\'"&]+)',
    re.IGNORECASE,
)
URL_CRED_PATTERN = re.compile(
    r'([a-zA-Z][a-zA-Z0-9+.-]*://)([^:@/]+):([^@/]+)@',
    re.IGNORECASE,
)


class DatabaseSecurityError(RuntimeError):
    """Raised when database target fails fail-closed security validation."""
    pass


def get_allowed_test_hosts() -> frozenset[str]:
    """
    Get the set of permitted test database hosts.
    Merges default local/container hosts with ALLOWED_TEST_DB_HOSTS if configured.
    """
    custom = os.environ.get("ALLOWED_TEST_DB_HOSTS", "").strip()
    if custom:
        extra = {h.strip().lower() for h in custom.split(",") if h.strip()}
        return DEFAULT_ALLOWED_TEST_HOSTS | extra
    return DEFAULT_ALLOWED_TEST_HOSTS


def get_allowed_test_ports() -> frozenset[int]:
    """
    Get the set of permitted test database ports.
    Merges default ports with ALLOWED_TEST_DB_PORTS if configured.
    """
    custom = os.environ.get("ALLOWED_TEST_DB_PORTS", "").strip()
    if custom:
        extra: set[int] = set()
        for p in custom.split(","):
            p_clean = p.strip()
            if p_clean.isdigit():
                extra.add(int(p_clean))
        return DEFAULT_ALLOWED_TEST_PORTS | extra
    return DEFAULT_ALLOWED_TEST_PORTS


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

        host = parsed.hostname or "unknown-host"
        port = f":{parsed.port}" if parsed.port else ""
        masked_user = f"{parsed.username}:***@" if parsed.username else ""
        masked_netloc = f"{masked_user}{host}{port}"

        return urlunparse((
            parsed.scheme,
            masked_netloc,
            parsed.path,
            parsed.params,
            "",  # strip query to avoid leaking query parameters or tokens
            "",  # strip fragment
        ))
    except Exception:
        return "<sanitized-url>"


def sanitize_exception_message(
    exc_or_str: Exception | str,
    sentinels: list[str] | None = None,
) -> str:
    """
    Sanitize an exception message or diagnostic log string.
    Removes:
      - Raw database URLs with embedded credentials.
      - Key-value patterns like password=..., token=..., secret=...
      - Any explicit sentinel secret strings passed in sentinels.
    """
    raw_str = str(exc_or_str) if isinstance(exc_or_str, Exception) else str(exc_or_str)

    # 1. Redact URL credentials: scheme://user:password@host -> scheme://user:***@host
    sanitized = URL_CRED_PATTERN.sub(r'\1\2:***@', raw_str)

    # 2. Redact key-value password patterns
    sanitized = PASSWORD_PATTERN.sub(r'\1=***', sanitized)

    # 3. Redact explicit sentinels
    if sentinels:
        for s in sentinels:
            if s and len(s) > 1:
                sanitized = sanitized.replace(s, "***REDACTED***")

    return sanitized


def validate_and_sanitize_db_url(
    raw_url: str | None,
    mode: Literal["test", "operational_readonly"] = "test",
) -> str:
    """
    Parse and strictly validate a database connection URL and destination.

    Args:
        raw_url: The connection string to validate.
        mode: 'test' (enforces pevn_test_db and destination allowlist)
              'operational_readonly' (requires explicit opt-in and read-only enforcement).

    Returns:
        The validated connection string.

    Raises:
        DatabaseSecurityError: On any validation or destination policy failure.
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
    host = (parsed.hostname or "").lower()
    if not host:
        masked = mask_url_credentials(clean_url)
        raise DatabaseSecurityError(
            f"Database connection URL missing valid host. Target: {masked}"
        )

    # 3. Port validation (defaulting to 5432 if omitted)
    port = parsed.port if parsed.port is not None else 5432

    # 4. Destination Allowlist Enforcement
    if mode == "test":
        allowed_hosts = get_allowed_test_hosts()
        if host not in allowed_hosts:
            masked = mask_url_credentials(clean_url)
            raise DatabaseSecurityError(
                f"FAIL-CLOSED REJECTION: Unauthorized database host '{host}'. "
                f"Target host is not in the approved test destination allowlist: {sorted(allowed_hosts)}. "
                f"Target: {masked}"
            )

        allowed_ports = get_allowed_test_ports()
        if port not in allowed_ports:
            masked = mask_url_credentials(clean_url)
            raise DatabaseSecurityError(
                f"FAIL-CLOSED REJECTION: Unauthorized database port '{port}'. "
                f"Target port is not in the approved test destination allowlist: {sorted(allowed_ports)}. "
                f"Target: {masked}"
            )

    elif mode == "operational_readonly":
        # Operational diagnostics also restrict destination to approved local/container host
        allowed_hosts = get_allowed_test_hosts()
        if host not in allowed_hosts:
            masked = mask_url_credentials(clean_url)
            raise DatabaseSecurityError(
                f"FAIL-CLOSED REJECTION: Unauthorized operational diagnostic host '{host}'. "
                f"Operational diagnostics are only permitted on approved hosts: {sorted(allowed_hosts)}. "
                f"Target: {masked}"
            )

    # 5. Query Parameter Safety Validation
    if parsed.query:
        qs = parse_qs(parsed.query, keep_blank_values=True)
        for param in qs:
            if param.lower() in DISALLOWED_QUERY_PARAMS:
                masked = mask_url_credentials(clean_url)
                raise DatabaseSecurityError(
                    f"FAIL-CLOSED REJECTION: Disallowed connection query parameter '{param}' "
                    f"in database URL. Target: {masked}"
                )

    # 6. Database Name Extraction (Strict, no substring matching)
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

    # 7. Mode Enforcement
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
    Requires ALLOW_OPERATIONAL_DIAGNOSTICS=true.
    Prefers OPERATIONAL_READONLY_DATABASE_URL over DATABASE_URL.
    Enforces read-only connection parameters.
    """
    op_url = os.environ.get("OPERATIONAL_READONLY_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not op_url or not op_url.strip():
        raise DatabaseSecurityError(
            "FAIL-CLOSED: Neither OPERATIONAL_READONLY_DATABASE_URL nor DATABASE_URL is configured."
        )

    validated = validate_and_sanitize_db_url(op_url, mode="operational_readonly")

    # Enforce read-only transaction connection parameter if not already present
    parsed = urlparse(validated)
    query_parts = [parsed.query] if parsed.query else []
    if "default_transaction_read_only" not in parsed.query:
        query_parts.append("options=-c%20default_transaction_read_only=on")
    new_query = "&".join(filter(None, query_parts))
    enforced_url = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        parsed.fragment,
    ))

    if as_asyncpg:
        return (
            enforced_url.replace("postgresql+asyncpg://", "postgresql://")
                        .replace("postgresql+psycopg2://", "postgresql://")
        )
    else:
        if enforced_url.startswith("postgresql://"):
            return enforced_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        if enforced_url.startswith("postgres://"):
            return enforced_url.replace("postgres://", "postgresql+asyncpg://", 1)
        return enforced_url
