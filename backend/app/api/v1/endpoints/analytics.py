"""
PEVN Backend — Territorial Analytics API Endpoints

Provides RESTful endpoints for national, departmental, municipal, and institutional
KPIs and educational territorial metrics, strictly protected by RBAC permissions
and OrganizationalScope constraints.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import AuthContextDep, SessionDep, require_permission
from app.schemas.analytics import (
    DepartmentAnalyticsResponse,
    InstitutionalKPIResponse,
    MunicipalityAnalyticsResponse,
    TerritorialSummaryResponse,
)
from app.services.territorial_analytics_service import TerritorialAnalyticsService

router = APIRouter(prefix="/analytics", tags=["Territorial Analytics"])


@router.get(
    "/territorial/summary",
    response_model=TerritorialSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener resumen consolidado de indicadores territoriales",
    description=(
        "Devuelve indicadores y métricas territoriales agregadas (departamentos, "
        "municipios, instituciones públicas/privadas, sedes, aprovisionamiento) "
        "acotadas estrictamente por el alcance organizacional del usuario."
    ),
)
async def get_territorial_summary(
    auth: Annotated[
        AuthContextDep, Depends(require_permission("institutions", "read"))
    ],
    db: SessionDep,
) -> TerritorialSummaryResponse:
    service = TerritorialAnalyticsService(session=db)
    return await service.get_national_summary(scope=auth.scope)


@router.get(
    "/territorial/departments",
    response_model=DepartmentAnalyticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener desglose analítico por departamento",
    description=(
        "Devuelve la distribución de instituciones, sedes y aprovisionamiento "
        "a nivel departamental. Requiere alcance nacional o departamental."
    ),
)
async def get_department_distribution(
    auth: Annotated[
        AuthContextDep, Depends(require_permission("institutions", "read"))
    ],
    db: SessionDep,
) -> DepartmentAnalyticsResponse:
    service = TerritorialAnalyticsService(session=db)
    return await service.get_department_distribution(scope=auth.scope)


@router.get(
    "/territorial/municipalities",
    response_model=MunicipalityAnalyticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener distribución analítica por municipio",
    description=(
        "Devuelve la distribución municipal dentro de un departamento o a nivel nacional "
        "respetando el alcance territorial del actor."
    ),
)
async def get_municipality_distribution(
    auth: Annotated[
        AuthContextDep, Depends(require_permission("institutions", "read"))
    ],
    db: SessionDep,
    department_code: str | None = Query(
        None,
        description="Código DANE de 2 dígitos del departamento a filtrar",
    ),
) -> MunicipalityAnalyticsResponse:
    service = TerritorialAnalyticsService(session=db)
    return await service.get_municipality_distribution(
        scope=auth.scope, department_code=department_code
    )


@router.get(
    "/territorial/institutions/{institution_id}",
    response_model=InstitutionalKPIResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener indicadores clave (KPIs) de una institución específica",
    description=(
        "Devuelve el conteo de sedes, grupos, estudiantes, docentes y matrículas activas "
        "para una institución autorizada."
    ),
)
async def get_institutional_kpis(
    institution_id: uuid.UUID,
    auth: Annotated[
        AuthContextDep, Depends(require_permission("institutions", "read"))
    ],
    db: SessionDep,
) -> InstitutionalKPIResponse:
    service = TerritorialAnalyticsService(session=db)
    return await service.get_institutional_kpis(
        scope=auth.scope, institution_id=institution_id
    )
