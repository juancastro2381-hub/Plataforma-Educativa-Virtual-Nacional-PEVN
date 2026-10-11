"""
PEVN Backend — Users API Endpoints

REST Controller for tenant-isolated user search, listing, and identity lookup,
delegating domain queries to UserService.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from sqlalchemy import select

from app.api.deps import (
    AuthContextDep,
    CurrentUserDep,
    SessionDep,
    require_permission,
)
from app.core.security.interfaces import SystemRole
from app.exceptions.errors import AuthorizationError
from app.models.institution import Institution
from app.models.territory import Municipality
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
    target_institution_id: uuid.UUID | None = None
    target_department_id: uuid.UUID | None = None
    target_municipality_id: uuid.UUID | None = None

    if auth.scope.is_national() or SystemRole.SUPERADMIN in auth.roles or SystemRole.NATIONAL_ADMIN in auth.roles:
        target_institution_id = institution_id
    elif auth.scope.is_municipality():
        muni_uuid = uuid.UUID(auth.scope.municipality_id)
        if institution_id is not None:
            # Verify institution is in this municipality
            inst_query = (
                select(Institution.id)
                .where(Institution.id == institution_id, Institution.municipality_id == muni_uuid)
            )
            inst_found = (await db.execute(inst_query)).scalar_one_or_none()
            if not inst_found:
                raise AuthorizationError(
                    "No está autorizado para consultar usuarios de una institución fuera de su jurisdicción municipal.",
                    code="PERMISSION_DENIED",
                )
            target_institution_id = institution_id
        else:
            target_municipality_id = muni_uuid
    elif auth.scope.is_department():
        dept_uuid = uuid.UUID(auth.scope.department_id)
        if institution_id is not None:
            # Verify institution is in this department
            inst_query = (
                select(Institution.id)
                .join(Municipality, Institution.municipality_id == Municipality.id)
                .where(Institution.id == institution_id, Municipality.department_id == dept_uuid)
            )
            inst_found = (await db.execute(inst_query)).scalar_one_or_none()
            if not inst_found:
                raise AuthorizationError(
                    "No está autorizado para consultar usuarios de una institución fuera de su jurisdicción departamental.",
                    code="PERMISSION_DENIED",
                )
            target_institution_id = institution_id
        else:
            target_department_id = dept_uuid
    elif current_user.institution_id:
        target_institution_id = current_user.institution_id
    else:
        raise AuthorizationError("Contexto institucional no disponible.")

    service = UserService(session=db)
    users, total = await service.list_users(
        institution_id=target_institution_id,
        department_id=target_department_id,
        municipality_id=target_municipality_id,
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
    target_institution_id: uuid.UUID | None = None
    target_department_id: uuid.UUID | None = None
    target_municipality_id: uuid.UUID | None = None

    if auth.scope.is_national() or SystemRole.SUPERADMIN in auth.roles or SystemRole.NATIONAL_ADMIN in auth.roles:
        target_institution_id = institution_id
    elif auth.scope.is_municipality():
        target_municipality_id = uuid.UUID(auth.scope.municipality_id)
    elif auth.scope.is_department():
        target_department_id = uuid.UUID(auth.scope.department_id)
    elif current_user.institution_id:
        target_institution_id = current_user.institution_id
    else:
        raise AuthorizationError("Contexto institucional no disponible.")

    service = UserService(session=db)
    user = await service.get_user_by_id(
        user_id=user_id,
        institution_id=target_institution_id,
        department_id=target_department_id,
        municipality_id=target_municipality_id,
    )

    return UserResponse.model_validate(user)
