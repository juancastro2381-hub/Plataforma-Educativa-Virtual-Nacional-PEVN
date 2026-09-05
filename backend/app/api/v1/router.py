"""
PEVN Backend — API v1 Router

Aggregates all v1 endpoint routers into a single router
that is included in the main application.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import (
    academic_assignments,
    academic_promotions,
    academic_years,
    analytics,
    auth,
    communications,
    enrollments,
    evaluation_grades,
    grades,
    groups,
    guardian_portal,
    guardians,
    health,
    incidents,
    institutions,
    news,
    ready,
    recordings,
    siee_policies,
    student_portal,
    students,
    subjects,
    teacher_portal,
    teachers,
    transfers,
    users,
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

# ---- Users endpoints ------------------------------------------------------
api_v1_router.include_router(
    users.router,
)

# ---- Institutional endpoints ----------------------------------------------
api_v1_router.include_router(
    institutions.router,
)

# ---- Academic Management endpoints (Phase 3B) -----------------------------
api_v1_router.include_router(
    grades.router,
)

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

api_v1_router.include_router(
    subjects.router,
)

# ---- Institutional Communications & Life (Phase 15) -----------------------
api_v1_router.include_router(
    communications.router,
)

api_v1_router.include_router(
    news.router,
)

api_v1_router.include_router(
    incidents.router,
)

# ---- Teacher Portal Endpoints (Phase 13D.5) -------------------------------
api_v1_router.include_router(
    teacher_portal.router,
)

# ---- Student Portal Endpoints (Phase 14A) ---------------------------------
api_v1_router.include_router(
    student_portal.router,
)

# ---- Guardian Portal Endpoints (Phase 14A) --------------------------------
api_v1_router.include_router(
    guardian_portal.router,
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

# ---- SIEE Evaluation, Report Cards & Promotion endpoints (Phase 16C) -------
api_v1_router.include_router(
    siee_policies.router,
)

api_v1_router.include_router(
    evaluation_grades.router,
)

api_v1_router.include_router(
    academic_promotions.router,
)
