"""
PEVN Backend — HTTP Security Header Configuration

Defines the security headers applied to all API responses.
These headers implement a defense-in-depth strategy at the HTTP layer.

References:
  - OWASP Secure Headers Project: https://owasp.org/www-project-secure-headers/
  - MDN HTTP Headers: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers
  - Mozilla Observatory: https://observatory.mozilla.org/
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.config import Settings


def build_security_headers(settings: Settings) -> dict[str, str]:
    """
    Build the security headers dict to be applied to all HTTP responses.

    Headers vary slightly by environment:
    - HSTS is only sent in staging/production (not development, since HTTP is used).
    - CSP is stricter in production.

    Args:
        settings: Application settings instance.

    Returns:
        A dictionary of header name → header value.
    """
    headers: dict[str, str] = {}

    # ---- Prevent MIME type sniffing ----------------------------------------
    # Prevents browsers from interpreting files as a different MIME type,
    # which can lead to XSS via content-type confusion.
    headers["X-Content-Type-Options"] = "nosniff"

    # ---- Prevent clickjacking -----------------------------------------------
    # Prevents the page from being embedded in an iframe.
    # Use SAMEORIGIN if embedding in your own pages is needed.
    headers["X-Frame-Options"] = "DENY"

    # ---- Referrer Policy ----------------------------------------------------
    # Controls what information is sent in the Referer header.
    # strict-origin-when-cross-origin: sends origin only for cross-origin requests.
    headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # ---- Permissions Policy -------------------------------------------------
    # Restricts which browser features the application can use.
    # Minimized to reduce attack surface. Add only what is actually needed.
    headers["Permissions-Policy"] = (
        "camera=(), "
        "microphone=(), "
        "geolocation=(), "
        "payment=(), "
        "usb=(), "
        "interest-cohort=()"  # Opt out of FLoC / Privacy Sandbox targeting
    )

    # ---- Cross-Origin Policies ----------------------------------------------
    # Mitigates Spectre-class side-channel attacks.
    headers["Cross-Origin-Opener-Policy"] = "same-origin"
    headers["Cross-Origin-Resource-Policy"] = "same-origin"

    # ---- Disable legacy XSS filter ------------------------------------------
    # Modern recommendation: disable the browser's built-in XSS filter
    # and rely on Content-Security-Policy instead.
    # Setting to "0" prevents the filter from introducing new vulnerabilities.
    headers["X-XSS-Protection"] = "0"

    # ---- Content Security Policy --------------------------------------------
    # Primary XSS defense mechanism.
    # Phase 1: permissive baseline that can be tightened per-environment.
    # Production will require a strict policy review before go-live.
    csp = _build_csp(settings)
    headers["Content-Security-Policy"] = csp

    # ---- HTTP Strict Transport Security (HSTS) ------------------------------
    # ONLY sent in non-development environments (HTTPS required).
    # Tells browsers to always use HTTPS for this domain.
    # WARNING: Do not enable in development — will break HTTP access.
    if not settings.is_development:
        headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
            # Note: Do NOT add 'preload' until the domain is registered
            # in the HSTS preload list and HTTPS is fully deployed.
        )

    return headers


def _build_csp(settings: Settings) -> str:
    """Build the Content-Security-Policy header value."""
    cors_list = (
        settings.CORS_ORIGINS
        if isinstance(settings.CORS_ORIGINS, list)
        else [settings.CORS_ORIGINS]
    )

    directives: list[str] = [
        "default-src 'self'",
        # Scripts: only from self — no inline scripts
        "script-src 'self'",
        # Styles: self + Google Fonts CDN (used by the design system)
        # unsafe-inline required for Tailwind CSS runtime generation in development
        # Phase 2+: remove unsafe-inline and use nonces or hashes
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
        # Fonts: self + Google Fonts CDN
        "font-src 'self' https://fonts.gstatic.com",
        # Images: self + data URIs (for inline SVG/icon data URLs)
        "img-src 'self' data:",
        # API connections to self and the backend origin
        f"connect-src 'self' {' '.join(cors_list)}",
        # Media: none by default (will be expanded for BigBlueButton in Phase 3)
        "media-src 'none'",
        # Objects/plugins: none
        "object-src 'none'",
        # Frames: deny embedding
        "frame-ancestors 'none'",
        # Form actions: self only
        "form-action 'self'",
        # Base tag: restrict to self
        "base-uri 'self'",
        # Block mixed content
        "upgrade-insecure-requests" if not settings.is_development else "",
    ]

    return "; ".join(d for d in directives if d)
