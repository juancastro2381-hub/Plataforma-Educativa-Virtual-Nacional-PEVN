"""
PEVN Backend — Students API Endpoints

REST Controller for student profiles, SIMAT identification, inclusion metadata,
account lifecycle, and guardian links, delegating business rules to StudentService.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

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
from app.schemas.academic import (
    AssociateGuardianRequest,
    StudentAccountActionResponse,
    StudentAccountProvisionRequest,
    StudentAccountStatusUpdateRequest,
    StudentCreateRequest,
    StudentGuardianResponse,
    StudentListResponse,
    StudentResponse,
)
from app.services.guardian_service import GuardianService
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
        new_user=payload.new_user,
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
    return service.build_student_response(student)


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
        user=current_user,
        auth=auth,
    )
    return service.build_student_response(student)


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
    service = StudentService(session=db)
    students = await service.list_students(
        institution_id=target_institution_id,
        user=current_user,
        auth=auth,
        code_simat=code_simat,
    )

    return StudentListResponse(
        items=[service.build_student_response(s) for s in students],
        total=len(students),
    )


@router.post(
    "/{student_id}/account/provision",
    response_model=StudentAccountActionResponse,
    status_code=status.HTTP_200_OK,
    summary="Aprovisionar cuenta de acceso para estudiante",
    description="Habilita el usuario de login para el estudiante y genera token de configuración.",
    dependencies=[Depends(require_permission("students", "update"))],
)
async def provision_student_account(
    student_id: uuid.UUID,
    payload: StudentAccountProvisionRequest,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    client_ip: ClientIpDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> StudentAccountActionResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    correlation_id = correlation_id_ctx.get()

    service = StudentService(session=db)
    student, status_enum, message, reset_token = await service.provision_student_account(
        student_id=student_id,
        institution_id=target_institution_id,
        email=payload.email,
        actor_id=current_user.id,
        actor_ip=client_ip,
        correlation_id=correlation_id,
    )
    await db.commit()
    return StudentAccountActionResponse(
        student_id=student.id,
        user_id=student.user_id,
        account_status=status_enum,
        message=message,
        reset_token=reset_token,
    )


@router.post(
    "/{student_id}/account/status",
    response_model=StudentAccountActionResponse,
    status_code=status.HTTP_200_OK,
    summary="Activar o desactivar cuenta de estudiante",
    description="Modifica el estado de acceso de la cuenta del estudiante.",
    dependencies=[Depends(require_permission("students", "update"))],
)
async def update_student_account_status(
    student_id: uuid.UUID,
    payload: StudentAccountStatusUpdateRequest,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    client_ip: ClientIpDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> StudentAccountActionResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    correlation_id = correlation_id_ctx.get()

    service = StudentService(session=db)
    student, status_enum, message = await service.update_student_account_status(
        student_id=student_id,
        institution_id=target_institution_id,
        is_active=payload.is_active,
        actor_id=current_user.id,
        actor_ip=client_ip,
        correlation_id=correlation_id,
    )
    await db.commit()
    return StudentAccountActionResponse(
        student_id=student.id,
        user_id=student.user_id,
        account_status=status_enum,
        message=message,
    )


@router.post(
    "/{student_id}/account/reset-password",
    response_model=StudentAccountActionResponse,
    status_code=status.HTTP_200_OK,
    summary="Restablecer contraseña de estudiante",
    description="Genera un token seguro para restablecer credenciales del estudiante.",
    dependencies=[Depends(require_permission("students", "update"))],
)
async def reset_student_password(
    student_id: uuid.UUID,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    client_ip: ClientIpDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> StudentAccountActionResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    correlation_id = correlation_id_ctx.get()

    service = StudentService(session=db)
    student, status_enum, message, reset_token = await service.reset_student_password(
        student_id=student_id,
        institution_id=target_institution_id,
        actor_id=current_user.id,
        actor_ip=client_ip,
        correlation_id=correlation_id,
    )
    await db.commit()
    return StudentAccountActionResponse(
        student_id=student.id,
        user_id=student.user_id,
        account_status=status_enum,
        message=message,
        reset_token=reset_token,
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
        user=current_user,
        auth=auth,
    )
    return [StudentGuardianResponse.model_validate(a) for a in associations]


@router.post(
    "/{student_id}/guardians/{guardian_id}",
    response_model=StudentGuardianResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Vincular acudiente a estudiante (desde estudiante)",
    description="Asocia un acudiente con este estudiante.",
    dependencies=[Depends(require_permission("guardians", "link_student"))],
)
async def associate_guardian_to_student_from_student(
    student_id: uuid.UUID,
    guardian_id: uuid.UUID,
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


@router.delete(
    "/{student_id}/guardians/{guardian_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desvincular acudiente de estudiante (desde estudiante)",
    description="Elimina la asociación entre acudiente y estudiante preservando los perfiles civiles.",
    dependencies=[Depends(require_permission("guardians", "link_student"))],
)
async def dissociate_guardian_from_student_from_student(
    student_id: uuid.UUID,
    guardian_id: uuid.UUID,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    client_ip: ClientIpDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> None:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    correlation_id = correlation_id_ctx.get()

    service = GuardianService(session=db)
    await service.dissociate_guardian_from_student(
        student_id=student_id,
        guardian_id=guardian_id,
        institution_id=target_institution_id,
        actor_id=current_user.id,
        actor_ip=client_ip,
        correlation_id=correlation_id,
    )
    await db.commit()

