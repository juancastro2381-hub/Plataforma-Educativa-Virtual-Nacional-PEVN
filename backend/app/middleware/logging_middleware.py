"""
PEVN Backend — Request Logging Middleware

Logs every HTTP request and response with structured metadata.
Emits structured JSON in production and readable console logs in development.

Metadata captured:
  - correlation_id: For end-to-end request tracing
  - method: HTTP method (GET, POST, etc.)
  - path: Request path (sanitized of sensitive query params)
  - status_code: HTTP response status code
  - duration_ms: Request processing time in milliseconds
  - client_ip: Client IP address (from headers or connection)

SECURITY:
  - Request/response bodies are NOT logged (may contain PII/credentials)
  - Authorization headers are NOT logged
  - Sensitive paths (e.g. /auth/login) have query params stripped
"""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable

from fastapi import status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import correlation_id_ctx, get_logger

logger = get_logger(__name__)

# Paths to suppress from logging (high-frequency health checks)
_SUPPRESSED_PATHS = frozenset(
    {
        "/api/v1/health",
        "/favicon.ico",
    }
)

_SENSITIVE_PATH_PREFIXES = ("/auth/", "/login", "/password", "/reset")


def _get_client_ip(request: Request) -> str:
    """Extract client IP, respecting X-Forwarded-For if set by reverse proxy."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _sanitize_path_for_logging(path: str) -> str:
    """
    Sanitize the request path before logging.
    For authentication-related endpoints, ensure no query params are logged.
    """
    if any(path.startswith(prefix) for prefix in _SENSITIVE_PATH_PREFIXES):
        return path.split("?", maxsplit=1)[0]
    return path


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Starlette middleware for structured request/response logging.
    Logs request completion time, status code, and correlation ID.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        start_time = time.perf_counter()
        path = request.url.path
        method = request.method
        client_ip = _get_client_ip(request)
        correlation_id = correlation_id_ctx.get()

        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

            if path not in _SUPPRESSED_PATHS:
                if status_code >= status.HTTP_400_BAD_REQUEST:
                    log_fn = logger.warning
                elif status_code >= status.HTTP_200_OK:
                    log_fn = logger.info
                else:
                    log_fn = logger.debug

                log_fn(
                    "Request completed",
                    method=method,
                    path=_sanitize_path_for_logging(path),
                    status_code=status_code,
                    duration_ms=duration_ms,
                    client_ip=client_ip,
                    correlation_id=correlation_id,
                )
