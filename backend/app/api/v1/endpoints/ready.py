"""
PEVN Backend — Readiness Endpoint

GET /api/v1/ready

Returns the application's readiness to serve traffic.
Checks all required infrastructure dependencies (DB, Redis).

Returns:
  200: Application is ready — all checks passed.
  503: Application is not ready — one or more checks failed.

Security:
  - Does NOT expose connection strings, credentials, or internal paths.
  - Check results are limited to "ok" or "error" — no technical details.
  - Does NOT require authentication (needed by infrastructure probes).
  - Rate limiting: this endpoint may be probed frequently by orchestration;
    do not perform expensive operations here.
"""

from __future__ import annotations

import redis.asyncio as aioredis
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.health import check_database_connectivity

router = APIRouter()
_logger = get_logger(__name__)


class CheckResult(BaseModel):
    """Result of a single dependency check."""

    status: str  # "ok" | "error"


class ReadinessResponse(BaseModel):
    """Readiness check response payload."""

    status: str  # "ready" | "not_ready"
    checks: dict[str, str]

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "ready",
                "checks": {
                    "database": "ok",
                    "redis": "ok",
                },
            }
        }
    }


@router.get(
    "",
    response_model=ReadinessResponse,
    summary="Application readiness check",
    description=(
        "Returns 200 if all infrastructure dependencies are available. "
        "Returns 503 if any dependency is unavailable. "
        "Used by container orchestration to determine if traffic should be routed here."
    ),
    responses={
        200: {"description": "Application is ready to serve traffic"},
        503: {"description": "Application is not ready — dependency check failed"},
    },
)
async def readiness_check() -> JSONResponse:
    """
    Readiness probe endpoint.

    Verifies connectivity to:
      - PostgreSQL (required for all operations)
      - Redis (checked for connectivity; graceful degradation may apply)
    """
    checks: dict[str, str] = {}
    all_ready = True

    # ---- Database check ---------------------------------------------------
    db_ok, _ = await check_database_connectivity()
    checks["database"] = "ok" if db_ok else "error"
    if not db_ok:
        all_ready = False

    # ---- Redis check ------------------------------------------------------
    redis_ok = await _check_redis_connectivity()
    checks["redis"] = "ok" if redis_ok else "error"
    if not redis_ok:
        all_ready = False

    overall_status = "ready" if all_ready else "not_ready"
    http_status = (
        status.HTTP_200_OK if all_ready else status.HTTP_503_SERVICE_UNAVAILABLE
    )

    return JSONResponse(
        status_code=http_status,
        content={
            "status": overall_status,
            "checks": checks,
        },
    )


async def _check_redis_connectivity() -> bool:
    """
    Check Redis connectivity.

    Returns True if Redis is reachable, False otherwise.
    Errors are logged but never exposed in the response.
    """
    try:
        settings = get_settings()

        client = aioredis.from_url(
            settings.REDIS_URL,
            socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
            socket_connect_timeout=settings.REDIS_CONNECT_TIMEOUT,
        )
        await client.ping()
        await client.aclose()
        return True

    except Exception as exc:
        _logger.error(
            "Redis connectivity check failed",
            error_type=type(exc).__name__,
        )
        return False
