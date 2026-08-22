"""
PEVN Backend — Correlation ID Middleware

Assigns a unique correlation ID to every HTTP request.
The ID is propagated through:
  - The response header X-Correlation-ID (for client-side tracing)
  - The structured logging context (for server-side log correlation)
  - The context variable app.core.logging.correlation_id_ctx

Clients may provide their own correlation ID via the X-Correlation-ID
request header (useful for distributed tracing across services).
If no header is provided, a new UUID4 is generated.

Security:
  - Provided IDs are validated and truncated to prevent header injection.
  - IDs are not used for security decisions — only for observability.
"""

from __future__ import annotations

import re
from collections.abc import Awaitable, Callable
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import correlation_id_ctx

# Allowed characters in a correlation ID — alphanumeric and hyphens only
_SAFE_CORRELATION_ID_RE = re.compile(r"^[a-zA-Z0-9\-]{1,64}$")

CORRELATION_ID_HEADER = "X-Correlation-ID"


def _generate_correlation_id() -> str:
    """Generate a new UUID4 correlation ID."""
    return str(uuid4())


def _sanitize_correlation_id(value: str) -> str:
    """
    Validate and sanitize a client-provided correlation ID.

    Accepts only alphanumeric characters and hyphens, max 64 chars.
    If the provided value is invalid, a new ID is generated.
    """
    if value and _SAFE_CORRELATION_ID_RE.match(value):
        return value
    return _generate_correlation_id()


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """
    Starlette middleware that ensures every request has a correlation ID.

    Execution order (per request):
    1. Extract or generate correlation ID
    2. Set in context variable (for logging)
    3. Call the next middleware/handler
    4. Add correlation ID to the response headers

    This middleware should be positioned BEFORE the request logging
    middleware so that log records already contain the correlation ID.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        # Extract from request header or generate a new one
        provided = request.headers.get(CORRELATION_ID_HEADER, "")
        correlation_id = (
            _sanitize_correlation_id(provided)
            if provided
            else _generate_correlation_id()
        )

        # Set in context var — automatically propagated to all log records
        token = correlation_id_ctx.set(correlation_id)

        try:
            response: Response = await call_next(request)
        finally:
            # Always reset the context var after the request, even on errors
            correlation_id_ctx.reset(token)

        # Add the correlation ID to the response headers so clients can trace it
        response.headers[CORRELATION_ID_HEADER] = correlation_id
        return response
