"""
PEVN Backend — API v1 Router

Aggregates all v1 endpoint routers into a single router
that is included in the main application.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import (
    academic_assignments,
    academic_years,
    analytics,
    auth,
    enrollments,
    groups,
    guardians,
    health,
    institutions,
    ready,
    recordings,
    students,
    teachers,
    transfers,
    virtual_classrooms,
)

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

# ---- Authentication endpoints ---------------------------------------------
api_v1_router.include_router(
    auth.router,
)

# ---- Institutional endpoints ----------------------------------------------
api_v1_router.include_router(
    institutions.router,
)

# ---- Academic Management endpoints (Phase 3B) -----------------------------
api_v1_router.include_router(
    academic_years.router,
)

api_v1_router.include_router(
    groups.router,
)

api_v1_router.include_router(
    students.router,
)

api_v1_router.include_router(
    teachers.router,
)

api_v1_router.include_router(
    guardians.router,
)

api_v1_router.include_router(
    enrollments.router,
)

api_v1_router.include_router(
    transfers.router,
)

api_v1_router.include_router(
    academic_assignments.router,
)

# ---- Virtual Classrooms & Recordings endpoints (Phase 4) ------------------
api_v1_router.include_router(
    virtual_classrooms.router,
)

api_v1_router.include_router(
    recordings.router,
)

# ---- Territorial Analytics endpoints (Phase 7 Step 4) ---------------------
api_v1_router.include_router(
    analytics.router,
)
