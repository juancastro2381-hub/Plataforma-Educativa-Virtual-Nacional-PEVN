"""
PEVN Backend - Academic Promotion & Graduation API Endpoints (Phase 16C)

REST controller for:
  - GET  /promotions/preview -> promotions:preview (Calculate proposed promotion outcomes)
  - POST /promotions/commit  -> promotions:execute (Commit official Promotion Act)

Enforces:
  - Strict multi-tenant isolation
  - PROMOVIDO != GRADUADO semantic invariant (DECISION-16-04)
  - Full audit logging of committed acts
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import (
    AuditServiceDep,
    AuthContextDep,
    CurrentUserDep,
    SessionDep,
    require_permission,
)
from app.core.security.interfaces import SystemRole
from app.exceptions.errors import AuthorizationError
from app.schemas.evaluation import (
    CommitGroupPromotionsRequest,
    CommitGroupPromotionsResponse,
    PromotionPreviewResponse,
    StudentPromotionResponse,
)
from app.services.academic_promotion_service import AcademicPromotionService

router = APIRouter(prefix="/promotions", tags=["Academic Promotions"])


def _resolve_institution_id(
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    institution_id_override: uuid.UUID | None = None,
) -> uuid.UUID:
    """Resolve institution_id from authenticated context."""
    if (
        SystemRole.SUPERADMIN in auth.roles
        or SystemRole.NATIONAL_ADMIN in auth.roles
        or auth.scope.is_national()
    ) and institution_id_override:
        return institution_id_override
    if current_user.institution_id:
        return current_user.institution_id
    raise AuthorizationError("Contexto institucional no disponible.")


@router.get(
    "/preview",
    response_model=PromotionPreviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Calcular propuesta de promocion escolar de grupo",
    description=(
        "Calcula y previsualiza el dictamen de promocion propuesto para cada estudiante "
        "del grupo segun la politica SIEE activa de la institucion."
    ),
    dependencies=[Depends(require_permission("promotions", "preview"))],
)
async def calculate_promotion_preview(
    group_id: Annotated[uuid.UUID, Query(description="ID del grupo")],
    academic_year_id: Annotated[uuid.UUID, Query(description="ID del ano lectivo")],
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override institucional (solo SuperAdmin / NationalAdmin)"),
    ] = None,
) -> PromotionPreviewResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    svc = AcademicPromotionService(session=db)
    preview = await svc.calculate_promotion_preview(
        institution_id=target_institution_id,
        group_id=group_id,
        academic_year_id=academic_year_id,
    )
    return PromotionPreviewResponse.model_validate(preview)


@router.post(
    "/commit",
    response_model=CommitGroupPromotionsResponse,
    status_code=status.HTTP_200_OK,
    summary="Asentar acta oficial de promocion y evaluacion",
    description=(
        "Asienta de forma inmutable el acta de promocion del grupo. "
        "PROMOVIDO mantiene la matricula en ACTIVE. Solo GRADUADO (grado 11) transiciona a GRADUATED."
    ),
    dependencies=[Depends(require_permission("promotions", "execute"))],
)
async def commit_group_promotions(
    payload: CommitGroupPromotionsRequest,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override institucional (solo SuperAdmin / NationalAdmin)"),
    ] = None,
) -> CommitGroupPromotionsResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    svc = AcademicPromotionService(session=db)
    decisions_dicts = [d.model_dump() for d in payload.decisions]
    records = await svc.commit_group_promotions(
        institution_id=target_institution_id,
        group_id=payload.group_id,
        academic_year_id=payload.academic_year_id,
        acta_number=payload.acta_number,
        decision_date=payload.decision_date,
        decisions=decisions_dicts,
        user_id=current_user.id,
        observations=payload.observations,
    )
    await db.commit()
    records_resp = [StudentPromotionResponse.model_validate(r) for r in records]
    return CommitGroupPromotionsResponse(
        committed_count=len(records),
        group_id=payload.group_id,
        academic_year_id=payload.academic_year_id,
        acta_number=payload.acta_number,
        records=records_resp,
    )
