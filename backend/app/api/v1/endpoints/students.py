"""
PEVN Backend — Students API Endpoints

REST Controller for student profiles, SIMAT identification, inclusion metadata,
and guardian links, delegating business rules to StudentService.
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
from app.models.student import Student
from app.schemas.academic import (
    StudentCreateRequest,
    StudentGuardianResponse,
    StudentListResponse,
    StudentResponse,
)
from app.services.student_service import StudentService

router = APIRouter(prefix="/students", tags=["Students"])


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
    response_model=StudentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear perfil de estudiante",
    description="Crea un perfil de estudiante vinculado 1:1 a un usuario.",
    dependencies=[Depends(require_permission("students", "create"))],
)
async def create_student(
    payload: StudentCreateRequest,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    client_ip: ClientIpDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> StudentResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    correlation_id = correlation_id_ctx.get()

    service = StudentService(session=db)
    student = await service.create_student(
        institution_id=target_institution_id,
        user_id=payload.user_id,
        code_simat=payload.code_simat,
        birth_date=payload.birth_date,
        gender=payload.gender,
        blood_type=payload.blood_type,
        stratum=payload.stratum,
        eps_health_provider=payload.eps_health_provider,
        has_disability=payload.has_disability,
        disability_type=payload.disability_type,
        actor_id=current_user.id,
        actor_ip=client_ip,
        correlation_id=correlation_id,
    )
    await db.commit()
    await db.refresh(student)
    return StudentResponse.model_validate(student)


@router.get(
    "/{student_id}",
    response_model=StudentResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar estudiante por ID",
    description="Obtiene los datos de un estudiante validando tenant.",
    dependencies=[Depends(require_permission("students", "read"))],
)
async def get_student(
    student_id: uuid.UUID,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> StudentResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    service = StudentService(session=db)
    student = await service.get_student_by_id(
        student_id=student_id,
        institution_id=target_institution_id,
    )
    return StudentResponse.model_validate(student)


@router.get(
    "",
    response_model=StudentListResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar estudiantes",
    description="Lista los estudiantes de la institución con filtros.",
    dependencies=[Depends(require_permission("students", "read"))],
)
async def list_students(
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    code_simat: Annotated[
        str | None,
        Query(description="Filtrar por código SIMAT"),
    ] = None,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> StudentListResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)

    query = (
        select(Student)
        .options(selectinload(Student.user))
        .where(Student.institution_id == target_institution_id)
    )
    if code_simat:
        query = query.where(Student.code_simat.ilike(f"%{code_simat}%"))

    query = query.order_by(Student.code_simat.asc())
    result = await db.execute(query)
    students = list(result.scalars().all())

    return StudentListResponse(
        items=[StudentResponse.model_validate(s) for s in students],
        total=len(students),
    )


@router.get(
    "/{student_id}/guardians",
    response_model=list[StudentGuardianResponse],
    status_code=status.HTTP_200_OK,
    summary="Consultar acudientes de un estudiante",
    description="Lista los acudientes vinculados y autorizaciones.",
    dependencies=[Depends(require_permission("students", "read"))],
)
async def get_student_guardians(
    student_id: uuid.UUID,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> list[StudentGuardianResponse]:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    service = StudentService(session=db)
    associations = await service.get_student_guardians(
        student_id=student_id,
        institution_id=target_institution_id,
    )
    return [StudentGuardianResponse.model_validate(a) for a in associations]
