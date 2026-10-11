"""
PEVN Backend — Coordinators API Controller

REST Controller for complete, secure, and institutional COORDINATOR lifecycle:
  - List and search institutional coordinators with tenant isolation
  - List active campuses of the institution for scope assignment
  - Create/invite new coordinator within active institution (Rector authority)
  - Resend/regenerate time-limited invitation token
  - Update coordinator status (activate/deactivate) with session invalidation
  - Anti-IDOR enforcement on institution boundaries
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status

from app.api.deps import (
    AuthContextDep,
    CurrentUserDep,
    SessionDep,
    require_permission,
    resolve_institution_id,
)
from app.core.security.interfaces import SystemRole
from app.exceptions.errors import AuthorizationError
from app.schemas.coordinator import (
    CoordinatorCampusOption,
    CoordinatorCreateRequest,
    CoordinatorListResponse,
    CoordinatorResendInvitationResponse,
    CoordinatorResponse,
    CoordinatorStatusUpdateRequest,
)
from app.services.coordinator_service import CoordinatorService

router = APIRouter()


@router.get(
    "/campuses",
    response_model=list[CoordinatorCampusOption],
    status_code=status.HTTP_200_OK,
    summary="Listar sedes de la institución educativa para asignación de coordinadores",
    description="Devuelve las sedes (campuses) registradas para la institución educativa en sesión.",
    dependencies=[Depends(require_permission("coordinators", "read"))],
)
async def list_institution_campuses(
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="UUID institucional (para roles multi-institución)"),
    ] = None,
) -> list[CoordinatorCampusOption]:
    """List campuses belonging strictly to the authorized institutional tenant."""
    target_inst_id = await resolve_institution_id(
        db=db,
        auth=auth,
        current_user=current_user,
        institution_id_override=institution_id,
    )
    service = CoordinatorService(session=db)
    return await service.list_campuses(institution_id=target_inst_id)


@router.get(
    "",
    response_model=CoordinatorListResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar coordinadores institucionales",
    description="Devuelve la lista de coordinadores de la institución educativa del actor en sesión.",
    dependencies=[Depends(require_permission("coordinators", "read"))],
)
async def list_coordinators(
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="UUID institucional (requerido para roles superiores con alcance multi-institución)"),
    ] = None,
    is_active: Annotated[
        bool | None,
        Query(description="Filtrar por estado activo/inactivo"),
    ] = None,
    search: Annotated[
        str | None,
        Query(description="Búsqueda por nombres, apellidos, correo o documento"),
    ] = None,
    page: Annotated[int, Query(ge=1, description="Número de página")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Tamaño de página")] = 20,
) -> CoordinatorListResponse:
    """List institutional coordinators enforcing server-side institutional scope."""
    target_inst_id = await resolve_institution_id(
        db=db,
        auth=auth,
        current_user=current_user,
        institution_id_override=institution_id,
    )

    service = CoordinatorService(session=db)
    items, total = await service.list_coordinators(
        institution_id=target_inst_id,
        is_active=is_active,
        search=search,
        page=page,
        page_size=page_size,
    )

    return CoordinatorListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{coordinator_id}",
    response_model=CoordinatorResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar coordinador institucional por ID",
    description="Devuelve el detalle de un coordinador garantizando la barrera multi-inquilino.",
    dependencies=[Depends(require_permission("coordinators", "read"))],
)
async def get_coordinator(
    coordinator_id: uuid.UUID,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="UUID institucional para verificación"),
    ] = None,
) -> CoordinatorResponse:
    """Retrieve single institutional coordinator verifying tenant isolation."""
    target_inst_id = await resolve_institution_id(
        db=db,
        auth=auth,
        current_user=current_user,
        institution_id_override=institution_id,
    )

    service = CoordinatorService(session=db)
    return await service.get_coordinator(
        institution_id=target_inst_id,
        coordinator_id=coordinator_id,
    )


@router.post(
    "",
    response_model=CoordinatorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Aprovisionar o invitar coordinador institucional",
    description="Crea e invita un nuevo coordinador a la institución educativa del Rector con alcance institucional o por sede.",
    dependencies=[Depends(require_permission("coordinators", "create"))],
)
async def create_coordinator(
    payload: CoordinatorCreateRequest,
    current_user: CurrentUserDep,
    auth: AuthContextDep,
    db: SessionDep,
    request: Request,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="UUID institucional para roles directivos/superiores"),
    ] = None,
) -> CoordinatorResponse:
    """Provision or invite a new Coordinator with strict server-side institution binding."""
    # Coordinators and lower roles cannot provision coordinators
    if (
        SystemRole.COORDINATOR in auth.roles
        or SystemRole.ACADEMIC_COORDINATOR in auth.roles
        or SystemRole.TEACHER in auth.roles
        or SystemRole.STUDENT in auth.roles
        or SystemRole.GUARDIAN in auth.roles
    ):
        raise AuthorizationError(
            "No posee facultades para aprovisionar coordinadores institucionales.",
            code="PERMISSION_DENIED",
        )

    target_inst_id = await resolve_institution_id(
        db=db,
        auth=auth,
        current_user=current_user,
        institution_id_override=institution_id,
    )

    service = CoordinatorService(session=db)
    coordinator = await service.create_coordinator(
        institution_id=target_inst_id,
        payload=payload,
        actor_id=current_user.id,
        actor_ip=request.client.host if request.client else "0.0.0.0",
        correlation_id=request.headers.get("X-Correlation-ID"),
    )

    if SystemRole.SUPERADMIN in auth.roles:
        from app.audit.interfaces import AuditEvent, AuditEventType
        from app.audit.service import audit_service

        await audit_service.record(
            AuditEvent(
                event_type=AuditEventType.SUPERADMIN_EMERGENCY_ROLE_PROVISIONING,
                actor_id=str(current_user.id),
                actor_ip=request.client.host if request.client else "0.0.0.0",
                target_id=str(coordinator.id),
                target_type="Coordinator",
                institution_id=str(target_inst_id),
                correlation_id=request.headers.get("X-Correlation-ID"),
                metadata={
                    "action": "create_coordinator",
                    "target_role": "coordinator",
                    "institution_id": str(target_inst_id),
                    "campus_id": str(payload.campus_id) if payload.campus_id else None,
                    "email": coordinator.email,
                    "authority_level": "superadmin_emergency",
                },
            ),
            session=db,
        )

    await db.commit()
    return coordinator


@router.post(
    "/{coordinator_id}/resend-invitation",
    response_model=CoordinatorResendInvitationResponse,
    status_code=status.HTTP_200_OK,
    summary="Reenviar invitación de acceso a un coordinador",
    description="Invalida invitaciones previas y genera un nuevo enlace de activación criptográfico de 48 horas.",
    dependencies=[Depends(require_permission("coordinators", "create"))],
)
async def resend_coordinator_invitation(
    coordinator_id: uuid.UUID,
    current_user: CurrentUserDep,
    auth: AuthContextDep,
    db: SessionDep,
    request: Request,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="UUID institucional para verificación"),
    ] = None,
) -> CoordinatorResendInvitationResponse:
    """Resend invitation for an inactive/pending coordinator."""
    if (
        SystemRole.COORDINATOR in auth.roles
        or SystemRole.ACADEMIC_COORDINATOR in auth.roles
        or SystemRole.TEACHER in auth.roles
        or SystemRole.STUDENT in auth.roles
        or SystemRole.GUARDIAN in auth.roles
    ):
        raise AuthorizationError(
            "No posee facultades para reenviar invitaciones a coordinadores.",
            code="PERMISSION_DENIED",
        )

    target_inst_id = await resolve_institution_id(
        db=db,
        auth=auth,
        current_user=current_user,
        institution_id_override=institution_id,
    )

    service = CoordinatorService(session=db)
    result = await service.resend_invitation(
        coordinator_id=coordinator_id,
        institution_id=target_inst_id,
        actor_id=current_user.id,
        actor_ip=request.client.host if request.client else "0.0.0.0",
        correlation_id=request.headers.get("X-Correlation-ID"),
    )
    await db.commit()
    return result


@router.patch(
    "/{coordinator_id}/status",
    response_model=CoordinatorResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar estado operativo del coordinador",
    description="Activa o suspende al coordinador institucional, invalidando tokens al suspender.",
    dependencies=[Depends(require_permission("coordinators", "update"))],
)
async def update_coordinator_status(
    coordinator_id: uuid.UUID,
    payload: CoordinatorStatusUpdateRequest,
    current_user: CurrentUserDep,
    auth: AuthContextDep,
    db: SessionDep,
    request: Request,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="UUID institucional para verificación"),
    ] = None,
) -> CoordinatorResponse:
    """Update active status of a coordinator with session invalidation."""
    # Coordinators cannot modify status of coordinators
    if SystemRole.COORDINATOR in auth.roles or SystemRole.TEACHER in auth.roles or SystemRole.STUDENT in auth.roles:
        raise AuthorizationError(
            "No posee facultades para modificar el estado de un coordinador.",
            code="PERMISSION_DENIED",
        )

    target_inst_id = await resolve_institution_id(
        db=db,
        auth=auth,
        current_user=current_user,
        institution_id_override=institution_id,
    )

    service = CoordinatorService(session=db)
    coordinator = await service.update_status(
        institution_id=target_inst_id,
        coordinator_id=coordinator_id,
        is_active=payload.is_active,
        actor_id=current_user.id,
        actor_ip=request.client.host if request.client else "0.0.0.0",
        reason=payload.reason,
        correlation_id=request.headers.get("X-Correlation-ID"),
    )
    await db.commit()
    return coordinator
