"""
PEVN Backend — Institutions API Endpoints

Handles institution profile inspection and multi-tenant organizational queries.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import (
    AuthContextDep,
    CurrentUserDep,
    SessionDep,
    require_permission,
)
from app.core.security.authorization import authorization_service
from app.core.security.interfaces import OrganizationalScope
from app.exceptions.errors import NotFoundError
from app.models.institution import Institution
from app.schemas.institution import InstitutionResponse

router = APIRouter(prefix="/institutions", tags=["Institutions"])


@router.get(
    "/me",
    response_model=InstitutionResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener institución del usuario autenticado",
    description=(
        "Devuelve la información de la institución educativa a la cual "
        "pertenece el usuario en sesión."
    ),
)
async def get_my_institution(
    current_user: CurrentUserDep,
    db: SessionDep,
) -> InstitutionResponse:
    if not current_user.institution_id:
        raise NotFoundError("El usuario no tiene una institución educativa asociada.")

    query = (
        select(Institution)
        .where(Institution.id == current_user.institution_id)
        .options(selectinload(Institution.campuses))
    )
    result = await db.execute(query)
    institution = result.scalar_one_or_none()

    if not institution:
        raise NotFoundError("Institución educativa no encontrada.")

    return InstitutionResponse.model_validate(institution)


@router.get(
    "/{institution_id}",
    response_model=InstitutionResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar institución por ID",
    description=(
        "Devuelve la información de una institución verificando que el "
        "usuario tenga permisos dentro de su alcance organizacional."
    ),
)
async def get_institution_by_id(
    institution_id: uuid.UUID,
    db: SessionDep,
    auth: Annotated[
        AuthContextDep, Depends(require_permission("institutions", "read"))
    ],
) -> InstitutionResponse:
    # Validate organizational scope barrier (prevent cross-tenant access)
    target_scope = OrganizationalScope(institution_id=str(institution_id))
    await authorization_service.require(
        auth,
        required_permission=auth.permissions[0] if auth.permissions else None,  # type: ignore[arg-type]
        target_scope=target_scope,
    )

    query = (
        select(Institution)
        .where(Institution.id == institution_id)
        .options(selectinload(Institution.campuses))
    )
    result = await db.execute(query)
    institution = result.scalar_one_or_none()

    if not institution:
        raise NotFoundError("Institución educativa no encontrada.")

    return InstitutionResponse.model_validate(institution)
