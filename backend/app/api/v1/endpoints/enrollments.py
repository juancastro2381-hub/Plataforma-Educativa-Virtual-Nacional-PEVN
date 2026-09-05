"""
PEVN Backend — Enrollments API Endpoints

REST Controller for student enrollment contracts, status lifecycle,
and historical immutability, delegating business rules to EnrollmentService.
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
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.student import Student
from app.schemas.academic import (
    EnrollmentCreateRequest,
    EnrollmentGraduateRequest,
    EnrollmentListResponse,
    EnrollmentResponse,
    EnrollmentWithdrawRequest,
)
from app.services.enrollment_service import EnrollmentService

router = APIRouter(prefix="/enrollments", tags=["Enrollments"])


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
    response_model=EnrollmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear matrícula estudiantil",
    description="Crea un contrato de matrícula verificando cupos e invariantes.",
    dependencies=[Depends(require_permission("enrollments", "create"))],
)
async def create_enrollment(
    payload: EnrollmentCreateRequest,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    client_ip: ClientIpDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> EnrollmentResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    correlation_id = correlation_id_ctx.get()

    service = EnrollmentService(session=db)
    enrollment = await service.create_enrollment(
        institution_id=target_institution_id,
        student_id=payload.student_id,
        group_id=payload.group_id,
        academic_year_id=payload.academic_year_id,
        enrollment_date=payload.enrollment_date,
        status=payload.status,
        status_reason=payload.status_reason,
        actor_id=current_user.id,
        actor_ip=client_ip,
        correlation_id=correlation_id,
    )
    await db.commit()
    await db.refresh(enrollment)
    return EnrollmentResponse.model_validate(enrollment)


@router.get(
    "/{enrollment_id}",
    response_model=EnrollmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar matrícula por ID",
    description="Obtiene los datos de una matrícula validando tenant.",
    dependencies=[Depends(require_permission("enrollments", "read"))],
)
async def get_enrollment(
    enrollment_id: uuid.UUID,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> EnrollmentResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    service = EnrollmentService(session=db)
    enrollment = await service.get_enrollment_by_id(
        enrollment_id=enrollment_id,
        institution_id=target_institution_id,
        user=current_user,
        auth=auth,
    )
    return EnrollmentResponse.model_validate(enrollment)


@router.get(
    "",
    response_model=EnrollmentListResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar matrículas",
    description="Lista matrículas de la institución con filtros.",
    dependencies=[Depends(require_permission("enrollments", "read"))],
)
async def list_enrollments(
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    student_id: Annotated[
        uuid.UUID | None,
        Query(description="Filtrar por estudiante"),
    ] = None,
    group_id: Annotated[
        uuid.UUID | None,
        Query(description="Filtrar por grupo"),
    ] = None,
    academic_year_id: Annotated[
        uuid.UUID | None,
        Query(description="Filtrar por año lectivo"),
    ] = None,
    status_filter: Annotated[
        EnrollmentStatus | None,
        Query(alias="status", description="Filtrar por estado"),
    ] = None,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> EnrollmentListResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    service = EnrollmentService(session=db)
    enrollments = await service.list_enrollments(
        institution_id=target_institution_id,
        user=current_user,
        auth=auth,
        student_id=student_id,
        group_id=group_id,
        academic_year_id=academic_year_id,
        status_filter=status_filter,
    )

    return EnrollmentListResponse(
        items=[EnrollmentResponse.model_validate(e) for e in enrollments],
        total=len(enrollments),
    )


@router.post(
    "/{enrollment_id}/activate",
    response_model=EnrollmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Activar prematrícula",
    description="Transiciona una matrícula en estado PRE_ENROLLED a ACTIVE.",
    dependencies=[Depends(require_permission("enrollments", "create"))],
)
async def activate_enrollment(
    enrollment_id: uuid.UUID,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    client_ip: ClientIpDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> EnrollmentResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    correlation_id = correlation_id_ctx.get()

    service = EnrollmentService(session=db)
    enrollment = await service.activate_enrollment(
        enrollment_id=enrollment_id,
        institution_id=target_institution_id,
        actor_id=current_user.id,
        actor_ip=client_ip,
        correlation_id=correlation_id,
    )
    await db.commit()
    await db.refresh(enrollment)
    return EnrollmentResponse.model_validate(enrollment)


@router.post(
    "/{enrollment_id}/withdraw",
    response_model=EnrollmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Retirar matrícula",
    description="Transiciona una matrícula activa a WITHDRAWN con histórico.",
    dependencies=[Depends(require_permission("enrollments", "withdraw"))],
)
async def withdraw_enrollment(
    enrollment_id: uuid.UUID,
    payload: EnrollmentWithdrawRequest,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    client_ip: ClientIpDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> EnrollmentResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    correlation_id = correlation_id_ctx.get()

    service = EnrollmentService(session=db)
    enrollment = await service.withdraw_enrollment(
        enrollment_id=enrollment_id,
        institution_id=target_institution_id,
        reason=payload.reason,
        actor_id=current_user.id,
        actor_ip=client_ip,
        correlation_id=correlation_id,
    )
    await db.commit()
    await db.refresh(enrollment)
    return EnrollmentResponse.model_validate(enrollment)


@router.post(
    "/{enrollment_id}/graduate",
    response_model=EnrollmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Graduar matrícula",
    description="Transiciona una matrícula activa a GRADUATED.",
    dependencies=[Depends(require_permission("enrollments", "withdraw"))],
)
async def graduate_enrollment(
    enrollment_id: uuid.UUID,
    payload: EnrollmentGraduateRequest,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    client_ip: ClientIpDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> EnrollmentResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    correlation_id = correlation_id_ctx.get()

    service = EnrollmentService(session=db)
    enrollment = await service.graduate_enrollment(
        enrollment_id=enrollment_id,
        institution_id=target_institution_id,
        reason=payload.reason,
        actor_id=current_user.id,
        actor_ip=client_ip,
        correlation_id=correlation_id,
    )
    await db.commit()
    await db.refresh(enrollment)
    return EnrollmentResponse.model_validate(enrollment)
