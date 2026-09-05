"""
PEVN Backend — Groups API Endpoints

REST Controller for classroom groups, capacity calculation, and group director
assignment, delegating business rules to GroupService.
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
from app.models.group import Group
from app.models.institution import Campus
from app.schemas.academic import (
    AssignGroupDirectorRequest,
    GroupCapacityResponse,
    GroupCreateRequest,
    GroupListResponse,
    GroupResponse,
)
from app.services.group_service import GroupService

router = APIRouter(prefix="/groups", tags=["Groups"])


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
    response_model=GroupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear grupo de clase",
    description="Crea un nuevo salón de clase para un grado en una sede.",
    dependencies=[Depends(require_permission("groups", "create"))],
)
async def create_group(
    payload: GroupCreateRequest,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    client_ip: ClientIpDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> GroupResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    correlation_id = correlation_id_ctx.get()

    service = GroupService(session=db)
    group = await service.create_group(
        institution_id=target_institution_id,
        campus_id=payload.campus_id,
        academic_year_id=payload.academic_year_id,
        grade_id=payload.grade_id,
        name=payload.name,
        shift=payload.shift,
        capacity_limit=payload.capacity_limit,
        director_teacher_id=payload.director_teacher_id,
        actor_id=current_user.id,
        actor_ip=client_ip,
        correlation_id=correlation_id,
    )
    await db.commit()
    await db.refresh(group)
    return GroupResponse.model_validate(group)


@router.get(
    "/{group_id}",
    response_model=GroupResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar grupo por ID",
    description="Obtiene los detalles de un grupo validando tenant.",
    dependencies=[Depends(require_permission("groups", "read"))],
)
async def get_group(
    group_id: uuid.UUID,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> GroupResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    service = GroupService(session=db)
    group = await service.get_group_by_id(
        group_id=group_id,
        institution_id=target_institution_id,
        user=current_user,
        auth=auth,
    )
    return GroupResponse.model_validate(group)


@router.get(
    "",
    response_model=GroupListResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar grupos",
    description="Lista los grupos de la institución con filtros.",
    dependencies=[Depends(require_permission("groups", "read"))],
)
async def list_groups(
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    campus_id: Annotated[
        uuid.UUID | None,
        Query(description="Filtrar por sede"),
    ] = None,
    academic_year_id: Annotated[
        uuid.UUID | None,
        Query(description="Filtrar por año lectivo"),
    ] = None,
    grade_id: Annotated[
        uuid.UUID | None,
        Query(description="Filtrar por grado"),
    ] = None,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> GroupListResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    service = GroupService(session=db)
    groups = await service.list_groups(
        institution_id=target_institution_id,
        user=current_user,
        auth=auth,
        campus_id=campus_id,
        academic_year_id=academic_year_id,
        grade_id=grade_id,
    )

    return GroupListResponse(
        items=[GroupResponse.model_validate(g) for g in groups],
        total=len(groups),
    )


@router.get(
    "/{group_id}/capacity",
    response_model=GroupCapacityResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar cupos y disponibilidad de un grupo",
    description="Calcula en tiempo real los cupos y disponibilidad.",
    dependencies=[Depends(require_permission("groups", "read"))],
)
async def get_group_capacity(
    group_id: uuid.UUID,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> GroupCapacityResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    service = GroupService(session=db)
    limit, active, available = await service.get_available_capacity(
        group_id=group_id,
        institution_id=target_institution_id,
    )
    return GroupCapacityResponse(
        group_id=group_id,
        capacity_limit=limit,
        active_enrolled_count=active,
        available_slots=available,
    )


@router.post(
    "/{group_id}/assign-director",
    response_model=GroupResponse,
    status_code=status.HTTP_200_OK,
    summary="Asignar director de grupo",
    description="Asigna un docente de la institución como director.",
    dependencies=[Depends(require_permission("groups", "assign_director"))],
)
async def assign_group_director(
    group_id: uuid.UUID,
    payload: AssignGroupDirectorRequest,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    client_ip: ClientIpDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> GroupResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    correlation_id = correlation_id_ctx.get()

    service = GroupService(session=db)
    group = await service.assign_group_director(
        group_id=group_id,
        teacher_id=payload.teacher_id,
        institution_id=target_institution_id,
        actor_id=current_user.id,
        actor_ip=client_ip,
        correlation_id=correlation_id,
    )
    await db.commit()
    await db.refresh(group)
    return GroupResponse.model_validate(group)
