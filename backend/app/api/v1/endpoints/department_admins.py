"""
PEVN Backend — Department Administrators API Controller

REST Controller for complete, secure, and auditable DEPARTMENT_ADMIN lifecycle:
  - List and search department administrators
  - Canonical department selector data
  - Create new department administrator with strict territorial assignment
  - Profile modification
  - Explicit department reassignment with session token revocation
  - Controlled activation / deactivation
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query, Request, status

from app.api.deps import (
    AuthContextDep,
    CurrentUserDep,
    SessionDep,
    get_auth_context,
    require_permission,
)
from app.core.security.interfaces import SystemRole
from app.exceptions.errors import AuthorizationError
from app.schemas.department_admin import (
    DepartmentAdminCreateRequest,
    DepartmentAdminInvitationResponse,
    DepartmentAdminKPIs,
    DepartmentAdminListResponse,
    DepartmentAdminReassignDepartmentRequest,
    DepartmentAdminResponse,
    DepartmentAdminStatusUpdateRequest,
    DepartmentAdminUpdateRequest,
    DepartmentOptionResponse,
)
from app.services.department_admin_service import DepartmentAdminService
from app.services.email_service import EmailDeliveryStatus

router = APIRouter()


@router.get(
    "/departments",
    response_model=list[DepartmentOptionResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar departamentos canónicos",
    description="Devuelve el catálogo de departamentos canónicos para alimentar selectores de territorio.",
)
async def list_canonical_departments(
    db: SessionDep,
    auth: AuthContextDep,
) -> list[DepartmentOptionResponse]:
    """List canonical departments for dropdown selectors."""
    service = DepartmentAdminService(session=db)
    return await service.list_departments()


@router.get(
    "/kpis",
    response_model=DepartmentAdminKPIs,
    status_code=status.HTTP_200_OK,
    summary="Obtener métricas y KPIs de administradores departamentales",
    description="Devuelve métricas autoritativas calculadas en el servidor sobre la población de administradores departamentales.",
    dependencies=[Depends(require_permission("department_admins", "read"))],
)
async def get_department_admin_kpis(
    db: SessionDep,
    auth: AuthContextDep,
) -> DepartmentAdminKPIs:
    """Retrieve authoritative server-side KPIs for department administrators."""
    service = DepartmentAdminService(session=db)
    return await service.get_kpis()


@router.get(
    "",
    response_model=DepartmentAdminListResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar y buscar administradores departamentales",
    description="Permite buscar y filtrar administradores departamentales por territorio y estado.",
    dependencies=[Depends(require_permission("department_admins", "read"))],
)
async def list_department_admins(
    db: SessionDep,
    auth: AuthContextDep,
    department_id: Annotated[
        uuid.UUID | None,
        Query(description="Filtrar por UUID de departamento asignado"),
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
    page_size: Annotated[int, Query(ge=1, le=100, description="Registros por página")] = 20,
) -> DepartmentAdminListResponse:
    """List all department administrators matching filter criteria."""
    service = DepartmentAdminService(session=db)
    items, total, kpis = await service.list_department_admins(
        department_id=department_id,
        is_active=is_active,
        search=search,
        page=page,
        page_size=page_size,
    )
    return DepartmentAdminListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        kpis=kpis,
    )



@router.get(
    "/{user_id}",
    response_model=DepartmentAdminResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar administrador departamental por ID",
    description="Obtiene el perfil y asignación territorial de un administrador departamental.",
)
async def get_department_admin_by_id(
    user_id: uuid.UUID,
    db: SessionDep,
    auth: AuthContextDep,
) -> DepartmentAdminResponse:
    """
    Retrieve single department admin. Higher-level administrators can view all;
    a department admin can view only their own record.
    """
    has_read_perm = (
        auth.has_wildcard()
        or SystemRole.SUPERADMIN in auth.roles
        or SystemRole.NATIONAL_ADMIN in auth.roles
        or any(p.resource == "department_admins" and p.action in ("read", "*") for p in auth.permissions)
    )

    if not has_read_perm:
        if auth.user_id != user_id:
            raise AuthorizationError(
                "No está autorizado para consultar la información de este administrador departamental.",
                code="PERMISSION_DENIED",
            )

    service = DepartmentAdminService(session=db)
    return await service.get_department_admin(user_id=user_id)


@router.post(
    "",
    response_model=DepartmentAdminResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear administrador departamental",
    description="Aprovisiona un nuevo usuario con rol DEPARTMENT_ADMIN y ámbito territorial estricto.",
    dependencies=[Depends(require_permission("department_admins", "create"))],
)
async def create_department_admin(
    payload: DepartmentAdminCreateRequest,
    request: Request,
    db: SessionDep,
    auth: AuthContextDep,
    x_correlation_id: Annotated[str | None, Header()] = None,
) -> DepartmentAdminResponse:
    """
    Create a new DEPARTMENT_ADMIN.
    Server-side authoritative: role is unconditionally set to department_admin,
    ignoring any client attempt to elevate privileges.
    """
    service = DepartmentAdminService(session=db)
    client_ip = request.client.host if request.client else "0.0.0.0"

    admin_res = await service.create_department_admin(
        payload=payload,
        actor_id=auth.user_id,
        actor_ip=client_ip,
        correlation_id=x_correlation_id,
    )
    await db.commit()
    return admin_res


@router.patch(
    "/{user_id}",
    response_model=DepartmentAdminResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar perfil de administrador departamental",
    description="Modifica datos de perfil de un administrador departamental existente.",
    dependencies=[Depends(require_permission("department_admins", "update"))],
)
async def update_department_admin(
    user_id: uuid.UUID,
    payload: DepartmentAdminUpdateRequest,
    request: Request,
    db: SessionDep,
    auth: AuthContextDep,
    x_correlation_id: Annotated[str | None, Header()] = None,
) -> DepartmentAdminResponse:
    """Update profile attributes."""
    service = DepartmentAdminService(session=db)
    client_ip = request.client.host if request.client else "0.0.0.0"

    admin_res = await service.update_department_admin(
        user_id=user_id,
        payload=payload,
        actor_id=auth.user_id,
        actor_ip=client_ip,
        correlation_id=x_correlation_id,
    )
    await db.commit()
    return admin_res


@router.patch(
    "/{user_id}/department",
    response_model=DepartmentAdminResponse,
    status_code=status.HTTP_200_OK,
    summary="Reasignar departamento territorial",
    description="Reasigna un administrador departamental a otro departamento canónico con invalidación de sesión.",
    dependencies=[Depends(require_permission("department_admins", "update"))],
)
async def reassign_department(
    user_id: uuid.UUID,
    payload: DepartmentAdminReassignDepartmentRequest,
    request: Request,
    db: SessionDep,
    auth: AuthContextDep,
    x_correlation_id: Annotated[str | None, Header()] = None,
) -> DepartmentAdminResponse:
    """
    Explicitly reassign the administrator's department.
    Immediately invalidates active refresh tokens to force context refresh.
    """
    service = DepartmentAdminService(session=db)
    client_ip = request.client.host if request.client else "0.0.0.0"

    admin_res = await service.reassign_department(
        user_id=user_id,
        new_department_id=payload.new_department_id,
        actor_id=auth.user_id,
        actor_ip=client_ip,
        reason=payload.reason,
        correlation_id=x_correlation_id,
    )
    await db.commit()
    return admin_res


@router.patch(
    "/{user_id}/status",
    response_model=DepartmentAdminResponse,
    status_code=status.HTTP_200_OK,
    summary="Activar o desactivar administrador departamental",
    description="Modifica el estado operativo del administrador con revocación de sesión en caso de baja.",
    dependencies=[Depends(require_permission("department_admins", "update"))],
)
async def update_status(
    user_id: uuid.UUID,
    payload: DepartmentAdminStatusUpdateRequest,
    request: Request,
    db: SessionDep,
    auth: AuthContextDep,
    x_correlation_id: Annotated[str | None, Header()] = None,
) -> DepartmentAdminResponse:
    """Activate or deactivate a department administrator."""
    service = DepartmentAdminService(session=db)
    client_ip = request.client.host if request.client else "0.0.0.0"

    admin_res = await service.update_status(
        user_id=user_id,
        is_active=payload.is_active,
        actor_id=auth.user_id,
        actor_ip=client_ip,
        reason=payload.reason,
        correlation_id=x_correlation_id,
    )
    await db.commit()
    return admin_res


@router.post(
    "/{user_id}/resend-invitation",
    response_model=DepartmentAdminInvitationResponse,
    status_code=status.HTTP_200_OK,
    summary="Reenviar invitación a administrador departamental",
    description="Invalida invitaciones pendientes anteriores y genera un nuevo enlace de activación de un solo uso.",
    dependencies=[Depends(require_permission("department_admins", "create"))],
)
async def resend_department_admin_invitation(
    user_id: uuid.UUID,
    request: Request,
    db: SessionDep,
    auth: AuthContextDep,
    x_correlation_id: Annotated[str | None, Header()] = None,
) -> DepartmentAdminInvitationResponse:
    """Resend a one-time invitation token for an existing department administrator."""
    service = DepartmentAdminService(session=db)
    client_ip = request.client.host if request.client else "0.0.0.0"

    result = await service.resend_invitation(
        user_id=user_id,
        actor_id=auth.user_id,
        actor_ip=client_ip,
        correlation_id=x_correlation_id,
    )
    invitation, raw_token = result
    user = getattr(result, "user", None) or invitation.user
    dept = getattr(result, "department", None) or invitation.department
    dept_code = dept.code
    dept_name = dept.name
    user_email = user.email
    invitation_id = invitation.id
    department_id = invitation.department_id
    user_id = invitation.user_id
    expires_at = invitation.expires_at
    is_used = invitation.is_used
    delivery_status = getattr(result, "delivery_status", EmailDeliveryStatus.EMAIL_NOT_CONFIGURED)
    activation_url = getattr(result, "activation_url", f"/invitation/accept?token={raw_token}")

    await db.commit()

    return DepartmentAdminInvitationResponse(
        invitation_id=invitation_id,
        department_id=department_id,
        department_code=dept_code,
        department_name=dept_name,
        user_id=user_id,
        email=user_email,
        expires_at=expires_at,
        is_used=is_used,
        raw_invitation_token=raw_token,
        email_delivery_status=delivery_status,
        invitation_url=activation_url,
    )

