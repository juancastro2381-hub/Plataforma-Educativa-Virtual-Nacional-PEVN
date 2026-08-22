"""
PEVN Backend — Health Endpoint (Liveness Probe)

Returns HTTP 200 if the application process is running.
This endpoint does not check database or Redis connectivity.
Use /api/v1/ready for dependency readiness checks.

Difference from /ready:
  - /health: Is the process alive and responding?
  - /ready: Is the application ready to serve traffic (dependencies OK)?
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    """Health check response payload."""

    status: str
    service: str

    model_config = {
        "json_schema_extra": {"example": {"status": "ok", "service": "pevn-backend"}}
    }


@router.get(
    "",
    response_model=HealthResponse,
    summary="Application Health Check (Liveness)",
    description=(
        "Returns HTTP 200 when the service is running. "
        "Used by container orchestrators (Docker, Kubernetes) for liveness probes."
    ),
)
async def get_health() -> HealthResponse:
    """Return health status."""
    return HealthResponse(status="ok", service="pevn-backend")
