"""
PEVN Backend — Teachers API Endpoints

REST Controller for educator professional profiles, appointments,
and workload eligibility, delegating business rules to TeacherService.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

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
from app.models.teacher import Teacher, TeacherContractType
from app.schemas.academic import (
    TeacherCreateRequest,
    TeacherEligibilityResponse,
    TeacherListResponse,
    TeacherResponse,
)
from app.services.teacher_service import TeacherService

router = APIRouter(prefix="/teachers", tags=["Teachers"])


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
    response_model=TeacherResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear perfil docente",
    description="Crea un perfil docente vinculado 1:1 a un usuario.",
    dependencies=[Depends(require_permission("teachers", "create"))],
)
async def create_teacher(
    payload: TeacherCreateRequest,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    client_ip: ClientIpDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> TeacherResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    correlation_id = correlation_id_ctx.get()

    service = TeacherService(session=db)
    teacher = await service.create_teacher(
        institution_id=target_institution_id,
        user_id=payload.user_id,
        specialty_area=payload.specialty_area,
        contract_type=payload.contract_type,
        escalafon_grade=payload.escalafon_grade,
        actor_id=current_user.id,
        actor_ip=client_ip,
        correlation_id=correlation_id,
    )
    await db.commit()
    await db.refresh(teacher)
    return TeacherResponse.model_validate(teacher)


@router.get(
    "/{teacher_id}",
    response_model=TeacherResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar docente por ID",
    description="Obtiene los detalles del perfil docente validando tenant.",
    dependencies=[Depends(require_permission("teachers", "read"))],
)
async def get_teacher(
    teacher_id: uuid.UUID,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> TeacherResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    service = TeacherService(session=db)
    teacher = await service.get_teacher_by_id(
        teacher_id=teacher_id,
        institution_id=target_institution_id,
    )
    return TeacherResponse.model_validate(teacher)


@router.get(
    "",
    response_model=TeacherListResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar docentes",
    description="Lista los docentes de la institución con filtros opcionales.",
    dependencies=[Depends(require_permission("teachers", "read"))],
)
async def list_teachers(
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    contract_type: Annotated[
        TeacherContractType | None,
        Query(description="Filtrar por tipo de vinculación"),
    ] = None,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> TeacherListResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)

    query = (
        select(Teacher)
        .options(selectinload(Teacher.user))
        .where(Teacher.institution_id == target_institution_id)
    )
    if contract_type:
        query = query.where(Teacher.contract_type == contract_type)

    query = query.order_by(Teacher.created_at.desc())
    result = await db.execute(query)
    teachers = list(result.scalars().all())

    return TeacherListResponse(
        items=[TeacherResponse.model_validate(t) for t in teachers],
        total=len(teachers),
    )


@router.get(
    "/{teacher_id}/eligibility",
    response_model=TeacherEligibilityResponse,
    status_code=status.HTTP_200_OK,
    summary="Verificar aptitud del docente",
    description="Verifica que el docente esté activo para asignación.",
    dependencies=[Depends(require_permission("teachers", "read"))],
)
async def validate_teacher_eligibility(
    teacher_id: uuid.UUID,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> TeacherEligibilityResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    service = TeacherService(session=db)
    is_eligible = await service.validate_teacher_eligibility(
        teacher_id=teacher_id,
        institution_id=target_institution_id,
    )
    return TeacherEligibilityResponse(
        teacher_id=teacher_id,
        is_eligible=is_eligible,
        message="Docente activo y habilitado para asignación académica.",
    )
