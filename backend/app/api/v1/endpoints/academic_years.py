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
    resolve_institution_id,
)
from app.core.logging import correlation_id_ctx
from app.core.security.interfaces import SystemRole
from app.exceptions.errors import AuthorizationError
from app.models.academic_year import AcademicPeriod, AcademicYear, AcademicYearStatus
from app.schemas.academic import (
    AcademicPeriodCreateRequest,
    AcademicPeriodDirectCreateRequest,
    AcademicPeriodListResponse,
    AcademicPeriodResponse,
    AcademicYearCreateRequest,
    AcademicYearListResponse,
    AcademicYearResponse,
    PeriodTemplatePreviewRequest,
    PeriodTemplatePreviewResponse,
    PeriodTemplateProvisionRequest,
    PeriodTemplateProvisionResponse,
)
from app.services.academic_year_service import AcademicYearService

router = APIRouter(prefix="/academic-years", tags=["Academic Years"])


async def _resolve_institution_id(
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    institution_id_override: uuid.UUID | None = None,
) -> uuid.UUID:
    """Resolve active institution context adhering to tenant isolation."""
    return await resolve_institution_id(
        db=db,
        auth=auth,
        current_user=current_user,
        institution_id_override=institution_id_override,
    )


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
    target_institution_id = await _resolve_institution_id(db, auth, current_user, institution_id)
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
    target_institution_id = await _resolve_institution_id(db, auth, current_user, institution_id)
    service = AcademicYearService(session=db)
    academic_year = await service.get_academic_year_by_id(
        year_id=year_id,
        institution_id=target_institution_id,
    )
    return AcademicYearResponse.model_validate(academic_year)


@router.get(
    "/{year_id}/periods",
    response_model=AcademicPeriodListResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar períodos académicos de un año lectivo",
    description="Obtiene los períodos de evaluación académica para un año escolar.",
    dependencies=[Depends(require_permission("academic_years", "read"))],
)
async def list_academic_year_periods(
    year_id: uuid.UUID,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> AcademicPeriodListResponse:
    target_institution_id = await _resolve_institution_id(db, auth, current_user, institution_id)
    service = AcademicYearService(session=db)
    academic_year = await service.get_academic_year_by_id(
        year_id=year_id,
        institution_id=target_institution_id,
    )
    periods_stmt = (
        select(AcademicPeriod)
        .where(AcademicPeriod.academic_year_id == academic_year.id)
        .order_by(AcademicPeriod.period_number.asc())
    )
    periods = list((await db.execute(periods_stmt)).scalars().all())
    return AcademicPeriodListResponse(
        items=[AcademicPeriodResponse.model_validate(p) for p in periods],
        total=len(periods),
    )


@router.post(
    "/{year_id}/periods",
    response_model=AcademicPeriodResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear período académico para un año lectivo",
    description="Registra un nuevo período de evaluación dentro del año escolar.",
    dependencies=[Depends(require_permission("academic_periods", "create"))],
)
async def create_academic_year_period(
    year_id: uuid.UUID,
    payload: AcademicPeriodCreateRequest,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    client_ip: ClientIpDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> AcademicPeriodResponse:
    target_institution_id = await _resolve_institution_id(db, auth, current_user, institution_id)
    correlation_id = correlation_id_ctx.get()
    service = AcademicYearService(session=db)
    period = await service.create_academic_period(
        year_id=year_id,
        institution_id=target_institution_id,
        period_number=payload.period_number,
        name=payload.name,
        weight_percentage=payload.weight_percentage,
        start_date=payload.start_date,
        end_date=payload.end_date,
        actor_id=current_user.id,
        actor_ip=client_ip,
        correlation_id=correlation_id,
    )
    await db.commit()
    await db.refresh(period)
    return AcademicPeriodResponse.model_validate(period)


@router.post(
    "/{year_id}/periods/template-preview",
    response_model=PeriodTemplatePreviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Previsualizar plantilla de períodos académicos",
    description="Calcula una propuesta no destructiva de períodos para el año lectivo.",
    dependencies=[Depends(require_permission("academic_periods", "read"))],
)
async def preview_academic_year_period_template(
    year_id: uuid.UUID,
    payload: PeriodTemplatePreviewRequest,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> PeriodTemplatePreviewResponse:
    target_institution_id = await _resolve_institution_id(db, auth, current_user, institution_id)
    service = AcademicYearService(session=db)
    return await service.preview_period_template(
        year_id=year_id,
        institution_id=target_institution_id,
        template_type=payload.template_type,
        custom_period_count=payload.custom_period_count,
    )


@router.post(
    "/{year_id}/periods/template-provision",
    response_model=PeriodTemplateProvisionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Aprovisionar períodos académicos desde plantilla",
    description="Crea atómicamente los períodos validados y registra la conformidad SIEE.",
    dependencies=[Depends(require_permission("academic_periods", "create"))],
)
async def provision_academic_year_period_template(
    year_id: uuid.UUID,
    payload: PeriodTemplateProvisionRequest,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    client_ip: ClientIpDep,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin only"),
    ] = None,
) -> PeriodTemplateProvisionResponse:
    target_institution_id = await _resolve_institution_id(db, auth, current_user, institution_id)
    correlation_id = correlation_id_ctx.get()
    service = AcademicYearService(session=db)
    result = await service.provision_period_template(
        year_id=year_id,
        institution_id=target_institution_id,
        payload=payload,
        actor_id=current_user.id,
        actor_ip=client_ip,
        correlation_id=correlation_id,
    )
    await db.commit()
    return result


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
    target_institution_id = await _resolve_institution_id(db, auth, current_user, institution_id)

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
    target_institution_id = await _resolve_institution_id(db, auth, current_user, institution_id)
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
    target_institution_id = await _resolve_institution_id(db, auth, current_user, institution_id)
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


periods_router = APIRouter(prefix="/academic-periods", tags=["Academic Periods"])


@periods_router.get(
    "",
    response_model=AcademicPeriodListResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar períodos académicos",
    description="Obtiene los períodos de evaluación académica para la institución.",
    dependencies=[Depends(require_permission("academic_periods", "read"))],
)
async def list_academic_periods(
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    year_id: Annotated[uuid.UUID | None, Query(description="Filtrar por año lectivo")] = None,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin/DepartmentAdmin"),
    ] = None,
) -> AcademicPeriodListResponse:
    target_institution_id = await _resolve_institution_id(db, auth, current_user, institution_id)
    query = (
        select(AcademicPeriod)
        .join(AcademicYear, AcademicPeriod.academic_year_id == AcademicYear.id)
        .where(AcademicYear.institution_id == target_institution_id)
    )
    if year_id:
        query = query.where(AcademicPeriod.academic_year_id == year_id)
    query = query.order_by(AcademicPeriod.period_number.asc())
    periods = list((await db.execute(query)).scalars().all())
    return AcademicPeriodListResponse(
        items=[AcademicPeriodResponse.model_validate(p) for p in periods],
        total=len(periods),
    )


@periods_router.post(
    "",
    response_model=AcademicPeriodResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear período académico directo",
    description="Registra un nuevo período de evaluación indicando el año escolar.",
    dependencies=[Depends(require_permission("academic_periods", "create"))],
)
async def create_academic_period_direct(
    payload: AcademicPeriodDirectCreateRequest,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    client_ip: ClientIpDep,
    year_id: Annotated[uuid.UUID | None, Query(description="Año escolar")] = None,
    institution_id: Annotated[
        uuid.UUID | None,
        Query(description="Override for SuperAdmin/DepartmentAdmin"),
    ] = None,
) -> AcademicPeriodResponse:
    target_year_id = payload.academic_year_id or year_id
    if not target_year_id:
        from app.core.exceptions import AcademicDomainError
        raise AcademicDomainError("Debe especificar el año lectivo (year_id) para el período.")
    target_institution_id = await _resolve_institution_id(db, auth, current_user, institution_id)
    correlation_id = correlation_id_ctx.get()
    service = AcademicYearService(session=db)
    period = await service.create_academic_period(
        year_id=target_year_id,
        institution_id=target_institution_id,
        period_number=payload.period_number,
        name=payload.name,
        weight_percentage=payload.weight_percentage,
        start_date=payload.start_date,
        end_date=payload.end_date,
        actor_id=current_user.id,
        actor_ip=client_ip,
        correlation_id=correlation_id,
    )
    await db.commit()
    await db.refresh(period)
    return AcademicPeriodResponse.model_validate(period)


