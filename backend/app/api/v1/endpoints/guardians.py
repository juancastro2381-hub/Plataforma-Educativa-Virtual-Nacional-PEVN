"""
PEVN Backend — Guardians API Endpoints

REST Controller for legal guardians (Acudientes) and student-guardian associations,
supporting decoupled national identity per [OPEN-DECISION-3A-01], account provisioning,
lifecycle management, and delegating business rules to GuardianService.
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
    GuardianAccountActionResponse,
    GuardianAccountProvisionRequest,
    GuardianAccountStatusUpdateRequest,
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
    description="Crea un registro de acudiente (OPEN-DECISION-3A-01) y opcionalmente aprovisiona cuenta.",
    dependencies=[Depends(require_permission("guardians", "create"))],
)
async def create_guardian(
    payload: GuardianCreateRequest,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    client_ip: ClientIpDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> GuardianResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    correlation_id = correlation_id_ctx.get()

    service = GuardianService(session=db)
    guardian, _ = await service.create_guardian(
        institution_id=target_institution_id,
        first_name=payload.first_name,
        last_name=payload.last_name,
        document_type=payload.document_type,
        document_number=payload.document_number,
        phone=payload.phone,
        email=payload.email,
        address=payload.address,
        relationship_type=payload.relationship_type,
        user_id=payload.user_id,
        new_user=payload.new_user,
        provision_account=payload.provision_account,
        actor_id=current_user.id,
        actor_ip=client_ip,
        correlation_id=correlation_id,
    )
    await db.commit()
    return service.build_guardian_response(guardian)


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
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> GuardianResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    service = GuardianService(session=db)
    guardian = await service.get_guardian_by_id(
        guardian_id=guardian_id,
        institution_id=target_institution_id,
    )
    return service.build_guardian_response(guardian)


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
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    document_number: Annotated[
        str | None,
        Query(description="Filtrar por documento"),
    ] = None,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> GuardianListResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    service = GuardianService(session=db)
    guardians = await service.list_guardians(
        institution_id=target_institution_id,
        document_number=document_number,
    )

    return GuardianListResponse(
        items=[service.build_guardian_response(g) for g in guardians],
        total=len(guardians),
    )


@router.post(
    "/{guardian_id}/account/provision",
    response_model=GuardianAccountActionResponse,
    status_code=status.HTTP_200_OK,
    summary="Aprovisionar cuenta de acceso para acudiente",
    description="Crea o habilita el usuario de login para el acudiente y genera token de configuración.",
    dependencies=[Depends(require_permission("guardians", "create"))],
)
async def provision_guardian_account(
    guardian_id: uuid.UUID,
    payload: GuardianAccountProvisionRequest,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    client_ip: ClientIpDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> GuardianAccountActionResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    correlation_id = correlation_id_ctx.get()

    service = GuardianService(session=db)
    guardian, status_enum, message, reset_token = await service.provision_guardian_account(
        guardian_id=guardian_id,
        institution_id=target_institution_id,
        email=payload.email,
        actor_id=current_user.id,
        actor_ip=client_ip,
        correlation_id=correlation_id,
    )
    await db.commit()
    return GuardianAccountActionResponse(
        guardian_id=guardian.id,
        user_id=guardian.user_id,
        account_status=status_enum,
        message=message,
        reset_token=reset_token,
    )


@router.post(
    "/{guardian_id}/account/status",
    response_model=GuardianAccountActionResponse,
    status_code=status.HTTP_200_OK,
    summary="Activar o desactivar cuenta de acudiente",
    description="Modifica el estado de acceso de la cuenta del acudiente.",
    dependencies=[Depends(require_permission("guardians", "update"))],
)
async def update_guardian_account_status(
    guardian_id: uuid.UUID,
    payload: GuardianAccountStatusUpdateRequest,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    client_ip: ClientIpDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> GuardianAccountActionResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    correlation_id = correlation_id_ctx.get()

    service = GuardianService(session=db)
    guardian, status_enum, message = await service.update_guardian_account_status(
        guardian_id=guardian_id,
        institution_id=target_institution_id,
        is_active=payload.is_active,
        actor_id=current_user.id,
        actor_ip=client_ip,
        correlation_id=correlation_id,
    )
    await db.commit()
    return GuardianAccountActionResponse(
        guardian_id=guardian.id,
        user_id=guardian.user_id,
        account_status=status_enum,
        message=message,
    )


@router.post(
    "/{guardian_id}/account/reset-password",
    response_model=GuardianAccountActionResponse,
    status_code=status.HTTP_200_OK,
    summary="Restablecer contraseña de acudiente",
    description="Genera un token seguro para restablecer credenciales del acudiente.",
    dependencies=[Depends(require_permission("guardians", "update"))],
)
async def reset_guardian_password(
    guardian_id: uuid.UUID,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    client_ip: ClientIpDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> GuardianAccountActionResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    correlation_id = correlation_id_ctx.get()

    service = GuardianService(session=db)
    guardian, status_enum, message, reset_token = await service.reset_guardian_password(
        guardian_id=guardian_id,
        institution_id=target_institution_id,
        actor_id=current_user.id,
        actor_ip=client_ip,
        correlation_id=correlation_id,
    )
    await db.commit()
    return GuardianAccountActionResponse(
        guardian_id=guardian.id,
        user_id=guardian.user_id,
        account_status=status_enum,
        message=message,
        reset_token=reset_token,
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


@router.delete(
    "/{guardian_id}/students/{student_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desvincular acudiente de estudiante",
    description="Elimina la asociación entre acudiente y estudiante preservando los perfiles civiles.",
    dependencies=[Depends(require_permission("guardians", "link_student"))],
)
async def dissociate_guardian_from_student(
    guardian_id: uuid.UUID,
    student_id: uuid.UUID,
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


@router.get(
    "/{guardian_id}/students",
    response_model=list[StudentGuardianResponse],
    status_code=status.HTTP_200_OK,
    summary="Consultar estudiantes de un acudiente",
    description="Lista los estudiantes vinculados y autorizaciones del acudiente.",
    dependencies=[Depends(require_permission("guardians", "read"))],
)
async def get_guardian_students(
    guardian_id: uuid.UUID,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> list[StudentGuardianResponse]:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    service = GuardianService(session=db)
    associations = await service.get_guardian_students(
        guardian_id=guardian_id,
        institution_id=target_institution_id,
    )
    return [StudentGuardianResponse.model_validate(a) for a in associations]


