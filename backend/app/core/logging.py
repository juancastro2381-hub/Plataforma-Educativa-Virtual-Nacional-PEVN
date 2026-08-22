"""
PEVN Backend — Structured Logging Configuration

Uses structlog for machine-readable JSON logging in production
and human-readable colored output in development.

SECURITY POLICY — NEVER LOG:
  - Passwords or authentication credentials
  - JWT tokens, session identifiers, or API keys
  - Authorization header values (Bearer tokens)
  - Raw database connection strings with credentials
  - Any field named 'password', 'token', 'secret', 'key', 'credential'
  - Full request/response bodies (may contain sensitive PII)
  - Personal identification numbers (cédula, NIT, etc.)

Log records include a correlation_id for request tracing.
See middleware/correlation.py for how correlation IDs are set.
"""

from __future__ import annotations

import logging
import sys
from contextvars import ContextVar
from typing import Any, cast

import structlog
from structlog.types import EventDict

# ---------------------------------------------------------------------------
# Context variable for correlation ID
# ---------------------------------------------------------------------------
# This ContextVar is set per-request by CorrelationIDMiddleware and
# automatically propagates through asyncio tasks within that request context.
correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="-")

# Sensitive keys to redact automatically
_SENSITIVE_KEYS: frozenset[str] = frozenset(
    {
        "password",
        "passwd",
        "secret",
        "token",
        "api_key",
        "apikey",
        "authorization",
        "auth",
        "credential",
        "credentials",
        "private_key",
        "access_key",
        "secret_key",
    }
)


# ---------------------------------------------------------------------------
# Custom structlog processors
# ---------------------------------------------------------------------------


def _add_correlation_id(logger: Any, method: str, event_dict: EventDict) -> EventDict:
    """Inject the current request correlation ID into every log record."""
    event_dict["correlation_id"] = correlation_id_ctx.get()
    return event_dict


def _drop_color_message(logger: Any, method: str, event_dict: EventDict) -> EventDict:
    """Remove the 'color_message' key injected by uvicorn's logger."""
    event_dict.pop("color_message", None)
    return event_dict


def _sanitize_sensitive_fields(
    logger: Any, method: str, event_dict: EventDict
) -> EventDict:
    """
    Redact known sensitive field names from log records.
    This is a defense-in-depth measure — code should never pass these
    fields to the logger in the first place.
    """
    for key in _SENSITIVE_KEYS:
        if key in event_dict:
            event_dict[key] = "***REDACTED***"
    return event_dict


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def configure_logging(log_level: str = "INFO", log_format: str = "console") -> None:
    """
    Configure structlog for the application.

    Must be called once during application startup, before any loggers are used.

    Args:
        log_level: Python log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_format: Output format — 'json' for production, 'console' for development.
    """
    level_num = getattr(logging, log_level.upper(), logging.INFO)

    shared_processors: list[structlog.types.Processor] = [
        # Merge any bound context vars (used by structlog.contextvars.bind_contextvars)
        structlog.contextvars.merge_contextvars,
        # Standard processors
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        # Custom processors
        _add_correlation_id,
        _sanitize_sensitive_fields,
        _drop_color_message,
        # Format positional arguments
        structlog.stdlib.PositionalArgumentsFormatter(),
        # Include stack info when requested
        structlog.processors.StackInfoRenderer(),
    ]

    if log_format == "json":
        # Production: machine-readable JSON for log aggregation systems
        final_processors: list[structlog.types.Processor] = [
            *shared_processors,
            structlog.processors.ExceptionRenderer(),
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Development: human-readable colored console output
        final_processors = [
            *shared_processors,
            structlog.dev.ConsoleRenderer(
                colors=True,
                sort_keys=False,
                exception_formatter=structlog.dev.plain_traceback,
            ),
        ]

    structlog.configure(
        processors=final_processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure stdlib logging to route through structlog.
    # This ensures uvicorn access logs and other stdlib loggers
    # are captured in the same format.
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level_num,
        force=True,
    )

    # Suppress noisy third-party loggers in non-debug mode
    if level_num > logging.DEBUG:
        logging.getLogger("asyncio").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """
    Return a bound structlog logger.

    Args:
        name: Optional logger name (typically __name__ of the calling module).

    Returns:
        A structlog BoundLogger with the correlation_id already bound via context var.

    Example:
        logger = get_logger(__name__)
        logger.info("User action completed", user_id=user.id, action="login")
    """
    return cast(structlog.stdlib.BoundLogger, structlog.get_logger(name))
