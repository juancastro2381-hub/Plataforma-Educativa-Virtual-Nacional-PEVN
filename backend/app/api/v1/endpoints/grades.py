"""
PEVN Backend — Grades API Endpoints

REST Controller for querying the standardized national Grade catalog (MEN).
Protected by the existing 'grades:read' RBAC permission.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy import select

from app.api.deps import (
    SessionDep,
    require_permission,
)
from app.models.grade import Grade
from app.schemas.academic import (
    GradeListResponse,
    GradeResponse,
)

router = APIRouter(prefix="/grades", tags=["Grades"])


@router.get(
    "",
    response_model=GradeListResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar catálogo nacional de grados",
    description="Devuelve el catálogo nacional estandarizado de grados curriculares (MEN) ordenados por nivel.",
    dependencies=[Depends(require_permission("grades", "read"))],
)
async def list_grades(
    db: SessionDep,
) -> GradeListResponse:
    """
    List all standardized national grades ordered by ordinal_order ascending.
    """
    query = select(Grade).order_by(Grade.ordinal_order.asc())
    result = await db.execute(query)
    grades = list(result.scalars().all())

    return GradeListResponse(
        items=[GradeResponse.model_validate(g) for g in grades],
        total=len(grades),
    )
