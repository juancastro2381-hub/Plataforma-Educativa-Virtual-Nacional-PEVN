"""
PEVN Backend — Security Headers Middleware

Applies HTTP security headers to every response.
These headers implement defense-in-depth at the HTTP transport layer.

Headers applied:
  - X-Content-Type-Options: nosniff
  - X-Frame-Options: DENY
  - Referrer-Policy: strict-origin-when-cross-origin
  - Permissions-Policy: (restrictive)
  - Cross-Origin-Opener-Policy: same-origin
  - Cross-Origin-Resource-Policy: same-origin
  - X-XSS-Protection: 0
  - Content-Security-Policy: (environment-appropriate)
  - Strict-Transport-Security: (staging/production only)

See app.core.security.headers for header value documentation.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from app.core.config import get_settings
from app.core.security.headers import build_security_headers


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Applies configured security headers to all HTTP responses.

    Headers are built once at class instantiation and cached,
    since they only depend on static configuration.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        settings = get_settings()
        self._security_headers = build_security_headers(settings)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response: Response = await call_next(request)

        # Apply security headers to the response
        # Avoid overriding headers already explicitly set
        for header_name, header_value in self._security_headers.items():
            if header_name not in response.headers:
                response.headers[header_name] = header_value

        return response
