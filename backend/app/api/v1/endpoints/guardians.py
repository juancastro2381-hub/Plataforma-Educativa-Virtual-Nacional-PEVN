"""
PEVN Backend — Guardians API Endpoints

REST Controller for legal guardians (Acudientes) and student-guardian associations,
supporting decoupled national identity per [OPEN-DECISION-3A-01] and delegating
business rules to GuardianService.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select

from app.api.deps import (
    AuthContextDep,
    ClientIpDep,
    CurrentUserDep,
    SessionDep,
    require_permission,
)
from app.core.logging import correlation_id_ctx
from app.core.security.interfaces import SystemRole
from app.exceptions.errors import AuthorizationError
from app.models.guardian import Guardian
from app.schemas.academic import (
    AssociateGuardianRequest,
    GuardianCreateRequest,
    GuardianListResponse,
    GuardianResponse,
    StudentGuardianResponse,
)
from app.services.guardian_service import GuardianService

router = APIRouter(prefix="/guardians", tags=["Guardians"])


def _resolve_institution_id(
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    institution_id_override: uuid.UUID | None = None,
) -> uuid.UUID:
    """Resolve active institution context adhering to tenant isolation."""
    if (
        SystemRole.SUPERADMIN in auth.roles
        or SystemRole.NATIONAL_ADMIN in auth.roles
        or auth.scope.is_national()
    ) and institution_id_override:
        return institution_id_override
    if current_user.institution_id:
        return current_user.institution_id
    raise AuthorizationError("Contexto institucional no disponible.")


@router.post(
    "",
    response_model=GuardianResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar acudiente",
    description="Crea un registro de acudiente (OPEN-DECISION-3A-01).",
    dependencies=[Depends(require_permission("guardians", "create"))],
)
async def create_guardian(
    payload: GuardianCreateRequest,
    db: SessionDep,
    current_user: CurrentUserDep,
    client_ip: ClientIpDep,
) -> GuardianResponse:
    correlation_id = correlation_id_ctx.get()

    service = GuardianService(session=db)
    guardian = await service.create_guardian(
        first_name=payload.first_name,
        last_name=payload.last_name,
        document_type=payload.document_type,
        document_number=payload.document_number,
        phone=payload.phone,
        email=payload.email,
        address=payload.address,
        relationship_type=payload.relationship_type,
        user_id=payload.user_id,
        actor_id=current_user.id,
        actor_ip=client_ip,
        correlation_id=correlation_id,
    )
    await db.commit()
    await db.refresh(guardian)
    return GuardianResponse.model_validate(guardian)


@router.get(
    "/{guardian_id}",
    response_model=GuardianResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar acudiente por ID",
    description="Obtiene los datos civiles de un acudiente registrado.",
    dependencies=[Depends(require_permission("guardians", "read"))],
)
async def get_guardian(
    guardian_id: uuid.UUID,
    db: SessionDep,
) -> GuardianResponse:
    service = GuardianService(session=db)
    guardian = await service.get_guardian_by_id(guardian_id=guardian_id)
    return GuardianResponse.model_validate(guardian)


@router.get(
    "",
    response_model=GuardianListResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar acudientes",
    description="Lista acudientes registrados con filtro por documento.",
    dependencies=[Depends(require_permission("guardians", "read"))],
)
async def list_guardians(
    db: SessionDep,
    document_number: Annotated[
        str | None,
        Query(description="Filtrar por documento"),
    ] = None,
) -> GuardianListResponse:
    query = select(Guardian)
    if document_number:
        query = query.where(Guardian.document_number.ilike(f"%{document_number}%"))

    query = query.order_by(Guardian.last_name.asc())
    result = await db.execute(query)
    guardians = list(result.scalars().all())

    return GuardianListResponse(
        items=[GuardianResponse.model_validate(g) for g in guardians],
        total=len(guardians),
    )


@router.post(
    "/{guardian_id}/students/{student_id}",
    response_model=StudentGuardianResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Vincular acudiente a estudiante",
    description="Asocia un acudiente con un estudiante de la institución.",
    dependencies=[Depends(require_permission("guardians", "link_student"))],
)
async def associate_guardian_to_student(
    guardian_id: uuid.UUID,
    student_id: uuid.UUID,
    payload: AssociateGuardianRequest,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    client_ip: ClientIpDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> StudentGuardianResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    correlation_id = correlation_id_ctx.get()

    service = GuardianService(session=db)
    assoc = await service.associate_guardian_to_student(
        student_id=student_id,
        guardian_id=guardian_id,
        institution_id=target_institution_id,
        relationship_type=payload.relationship_type,
        is_primary_contact=payload.is_primary_contact,
        is_authorized_pickup=payload.is_authorized_pickup,
        actor_id=current_user.id,
        actor_ip=client_ip,
        correlation_id=correlation_id,
    )
    await db.commit()
    await db.refresh(assoc)
    return StudentGuardianResponse.model_validate(assoc)
