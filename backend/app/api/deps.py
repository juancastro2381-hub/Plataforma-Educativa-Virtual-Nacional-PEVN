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
from app.models.role import Role, UserRole
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
    user: Annotated[User, Depends(get_current_user)],
) -> AuthorizationContext:
    """
    Build and return the complete AuthorizationContext for the current request.
    """
    return auth_service.build_auth_context(user)


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
    """Extract client IP safely from request or X-Forwarded-For header."""
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "127.0.0.1"


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
    "get_async_session",
    "get_auth_context",
    "get_client_ip",
    "get_current_user",
    "get_settings",
    "require_permission",
    "require_role",
]
