"""
PEVN Backend - SIEE Policy Management API Endpoints (Phase 16C)

REST controller for institutional evaluation policy (SIEE) configuration,
versioning, and historical audit trail.

Authorization:
  GET  /siee-policies/active               -> evaluations:read (all institutional actors)
  GET  /siee-policies/history              -> siee_policies:read
  POST /siee-policies                      -> siee_policies:manage (Rector/Coordinator/Admin)

Multi-tenant: institution_id is always resolved from the authenticated user's context.
SuperAdmin and National Admin may override institution_id via query parameter.
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
    SieePolicyCreateRequest,
    SieePolicyHistoryResponse,
    SieePolicyResponse,
)
from app.services.siee_policy_service import SieePolicyService

router = APIRouter(prefix="/siee-policies", tags=["SIEE Policies"])


def _resolve_institution_id(
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    institution_id_override: uuid.UUID | None = None,
) -> uuid.UUID:
    """
    Resolve institution_id from authenticated context.
    SuperAdmin / NationalAdmin may supply an override for cross-institution operations.
    """
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
    "/active",
    response_model=SieePolicyResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener politica SIEE activa",
    description=(
        "Resuelve y retorna la politica SIEE institucional activa para el ano lectivo indicado. "
        "Si no existe, crea automaticamente la politica estandar nacional."
    ),
    dependencies=[Depends(require_permission("evaluations", "read"))],
)
async def get_active_siee_policy(
    academic_year_id: Annotated[uuid.UUID, Query(description="ID del ano lectivo")],
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override institucional (solo SuperAdmin / NationalAdmin)"),
    ] = None,
) -> SieePolicyResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    svc = SieePolicyService(session=db)
    policy = await svc.get_or_create_default_policy(
        institution_id=target_institution_id,
        academic_year_id=academic_year_id,
        user_id=current_user.id,
    )
    await db.commit()
    return SieePolicyResponse.model_validate(policy)


@router.get(
    "/history",
    response_model=SieePolicyHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Historial de versiones de la politica SIEE",
    description="Lista todas las versiones (activas e historicas) de la politica SIEE para auditoria.",
    dependencies=[Depends(require_permission("siee_policies", "read"))],
)
async def list_siee_policy_history(
    academic_year_id: Annotated[uuid.UUID, Query(description="ID del ano lectivo")],
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override institucional (solo SuperAdmin / NationalAdmin)"),
    ] = None,
) -> SieePolicyHistoryResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    svc = SieePolicyService(session=db)
    versions = await svc.list_policy_history(
        institution_id=target_institution_id,
        academic_year_id=academic_year_id,
    )
    items = [SieePolicyResponse.model_validate(p) for p in versions]
    return SieePolicyHistoryResponse(items=items, total=len(items))


@router.post(
    "",
    response_model=SieePolicyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nueva version de politica SIEE",
    description=(
        "Publica una nueva version de la politica SIEE institucional. "
        "La version anterior queda inactiva de forma inmutable (audit trail)."
    ),
    dependencies=[Depends(require_permission("siee_policies", "manage"))],
)
async def create_siee_policy_version(
    payload: SieePolicyCreateRequest,
    academic_year_id: Annotated[uuid.UUID, Query(description="ID del ano lectivo")],
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override institucional (solo SuperAdmin / NationalAdmin)"),
    ] = None,
) -> SieePolicyResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    svc = SieePolicyService(session=db)
    new_policy = await svc.create_policy_version(
        institution_id=target_institution_id,
        academic_year_id=academic_year_id,
        data=payload.model_dump(exclude_none=False),
        user_id=current_user.id,
    )
    await db.commit()
    return SieePolicyResponse.model_validate(new_policy)
