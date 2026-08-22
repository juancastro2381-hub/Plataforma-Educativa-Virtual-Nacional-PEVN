"""
PEVN Backend — API v1 Router

Aggregates all v1 endpoint routers into a single router
that is included in the main application.

Adding new endpoints:
  1. Create a new module in app/api/v1/endpoints/
  2. Define a router in that module
  3. Include it here with an appropriate prefix and tags
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import health, ready

api_v1_router = APIRouter()

# ---- Operational endpoints ------------------------------------------------
api_v1_router.include_router(
    health.router,
    prefix="/health",
    tags=["Operations"],
)

api_v1_router.include_router(
    ready.router,
    prefix="/ready",
    tags=["Operations"],
)

# ---- Future Phase 2+ endpoints (not yet implemented) ----------------------
# api_v1_router.include_router(
#     auth.router, prefix="/auth", tags=["Authentication"]
# )
# api_v1_router.include_router(
#     users.router, prefix="/users", tags=["Users"]
# )
# api_v1_router.include_router(
#     institutions.router, prefix="/institutions", tags=["Institutions"]
# )
