"""
PEVN Backend — Users API Endpoints

REST Controller for tenant-isolated user search, listing, and identity lookup,
delegating domain queries to UserService.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import (
    AuthContextDep,
    CurrentUserDep,
    SessionDep,
    require_permission,
)
from app.core.security.interfaces import SystemRole
from app.exceptions.errors import AuthorizationError
from app.schemas.user import UserListResponse, UserResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


def _resolve_institution_id(
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    institution_id_override: uuid.UUID | None = None,
) -> uuid.UUID | None:
    """Resolve active institution context adhering to tenant isolation."""
    if (
        SystemRole.SUPERADMIN in auth.roles
        or SystemRole.NATIONAL_ADMIN in auth.roles
        or auth.scope.is_national()
    ):
        return institution_id_override

    if current_user.institution_id:
        return current_user.institution_id

    raise AuthorizationError("Contexto institucional no disponible.")


@router.get(
    "",
    response_model=UserListResponse,
    status_code=status.HTTP_200_OK,
    summary="Buscar y listar usuarios institucionales",
    description="Permite buscar usuarios por documento, nombre o correo dentro del alcance institucional del actor.",
    dependencies=[Depends(require_permission("users", "read"))],
)
async def list_users(
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    search: Annotated[
        str | None,
        Query(description="Búsqueda por número de documento, nombre, apellido, correo o nombre de usuario"),
    ] = None,
    is_active: Annotated[
        bool | None,
        Query(description="Filtrar por estado activo del usuario"),
    ] = True,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override de institución (solo Superadmin / Administrador Nacional)"),
    ] = None,
    page: Annotated[int, Query(ge=1, description="Página actual")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Registros por página")] = 20,
) -> UserListResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)

    service = UserService(session=db)
    users, total = await service.list_users(
        institution_id=target_institution_id,
        search=search,
        is_active=is_active,
        page=page,
        page_size=page_size,
    )

    return UserListResponse(
        items=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar usuario por ID",
    description="Obtiene los datos públicos de un usuario validando el aislamiento de tenant.",
    dependencies=[Depends(require_permission("users", "read"))],
)
async def get_user_by_id(
    user_id: uuid.UUID,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override de institución (solo Superadmin / Administrador Nacional)"),
    ] = None,
) -> UserResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)

    service = UserService(session=db)
    user = await service.get_user_by_id(
        user_id=user_id,
        institution_id=target_institution_id,
    )

    return UserResponse.model_validate(user)
