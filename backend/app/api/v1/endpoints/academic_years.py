"""
PEVN Backend — Academic Years API Endpoints

REST Controller for managing academic school years, term periods,
and year lifecycle transitions, delegating business rules to AcademicYearService.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select

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
from app.models.academic_year import AcademicYear, AcademicYearStatus
from app.schemas.academic import (
    AcademicYearCreateRequest,
    AcademicYearListResponse,
    AcademicYearResponse,
)
from app.services.academic_year_service import AcademicYearService

router = APIRouter(prefix="/academic-years", tags=["Academic Years"])


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
    response_model=AcademicYearResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear año lectivo escolar",
    description="Crea un nuevo año lectivo para la institución educativa.",
    dependencies=[Depends(require_permission("academic_years", "create"))],
)
async def create_academic_year(
    payload: AcademicYearCreateRequest,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    client_ip: ClientIpDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> AcademicYearResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    correlation_id = correlation_id_ctx.get()

    service = AcademicYearService(session=db)
    academic_year = await service.create_academic_year(
        institution_id=target_institution_id,
        year=payload.year,
        name=payload.name,
        start_date=payload.start_date,
        end_date=payload.end_date,
        calendar_type=payload.calendar_type,
        status=payload.status,
        actor_id=current_user.id,
        actor_ip=client_ip,
        correlation_id=correlation_id,
    )
    await db.commit()
    await db.refresh(academic_year)
    return AcademicYearResponse.model_validate(academic_year)


@router.get(
    "/{year_id}",
    response_model=AcademicYearResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar año lectivo por ID",
    description="Obtiene los detalles de un año lectivo verificando tenant.",
    dependencies=[Depends(require_permission("academic_years", "read"))],
)
async def get_academic_year(
    year_id: uuid.UUID,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> AcademicYearResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    service = AcademicYearService(session=db)
    academic_year = await service.get_academic_year_by_id(
        year_id=year_id,
        institution_id=target_institution_id,
    )
    return AcademicYearResponse.model_validate(academic_year)


@router.get(
    "",
    response_model=AcademicYearListResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar años lectivos",
    description="Lista los años lectivos de la institución con filtros.",
    dependencies=[Depends(require_permission("academic_years", "read"))],
)
async def list_academic_years(
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    status_filter: Annotated[
        AcademicYearStatus | None,
        Query(alias="status", description="Filtrar por estado"),
    ] = None,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> AcademicYearListResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)

    query = select(AcademicYear).where(
        AcademicYear.institution_id == target_institution_id
    )
    if status_filter:
        query = query.where(AcademicYear.status == status_filter)

    query = query.order_by(AcademicYear.year.desc())
    result = await db.execute(query)
    years = list(result.scalars().all())

    return AcademicYearListResponse(
        items=[AcademicYearResponse.model_validate(y) for y in years],
        total=len(years),
    )


@router.post(
    "/{year_id}/activate",
    response_model=AcademicYearResponse,
    status_code=status.HTTP_200_OK,
    summary="Activar año lectivo",
    description="Transiciona el estado del año lectivo a ACTIVO.",
    dependencies=[Depends(require_permission("academic_years", "update"))],
)
async def activate_academic_year(
    year_id: uuid.UUID,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    client_ip: ClientIpDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> AcademicYearResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    correlation_id = correlation_id_ctx.get()

    service = AcademicYearService(session=db)
    academic_year = await service.activate_academic_year(
        year_id=year_id,
        institution_id=target_institution_id,
        actor_id=current_user.id,
        actor_ip=client_ip,
        correlation_id=correlation_id,
    )
    await db.commit()
    await db.refresh(academic_year)
    return AcademicYearResponse.model_validate(academic_year)


@router.post(
    "/{year_id}/close",
    response_model=AcademicYearResponse,
    status_code=status.HTTP_200_OK,
    summary="Cerrar año lectivo",
    description="Transiciona el estado del año lectivo a CERRADO.",
    dependencies=[Depends(require_permission("academic_years", "close"))],
)
async def close_academic_year(
    year_id: uuid.UUID,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    client_ip: ClientIpDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> AcademicYearResponse:
    target_institution_id = _resolve_institution_id(auth, current_user, institution_id)
    correlation_id = correlation_id_ctx.get()

    service = AcademicYearService(session=db)
    academic_year = await service.close_academic_year(
        year_id=year_id,
        institution_id=target_institution_id,
        actor_id=current_user.id,
        actor_ip=client_ip,
        correlation_id=correlation_id,
    )
    await db.commit()
    await db.refresh(academic_year)
    return AcademicYearResponse.model_validate(academic_year)
