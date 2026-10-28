"""
PEVN Backend — FastAPI Dependencies

Reusable FastAPI dependency functions for database sessions, settings,
authentication context, and centralized authorization enforcement.
"""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends, Header, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.audit.interfaces import IAuditService
from app.audit.service import audit_service
from app.core.config import Settings, get_settings
from app.core.security.authorization import authorization_service
from app.core.security.interfaces import (
    AuthorizationContext,
    SystemRole,
)
from app.core.security.interfaces import (
    Permission as SecurityPermission,
)
from app.core.security.tokens import token_service
from app.db.session import get_async_session
from app.exceptions.errors import AuthenticationError, AuthorizationError
from app.models.institution import Institution
from app.models.role import Role, UserRole
from app.models.territory import Municipality
from app.models.user import User
from app.services.auth_service import auth_service

# Security scheme for Swagger UI
security_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_async_session)],
    auth_header: Annotated[
        HTTPAuthorizationCredentials | None, Depends(security_bearer)
    ],
) -> User:
    """
    Extract and validate the authenticated User from the Bearer token.
    """
    token: str | None = None
    if auth_header:
        token = auth_header.credentials
    else:
        # Fallback to Authorization header if HTTPBearer didn't capture it
        raw_auth = request.headers.get("Authorization")
        if raw_auth and raw_auth.startswith("Bearer "):
            token = raw_auth[7:].strip()

    if not token:
        raise AuthenticationError("Autenticación requerida.")

    payload = await token_service.verify_token(token, expected_type="access")
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise AuthenticationError(
            "Token de autenticación no contiene identidad de usuario."
        )

    try:
        user_uuid = uuid.UUID(user_id_str)
    except (ValueError, TypeError) as exc:
        raise AuthenticationError(
            "Identificador de usuario inválido en token."
        ) from exc

    query = (
        select(User)
        .where(User.id == user_uuid)
        .options(
            selectinload(User.user_roles)
            .selectinload(UserRole.role)
            .selectinload(Role.permissions),
            selectinload(User.user_roles)
            .selectinload(UserRole.department),
            selectinload(User.user_roles)
            .selectinload(UserRole.municipality)
            .selectinload(Municipality.department),
            selectinload(User.institution),
        )
    )
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise AuthenticationError("Usuario no encontrado.")

    if not user.is_active:
        raise AuthenticationError("Cuenta de usuario inactiva.")

    if user.is_locked:
        raise AuthenticationError("Cuenta de usuario bloqueada temporalmente.")

    return user


async def get_auth_context(
    request: Request,
    user: Annotated[User, Depends(get_current_user)],
) -> AuthorizationContext:
    """
    Build and return the complete AuthorizationContext for the current request.
    """
    ctx = auth_service.build_auth_context(user)
    header_val = request.headers.get("x-institution-context") or request.headers.get("x-institution-id")
    if header_val:
        ctx.extra["institution_context_header"] = header_val
    return ctx


def require_permission(
    resource: str, action: str
) -> Callable[..., Awaitable[AuthorizationContext]]:
    """
    Dependency factory to enforce an atomic permission on a route.

    Usage:
        @router.get(
            "/items",
            dependencies=[Depends(require_permission("items", "read"))]
        )
        async def read_items(auth: AuthContextDep):
            ...
    """
    req_permission = SecurityPermission(resource=resource, action=action)

    async def _permission_dependency(
        context: Annotated[AuthorizationContext, Depends(get_auth_context)],
    ) -> AuthorizationContext:
        await authorization_service.require(context, req_permission)
        return context

    return _permission_dependency


def require_role(
    role_name: str | SystemRole,
) -> Callable[..., Awaitable[AuthorizationContext]]:
    """
    Dependency factory to enforce a specific system role.
    """
    target_role = (
        role_name if isinstance(role_name, SystemRole) else SystemRole(role_name)
    )

    async def _role_dependency(
        context: Annotated[AuthorizationContext, Depends(get_auth_context)],
    ) -> AuthorizationContext:
        if SystemRole.SUPERADMIN in context.roles:
            return context

        if target_role not in context.roles:
            raise AuthorizationError(
                f"Se requiere el rol {target_role.value} para acceder a este recurso."
            )
        return context

    return _role_dependency


def get_client_ip(
    request: Request,
    x_forwarded_for: Annotated[str | None, Header()] = None,
) -> str:
    """Extract client IP safely adhering to TRUSTED_PROXIES right-to-left resolution."""
    if hasattr(request.state, "client_ip") and request.state.client_ip:
        return str(request.state.client_ip)

    from app.core.security.rate_limiter import resolve_client_ip

    settings = get_settings()
    direct_peer = request.client.host if request.client else "127.0.0.1"
    trusted_proxies = (
        settings.TRUSTED_PROXIES
        if isinstance(settings.TRUSTED_PROXIES, list)
        else [settings.TRUSTED_PROXIES]
    )
    return resolve_client_ip(direct_peer, x_forwarded_for, trusted_proxies)


async def resolve_institution_id(
    db: AsyncSession,
    auth: AuthorizationContext,
    current_user: User,
    institution_id_override: uuid.UUID | str | None = None,
    request: Request | None = None,
) -> uuid.UUID:
    """
    Resolve active institution context adhering to strict tenant and territorial isolation.

    - National scope (SUPERADMIN, NATIONAL_ADMIN):
      Uses institution_id_override or current_user.institution_id across any institution.
    - Department scope (DEPARTMENT_ADMIN):
      Uses institution_id_override ONLY if the institution belongs to the administrator's department.
      Attempts to access an institution outside the department raise HTTP 403 (PERMISSION_DENIED).
      If no override is provided and user has no direct institution_id, raises HTTP 403.
    - Institutional scope (RECTOR, COORDINATOR, TEACHER, STUDENT, GUARDIAN):
      Restricted to current_user.institution_id.
    """
    target_inst_id: uuid.UUID | None = None
    if institution_id_override is not None:
        if isinstance(institution_id_override, str):
            try:
                target_inst_id = uuid.UUID(institution_id_override)
            except (ValueError, TypeError):
                target_inst_id = None
        else:
            target_inst_id = institution_id_override
    elif request is not None:
        header_val = request.headers.get("x-institution-context") or request.headers.get("x-institution-id")
        if header_val:
            try:
                target_inst_id = uuid.UUID(header_val)
            except (ValueError, TypeError):
                target_inst_id = None
    elif hasattr(auth, "extra") and auth.extra.get("institution_context_header"):
        try:
            target_inst_id = uuid.UUID(auth.extra["institution_context_header"])
        except (ValueError, TypeError):
            target_inst_id = None

    if (
        SystemRole.SUPERADMIN in auth.roles
        or SystemRole.NATIONAL_ADMIN in auth.roles
        or auth.scope.is_national()
    ):
        if target_inst_id:
            return target_inst_id
        if current_user.institution_id:
            return current_user.institution_id
        raise AuthorizationError("Contexto institucional no disponible.")

    if auth.scope.is_department():
        if target_inst_id:
            dept_uuid = uuid.UUID(auth.scope.department_id)
            inst_query = (
                select(Institution.id)
                .join(Municipality, Institution.municipality_id == Municipality.id)
                .where(
                    Institution.id == target_inst_id,
                    Municipality.department_id == dept_uuid,
                )
            )
            inst_found = (await db.execute(inst_query)).scalar_one_or_none()
            if not inst_found:
                raise AuthorizationError(
                    "No está autorizado para acceder a datos de una institución fuera de su jurisdicción departamental.",
                    code="PERMISSION_DENIED",
                )
            return target_inst_id
        if current_user.institution_id:
            return current_user.institution_id
        raise AuthorizationError(
            "Contexto institucional requerido para la consulta. Seleccione una institución educativa dentro de su jurisdicción departamental.",
            code="INSTITUTION_CONTEXT_REQUIRED",
        )

    if auth.scope.is_municipality():
        if target_inst_id:
            muni_uuid = uuid.UUID(auth.scope.municipality_id)
            inst_query = (
                select(Institution.id)
                .where(
                    Institution.id == target_inst_id,
                    Institution.municipality_id == muni_uuid,
                )
            )
            inst_found = (await db.execute(inst_query)).scalar_one_or_none()
            if not inst_found:
                raise AuthorizationError(
                    "No está autorizado para acceder a datos de una institución fuera de su jurisdicción municipal.",
                    code="PERMISSION_DENIED",
                )
            return target_inst_id
        if current_user.institution_id:
            return current_user.institution_id
        raise AuthorizationError(
            "Contexto institucional requerido para la consulta. Seleccione una institución educativa dentro de su jurisdicción municipal.",
            code="INSTITUTION_CONTEXT_REQUIRED",
        )

    if current_user.institution_id:
        return current_user.institution_id

    raise AuthorizationError("Contexto institucional no disponible.")


async def assert_coordinator_delegation_allowed(
    db: AsyncSession,
    auth: AuthorizationContext,
    institution_id: uuid.UUID,
) -> None:
    """
    Enforce Rector-controlled Coordinator delegation policy.

    If the actor is a Coordinator (and not a Rector, Director, or SuperAdmin),
    the target institution must have coordinator_delegation_enabled == True.
    Otherwise, raises HTTP 403 AuthorizationError (PERMISSION_DENIED).
    """
    role_names = {r.value if isinstance(r, SystemRole) else str(r).lower() for r in auth.roles}
    is_coordinator = bool({"coordinator", "academic_coordinator"} & role_names)
    is_rector = bool(
        {"rector", "institution_admin"} & role_names
    )

    if is_coordinator and not is_rector:
        inst_stmt = select(Institution.coordinator_delegation_enabled).where(Institution.id == institution_id)
        result = await db.execute(inst_stmt)
        delegation_enabled = result.scalar_one_or_none()
        if not delegation_enabled:
            raise AuthorizationError(
                "La delegación operativa para coordinadores se encuentra inhabilitada en esta institución. El Rector debe habilitar esta opción en la configuración institucional.",
                code="PERMISSION_DENIED",
            )


# Type aliases for dependency injection
SessionDep = Annotated[AsyncSession, Depends(get_async_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]
AuthContextDep = Annotated[AuthorizationContext, Depends(get_auth_context)]
ClientIpDep = Annotated[str, Depends(get_client_ip)]
AuditServiceDep = Annotated[IAuditService, Depends(lambda: audit_service)]

__all__ = [
    "AuditServiceDep",
    "AuthContextDep",
    "ClientIpDep",
    "CurrentUserDep",
    "SessionDep",
    "SettingsDep",
    "assert_coordinator_delegation_allowed",
    "get_async_session",
    "get_auth_context",
    "get_client_ip",
    "get_current_user",
    "get_settings",
    "require_permission",
    "require_role",
    "resolve_institution_id",
]
