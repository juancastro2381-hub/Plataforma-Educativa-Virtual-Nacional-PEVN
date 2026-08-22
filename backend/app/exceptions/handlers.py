"""
PEVN Backend — Global Exception Handlers

Provides centralized exception handling for the FastAPI application.
All unhandled exceptions are caught here and converted into
safe, predictable JSON responses.

Security principles enforced:
  - No stack traces in responses (especially in production)
  - No SQL error details exposed
  - No internal file paths exposed
  - No secrets or configuration values exposed
  - All errors include a correlation_id for server-side log correlation
  - Error verbosity is controlled by the application environment
"""

from __future__ import annotations

from typing import Any, cast

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import get_settings
from app.core.logging import correlation_id_ctx, get_logger
from app.exceptions.errors import PEVNException

logger = get_logger(__name__)


def _make_error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    details: list[dict[str, Any]] | None = None,
) -> JSONResponse:
    """
    Create a consistent JSON error response.

    Response format:
    {
      "error": {
        "code": "ERROR_CODE",
        "message": "Human-readable message",
        "correlation_id": "uuid-for-tracing",
        "details": [...]  // Only in development
      }
    }
    """
    settings = get_settings()
    correlation_id = correlation_id_ctx.get()

    body: dict[str, Any] = {
        "code": code,
        "message": message,
        "correlation_id": correlation_id,
    }

    # Include error details only in development to aid debugging.
    # Production responses must never expose internal details.
    if details and settings.is_development:
        body["details"] = details

    return JSONResponse(
        status_code=status_code,
        content={"error": body},
    )


async def pevn_exception_handler(request: Request, exc: PEVNException) -> JSONResponse:
    """Handle all PEVN application-level exceptions."""
    # Log at appropriate level based on status code
    if exc.status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
        logger.error(
            "Application error",
            error_code=exc.code,
            status_code=exc.status_code,
            path=request.url.path,
        )
    elif exc.status_code >= status.HTTP_400_BAD_REQUEST:
        logger.warning(
            "Client error",
            error_code=exc.code,
            status_code=exc.status_code,
            path=request.url.path,
        )

    return _make_error_response(
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Handle standard Starlette/FastAPI HTTP exceptions."""
    logger.info(
        "HTTP exception",
        status_code=exc.status_code,
        path=request.url.path,
    )

    return _make_error_response(
        status_code=exc.status_code,
        code=f"HTTP_{exc.status_code}",
        message=str(exc.detail) if exc.detail else "An error occurred",
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Handle request body/query validation failures from Pydantic.

    Converts Pydantic's verbose error format into the application's
    standard error structure. Details are only included in development.
    """
    logger.info(
        "Request validation failed",
        path=request.url.path,
        error_count=len(exc.errors()),
    )

    # Build safe validation error details (no internal paths exposed)
    details = [
        {
            "field": " → ".join(str(loc) for loc in err.get("loc", [])),
            "message": err.get("msg", "Invalid value"),
            "type": err.get("type", "value_error"),
        }
        for err in exc.errors()
    ]

    return _make_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        code="VALIDATION_ERROR",
        message="Request validation failed. Check the request and try again.",
        details=details,
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all handler for unexpected exceptions.

    SECURITY: Stack traces, SQL errors, and internal details are
    NEVER included in the response. They are logged server-side only.
    """
    correlation_id = correlation_id_ctx.get()

    # Log the full exception server-side for debugging
    logger.exception(
        "Unhandled exception",
        path=request.url.path,
        method=request.method,
        error_type=type(exc).__name__,
        correlation_id=correlation_id,
    )

    return _make_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="INTERNAL_ERROR",
        message="An unexpected error occurred. Please try again later.",
    )


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register all exception handlers with the FastAPI application.

    Call this once during application creation in main.py.
    """
    app.add_exception_handler(PEVNException, cast(Any, pevn_exception_handler))
    app.add_exception_handler(StarletteHTTPException, cast(Any, http_exception_handler))
    app.add_exception_handler(
        RequestValidationError, cast(Any, validation_exception_handler)
    )
    app.add_exception_handler(Exception, unhandled_exception_handler)
