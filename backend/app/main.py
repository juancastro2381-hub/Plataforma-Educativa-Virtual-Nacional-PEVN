"""
PEVN Backend — FastAPI Application Factory

This module creates and configures the FastAPI application instance.
The `app` variable at the bottom is the ASGI entry point for:
  - uvicorn: `uvicorn app.main:app`
  - gunicorn: `gunicorn app.main:app -k uvicorn.workers.UvicornWorker`

Architecture:
  - Lifespan: async context manager for startup/shutdown logic
  - Middleware: applied in correct order (last added = outermost layer)
  - Exception handlers: centralized, safe, no internal details exposed
  - Router: versioned API namespace (/api/v1)
  - OpenAPI: disabled in production

Middleware execution order (outermost → innermost for requests):
  TrustedHost → CORS → SecurityHeaders → CorrelationID → RequestLogging → Handler

For response processing, this order is reversed.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1.router import api_v1_router
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.db.session import close_engine, get_engine
from app.exceptions.handlers import register_exception_handlers
from app.middleware.correlation import CorrelationIDMiddleware
from app.middleware.logging_middleware import RequestLoggingMiddleware
from app.middleware.security import SecurityHeadersMiddleware


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context manager.

    Handles startup and shutdown logic in a single, clean function.
    Replaces the deprecated @app.on_event("startup") pattern.

    Startup:
      1. Configure structured logging
      2. Log startup event with environment info
      3. Warm up the database connection pool
      4. Verify database connectivity

    Shutdown:
      1. Log shutdown event
      2. Dispose of database connection pool
    """
    settings = get_settings()

    # ---- Startup ----------------------------------------------------------
    configure_logging(
        log_level=settings.LOG_LEVEL,
        log_format=settings.LOG_FORMAT,
    )

    logger = get_logger(__name__)
    logger.info(
        "Starting PEVN backend",
        service="pevn-backend",
        version=settings.PROJECT_VERSION,
        environment=settings.ENVIRONMENT,
        # Never log SECRET_KEY, DATABASE_URL, or REDIS_URL directly
        database=settings.get_safe_database_url(),
        debug=settings.DEBUG,
    )

    # Warm up the database connection pool on startup
    # This catches misconfigured DATABASE_URL before the first request
    try:
        _ = get_engine()
        logger.info("Database connection pool initialized")
    except Exception as exc:
        logger.error(
            "Failed to initialize database connection pool",
            error_type=type(exc).__name__,
            # Safe URL only (password masked)
            database=settings.get_safe_database_url(),
        )
        # Do not raise — allow the app to start and report via /ready

    # ---- Application runs here -------------------------------------------
    yield

    # ---- Shutdown ---------------------------------------------------------
    logger.info("Shutting down PEVN backend")
    await close_engine()
    logger.info("Shutdown complete")


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.

    This factory function is used both for the production app instance
    and for creating isolated instances in tests.

    Returns:
        A fully configured FastAPI application instance.
    """
    settings = get_settings()

    application = FastAPI(
        title=settings.PROJECT_NAME,
        description=(
            "Plataforma Educativa Virtual Nacional — API v1\n\n"
            "Backend service for the Colombian National Virtual Educational Platform. "
            "Provides institutional management, academic coordination, and educational "
            "services."
        ),
        version=settings.PROJECT_VERSION,
        openapi_url=settings.OPENAPI_URL,
        docs_url=settings.DOCS_URL,
        redoc_url=settings.REDOC_URL,
        lifespan=lifespan,
        # Disable the default 422 validation error handler
        # (we replace it with our own in register_exception_handlers)
        generate_unique_id_function=lambda route: (
            f"{route.tags[0]}-{route.name}" if route.tags else route.name
        ),
    )

    # ---- Exception Handlers -----------------------------------------------
    # Must be registered before middleware so they handle errors at all layers
    register_exception_handlers(application)

    # ---- Middleware --------------------------------------------------------
    # IMPORTANT: Middleware is added in LIFO order by Starlette.
    # The LAST add_middleware call wraps the outermost layer.
    # Request flow: last added → ... → first added → route handler
    # Response flow: route handler → first added → ... → last added

    # Innermost: request logging (measures actual handler time)
    application.add_middleware(RequestLoggingMiddleware)

    # Correlation ID (must be set before logging middleware sees the request)
    application.add_middleware(CorrelationIDMiddleware)

    # Security headers (applied to all responses)
    application.add_middleware(SecurityHeadersMiddleware)

    # Trusted host validation (rejects bad Host headers)
    allowed_hosts = (
        settings.ALLOWED_HOSTS
        if isinstance(settings.ALLOWED_HOSTS, list)
        else [settings.ALLOWED_HOSTS]
    )
    application.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=allowed_hosts,
    )

    # Outermost: CORS — handles preflight OPTIONS and allows credentials from frontend
    cors_origins = (
        settings.CORS_ORIGINS
        if isinstance(settings.CORS_ORIGINS, list)
        else [settings.CORS_ORIGINS]
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )

    # ---- Routes -----------------------------------------------------------
    application.include_router(
        api_v1_router,
        prefix=settings.API_V1_PREFIX,
    )

    return application


# ---------------------------------------------------------------------------
# Module-level application instance
# ---------------------------------------------------------------------------
# This is the entry point for uvicorn and gunicorn:
#   uvicorn app.main:app --host 0.0.0.0 --port 8000
#   gunicorn app.main:app -k uvicorn.workers.UvicornWorker -w 4
#
# Note: get_settings() is called here to validate configuration at import time.
# Any configuration errors will surface immediately on startup.
# ---------------------------------------------------------------------------
app: FastAPI = create_application()
