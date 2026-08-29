"""
PEVN Backend — Academic Assignments API Endpoints

REST Controller for teacher workload allocations (Carga Académica Docente),
single-active instructor invariants, and teacher substitution workflows,
delegating business rules to AcademicAssignmentService.
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
from app.models.academic_assignment import AcademicAssignment
from app.models.teacher import Teacher
from app.schemas.academic import (
    AcademicAssignmentCreateRequest,
    AcademicAssignmentListResponse,
    AcademicAssignmentResponse,
    TeacherReplacementRequest,
    TeacherReplacementResponse,
)
from app.services.academic_assignment_service import AcademicAssignmentService

router = APIRouter(prefix="/academic-assignments", tags=["Academic Assignments"])


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
    response_model=AcademicAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear asignación académica",
    description="Asigna un docente titular garantizando titularidad única.",
    dependencies=[Depends(require_permission("academic_assignments", "create"))],
)
async def create_assignment(
    payload: AcademicAssignmentCreateRequest,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    client_ip: ClientIpDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> AcademicAssignmentResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    correlation_id = correlation_id_ctx.get()

    service = AcademicAssignmentService(session=db)
    assignment = await service.create_assignment(
        institution_id=target_institution_id,
        teacher_id=payload.teacher_id,
        subject_id=payload.subject_id,
        group_id=payload.group_id,
        academic_year_id=payload.academic_year_id,
        weekly_hours=payload.weekly_hours,
        is_active=payload.is_active,
        actor_id=current_user.id,
        actor_ip=client_ip,
        correlation_id=correlation_id,
    )
    await db.commit()
    await db.refresh(assignment)
    return AcademicAssignmentResponse.model_validate(assignment)


@router.get(
    "/{assignment_id}",
    response_model=AcademicAssignmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar asignación académica por ID",
    description="Obtiene los datos de una asignación validando tenant.",
    dependencies=[Depends(require_permission("academic_assignments", "read"))],
)
async def get_assignment(
    assignment_id: uuid.UUID,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> AcademicAssignmentResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    service = AcademicAssignmentService(session=db)
    assignment = await service.get_assignment_by_id(
        assignment_id=assignment_id,
        institution_id=target_institution_id,
    )
    return AcademicAssignmentResponse.model_validate(assignment)


@router.get(
    "",
    response_model=AcademicAssignmentListResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar asignaciones académicas",
    description="Lista asignaciones académicas con filtros opcionales.",
    dependencies=[Depends(require_permission("academic_assignments", "read"))],
)
async def list_assignments(
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    teacher_id: Annotated[
        uuid.UUID | None,
        Query(description="Filtrar por docente"),
    ] = None,
    group_id: Annotated[
        uuid.UUID | None,
        Query(description="Filtrar por grupo"),
    ] = None,
    subject_id: Annotated[
        uuid.UUID | None,
        Query(description="Filtrar por materia"),
    ] = None,
    academic_year_id: Annotated[
        uuid.UUID | None,
        Query(description="Filtrar por año lectivo"),
    ] = None,
    is_active: Annotated[
        bool | None,
        Query(description="Filtrar por estado activo"),
    ] = None,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> AcademicAssignmentListResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)

    query = (
        select(AcademicAssignment)
        .join(Teacher, AcademicAssignment.teacher_id == Teacher.id)
        .options(
            selectinload(AcademicAssignment.teacher),
            selectinload(AcademicAssignment.subject),
            selectinload(AcademicAssignment.group),
            selectinload(AcademicAssignment.academic_year),
        )
        .where(Teacher.institution_id == target_institution_id)
    )
    if teacher_id:
        query = query.where(AcademicAssignment.teacher_id == teacher_id)
    if group_id:
        query = query.where(AcademicAssignment.group_id == group_id)
    if subject_id:
        query = query.where(AcademicAssignment.subject_id == subject_id)
    if academic_year_id:
        query = query.where(AcademicAssignment.academic_year_id == academic_year_id)
    if is_active is not None:
        query = query.where(AcademicAssignment.is_active == is_active)

    query = query.order_by(AcademicAssignment.created_at.desc())
    result = await db.execute(query)
    assignments = list(result.scalars().all())

    return AcademicAssignmentListResponse(
        items=[AcademicAssignmentResponse.model_validate(a) for a in assignments],
        total=len(assignments),
    )


@router.post(
    "/{assignment_id}/deactivate",
    response_model=AcademicAssignmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Desactivar asignación académica",
    description="Desactiva una asignación académica activa.",
    dependencies=[Depends(require_permission("academic_assignments", "update"))],
)
async def deactivate_assignment(
    assignment_id: uuid.UUID,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    client_ip: ClientIpDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> AcademicAssignmentResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    correlation_id = correlation_id_ctx.get()

    service = AcademicAssignmentService(session=db)
    assignment = await service.deactivate_assignment(
        assignment_id=assignment_id,
        institution_id=target_institution_id,
        actor_id=current_user.id,
        actor_ip=client_ip,
        correlation_id=correlation_id,
    )
    await db.commit()
    await db.refresh(assignment)
    return AcademicAssignmentResponse.model_validate(assignment)


@router.post(
    "/{assignment_id}/replace-teacher",
    response_model=TeacherReplacementResponse,
    status_code=status.HTTP_200_OK,
    summary="Sustituir docente en asignación académica",
    description="Sustituye de forma atómica al docente titular de una materia.",
    dependencies=[Depends(require_permission("academic_assignments", "update"))],
)
async def replace_teacher(
    assignment_id: uuid.UUID,
    payload: TeacherReplacementRequest,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    client_ip: ClientIpDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> TeacherReplacementResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    correlation_id = correlation_id_ctx.get()

    service = AcademicAssignmentService(session=db)
    prev, new = await service.replace_teacher(
        assignment_id=assignment_id,
        new_teacher_id=payload.new_teacher_id,
        institution_id=target_institution_id,
        actor_id=current_user.id,
        actor_ip=client_ip,
        correlation_id=correlation_id,
    )
    await db.commit()
    await db.refresh(prev)
    await db.refresh(new)

    return TeacherReplacementResponse(
        previous_assignment=AcademicAssignmentResponse.model_validate(prev),
        new_assignment=AcademicAssignmentResponse.model_validate(new),
    )
