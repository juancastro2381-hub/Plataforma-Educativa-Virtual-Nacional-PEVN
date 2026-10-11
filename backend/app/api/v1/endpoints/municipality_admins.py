"""
PEVN Backend — Municipality Administrators API Controller

REST Controller for complete, secure, and auditable MUNICIPALITY_ADMIN lifecycle:
  - List and search municipality administrators with territorial scope enforcement
  - Canonical municipality selector data
  - Create new municipality administrator with strict territorial assignment
  - Status updates (activate / deactivate) with session token revocation
  - Controlled municipality reassignment with session token revocation
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
)
from app.core.config import get_settings
from app.core.security.interfaces import SystemRole
from app.exceptions.errors import AuthorizationError
from app.schemas.municipality_admin import (
    MunicipalityAdminCreateRequest,
    MunicipalityAdminInvitationResponse,
    MunicipalityAdminListResponse,
    MunicipalityAdminReassignMunicipalityRequest,
    MunicipalityAdminResponse,
    MunicipalityAdminStatusUpdateRequest,
    MunicipalityOptionResponse,
)
from app.services.email_service import EmailDeliveryStatus
from app.services.municipality_admin_service import MunicipalityAdminService

router = APIRouter()


@router.get(
    "/municipalities",
    response_model=list[MunicipalityOptionResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar municipios canónicos",
    description="Devuelve el catálogo de municipios canónicos para selectores de territorio, filtrado según el alcance del actor.",
)
async def list_canonical_municipalities(
    db: SessionDep,
    auth: AuthContextDep,
    department_id: Annotated[
        uuid.UUID | None,
        Query(description="Filtrar por UUID de departamento (para administradores nacionales)"),
    ] = None,
) -> list[MunicipalityOptionResponse]:
    """List canonical municipalities for dropdown selectors, scoped by authority."""
    service = MunicipalityAdminService(session=db)

    # Scoping rules
    if auth.scope.is_municipality() and SystemRole.MUNICIPALITY_ADMIN in auth.roles:
        actor_muni = uuid.UUID(auth.scope.municipality_id) if auth.scope.municipality_id else None
        return await service.list_municipalities(municipality_id=actor_muni)

    if auth.scope.is_department() and SystemRole.DEPARTMENT_ADMIN in auth.roles:
        actor_dept = uuid.UUID(auth.scope.department_id) if auth.scope.department_id else None
        if department_id and department_id != actor_dept:
            raise AuthorizationError(
                "No está autorizado para consultar municipios de otros departamentos.",
                code="PERMISSION_DENIED",
            )
        return await service.list_municipalities(department_id=actor_dept)

    return await service.list_municipalities(department_id=department_id)


@router.get(
    "",
    response_model=MunicipalityAdminListResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar y buscar administradores municipales",
    description="Permite buscar y filtrar administradores municipales respetando el aislamiento territorial.",
    dependencies=[Depends(require_permission("municipality_admins", "read"))],
)
async def list_municipality_admins(
    db: SessionDep,
    auth: AuthContextDep,
    department_id: Annotated[
        uuid.UUID | None,
        Query(description="Filtrar por UUID de departamento"),
    ] = None,
    municipality_id: Annotated[
        uuid.UUID | None,
        Query(description="Filtrar por UUID de municipio"),
    ] = None,
    is_active: Annotated[
        bool | None,
        Query(description="Filtrar por estado activo/inactivo"),
    ] = None,
    search: Annotated[
        str | None,
        Query(description="Búsqueda por nombre, apellido, correo, username o documento"),
    ] = None,
    page: Annotated[int, Query(ge=1, description="Número de página")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Tamaño de página")] = 20,
) -> MunicipalityAdminListResponse:
    """List municipality admins strictly bounded by caller's territorial scope."""
    service = MunicipalityAdminService(session=db)

    effective_dept_id = department_id
    effective_muni_id = municipality_id

    # Department Admin scope enforcement
    if auth.scope.is_department() and SystemRole.DEPARTMENT_ADMIN in auth.roles:
        actor_dept = uuid.UUID(auth.scope.department_id) if auth.scope.department_id else None
        if department_id and department_id != actor_dept:
            raise AuthorizationError(
                "No está autorizado para consultar administradores fuera de su departamento.",
                code="PERMISSION_DENIED",
            )
        effective_dept_id = actor_dept

    # Municipality Admin scope enforcement
    elif auth.scope.is_municipality() and SystemRole.MUNICIPALITY_ADMIN in auth.roles:
        actor_muni = uuid.UUID(auth.scope.municipality_id) if auth.scope.municipality_id else None
        if municipality_id and municipality_id != actor_muni:
            raise AuthorizationError(
                "No está autorizado para consultar administradores de otros municipios.",
                code="PERMISSION_DENIED",
            )
        effective_muni_id = actor_muni

    items, total = await service.list_municipality_admins(
        department_id=effective_dept_id,
        municipality_id=effective_muni_id,
        is_active=is_active,
        search=search,
        page=page,
        page_size=page_size,
    )

    return MunicipalityAdminListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{user_id}",
    response_model=MunicipalityAdminResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar administrador municipal por ID",
    description="Devuelve el detalle de un administrador municipal verificando la barrera territorial.",
    dependencies=[Depends(require_permission("municipality_admins", "read"))],
)
async def get_municipality_admin(
    user_id: uuid.UUID,
    db: SessionDep,
    auth: AuthContextDep,
) -> MunicipalityAdminResponse:
    """Retrieve single municipality admin with Anti-IDOR territorial boundary check."""
    service = MunicipalityAdminService(session=db)
    admin = await service.get_municipality_admin(user_id)

    # Validate territorial boundaries
    if auth.scope.is_department() and SystemRole.DEPARTMENT_ADMIN in auth.roles:
        actor_dept = uuid.UUID(auth.scope.department_id) if auth.scope.department_id else None
        if admin.department_id != actor_dept:
            raise AuthorizationError(
                "No está autorizado para consultar administradores fuera de su departamento.",
                code="PERMISSION_DENIED",
            )
    elif auth.scope.is_municipality() and SystemRole.MUNICIPALITY_ADMIN in auth.roles:
        actor_muni = uuid.UUID(auth.scope.municipality_id) if auth.scope.municipality_id else None
        if admin.municipality_id != actor_muni and str(auth.user_id) != str(user_id):
            raise AuthorizationError(
                "No está autorizado para consultar administradores de otros municipios.",
                code="PERMISSION_DENIED",
            )

    return admin


@router.post(
    "",
    response_model=MunicipalityAdminResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Aprovisionar administrador municipal",
    description="Crea un nuevo administrador municipal derivando autoritativamente su departamento de pertenencia.",
    dependencies=[Depends(require_permission("municipality_admins", "create"))],
)
async def create_municipality_admin(
    payload: MunicipalityAdminCreateRequest,
    current_user: CurrentUserDep,
    auth: AuthContextDep,
    db: SessionDep,
    request: Request,
) -> MunicipalityAdminResponse:
    """Provision a new Municipality Admin enforcing strict departmental isolation."""
    # Municipality Admin cannot provision other Municipality Admins
    if SystemRole.MUNICIPALITY_ADMIN in auth.roles and not (
        SystemRole.SUPERADMIN in auth.roles or SystemRole.NATIONAL_ADMIN in auth.roles or SystemRole.DEPARTMENT_ADMIN in auth.roles
    ):
        raise AuthorizationError(
            "Los administradores municipales no tienen facultades para aprovisionar otros administradores.",
            code="PERMISSION_DENIED",
        )

    service = MunicipalityAdminService(session=db)
    caller_dept_id = (
        uuid.UUID(auth.scope.department_id)
        if (auth.scope.is_department() and SystemRole.DEPARTMENT_ADMIN in auth.roles and auth.scope.department_id)
        else None
    )

    admin = await service.create_municipality_admin(
        payload=payload,
        actor_id=current_user.id,
        actor_ip=request.client.host if request.client else "0.0.0.0",
        correlation_id=request.headers.get("X-Correlation-ID"),
        caller_department_id=caller_dept_id,
    )
    await db.commit()
    return admin


@router.patch(
    "/{user_id}/status",
    response_model=MunicipalityAdminResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar estado operativo del administrador municipal",
    description="Activa o desactiva la cuenta del administrador municipal revocando sesiones activas al desactivar.",
    dependencies=[Depends(require_permission("municipality_admins", "update"))],
)
async def update_municipality_admin_status(
    user_id: uuid.UUID,
    payload: MunicipalityAdminStatusUpdateRequest,
    current_user: CurrentUserDep,
    auth: AuthContextDep,
    db: SessionDep,
    request: Request,
) -> MunicipalityAdminResponse:
    """Update active status of a municipality admin with session invalidation."""
    if SystemRole.MUNICIPALITY_ADMIN in auth.roles and not (
        SystemRole.SUPERADMIN in auth.roles or SystemRole.NATIONAL_ADMIN in auth.roles or SystemRole.DEPARTMENT_ADMIN in auth.roles
    ):
        raise AuthorizationError(
            "Los administradores municipales no tienen facultades para modificar el estado de otros administradores.",
            code="PERMISSION_DENIED",
        )

    service = MunicipalityAdminService(session=db)
    caller_dept_id = (
        uuid.UUID(auth.scope.department_id)
        if (auth.scope.is_department() and SystemRole.DEPARTMENT_ADMIN in auth.roles and auth.scope.department_id)
        else None
    )

    admin = await service.update_status(
        user_id=user_id,
        is_active=payload.is_active,
        actor_id=current_user.id,
        actor_ip=request.client.host if request.client else "0.0.0.0",
        reason=payload.reason,
        correlation_id=request.headers.get("X-Correlation-ID"),
        caller_department_id=caller_dept_id,
    )
    await db.commit()
    return admin


@router.patch(
    "/{user_id}/municipality",
    response_model=MunicipalityAdminResponse,
    status_code=status.HTTP_200_OK,
    summary="Reasignar administrador a otro municipio",
    description="Reasigna el administrador a un nuevo municipio e invalida tokens de sesión activos.",
    dependencies=[Depends(require_permission("municipality_admins", "update"))],
)
async def reassign_municipality_admin_municipality(
    user_id: uuid.UUID,
    payload: MunicipalityAdminReassignMunicipalityRequest,
    current_user: CurrentUserDep,
    auth: AuthContextDep,
    db: SessionDep,
    request: Request,
) -> MunicipalityAdminResponse:
    """Reassign municipality admin to another municipality within allowed authority."""
    if SystemRole.MUNICIPALITY_ADMIN in auth.roles and not (
        SystemRole.SUPERADMIN in auth.roles or SystemRole.NATIONAL_ADMIN in auth.roles or SystemRole.DEPARTMENT_ADMIN in auth.roles
    ):
        raise AuthorizationError(
            "Los administradores municipales no tienen facultades para reasignar administradores a otros municipios.",
            code="PERMISSION_DENIED",
        )

    service = MunicipalityAdminService(session=db)
    caller_dept_id = (
        uuid.UUID(auth.scope.department_id)
        if (auth.scope.is_department() and SystemRole.DEPARTMENT_ADMIN in auth.roles and auth.scope.department_id)
        else None
    )

    admin = await service.reassign_municipality(
        user_id=user_id,
        new_municipality_id=payload.new_municipality_id,
        actor_id=current_user.id,
        actor_ip=request.client.host if request.client else "0.0.0.0",
        reason=payload.reason,
        correlation_id=request.headers.get("X-Correlation-ID"),
        caller_department_id=caller_dept_id,
    )
    await db.commit()
    return admin


@router.post(
    "/{user_id}/resend-invitation",
    response_model=MunicipalityAdminInvitationResponse,
    status_code=status.HTTP_200_OK,
    summary="Reenviar invitación a administrador municipal",
    description="Invalida invitaciones pendientes anteriores y genera un nuevo enlace de activación de un solo uso.",
    dependencies=[Depends(require_permission("municipality_admins", "create"))],
)
async def resend_municipality_admin_invitation(
    user_id: uuid.UUID,
    request: Request,
    db: SessionDep,
    auth: AuthContextDep,
) -> MunicipalityAdminInvitationResponse:
    """Resend a one-time invitation token for an existing municipality administrator."""
    if SystemRole.MUNICIPALITY_ADMIN in auth.roles and not (
        SystemRole.SUPERADMIN in auth.roles or SystemRole.NATIONAL_ADMIN in auth.roles or SystemRole.DEPARTMENT_ADMIN in auth.roles
    ):
        raise AuthorizationError(
            "Los administradores municipales no tienen facultades para reenviar invitaciones a otros administradores.",
            code="PERMISSION_DENIED",
        )

    service = MunicipalityAdminService(session=db)
    caller_dept_id = (
        uuid.UUID(auth.scope.department_id)
        if (auth.scope.is_department() and SystemRole.DEPARTMENT_ADMIN in auth.roles and auth.scope.department_id)
        else None
    )

    result = await service.resend_invitation(
        user_id=user_id,
        actor_id=auth.user_id,
        actor_ip=request.client.host if request.client else "0.0.0.0",
        correlation_id=request.headers.get("X-Correlation-ID"),
        caller_department_id=caller_dept_id,
    )
    invitation, raw_token = result
    user = getattr(result, "user", None) or invitation.user
    municipality = getattr(result, "municipality", None) or invitation.municipality
    muni_code = municipality.code
    muni_name = municipality.name
    user_email = user.email
    invitation_id = invitation.id
    municipality_id = invitation.municipality_id
    uid = invitation.user_id
    expires_at = invitation.expires_at
    is_used = invitation.is_used
    delivery_status = getattr(result, "delivery_status", EmailDeliveryStatus.EMAIL_NOT_CONFIGURED)
    settings = get_settings()
    activation_url = getattr(result, "activation_url", None) if settings.is_development else None
    disclosed_token = raw_token if (raw_token and settings.is_development) else None

    await db.commit()

    return MunicipalityAdminInvitationResponse(
        invitation_id=invitation_id,
        municipality_id=municipality_id,
        municipality_code=muni_code,
        municipality_name=muni_name,
        user_id=uid,
        email=user_email,
        expires_at=expires_at,
        is_used=is_used,
        raw_invitation_token=disclosed_token,
        email_delivery_status=delivery_status,
        invitation_url=activation_url,
    )

