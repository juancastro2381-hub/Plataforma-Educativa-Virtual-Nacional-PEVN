"""
PEVN Backend — Territorial Analytics Data Contracts & Pydantic Schemas

Defines request and response schemas for multi-level territorial KPI aggregations,
departmental breakdowns, municipal distributions, and institutional metrics.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class TerritorialSectorBreakdown(BaseModel):
    """Distribution by educational sector."""

    model_config = ConfigDict(from_attributes=True)

    official: int = Field(0, description="Total de instituciones oficiales (públicas)")
    non_official: int = Field(0, description="Total de instituciones no oficiales (privadas)")


class TerritorialZoneBreakdown(BaseModel):
    """Distribution by territorial zone."""

    model_config = ConfigDict(from_attributes=True)

    urban: int = Field(0, description="Total de sedes / instituciones en zona urbana")
    rural: int = Field(0, description="Total de sedes / instituciones en zona rural")


class TerritorialSummaryResponse(BaseModel):
    """
    High-level territorial KPIs aggregated according to the caller's authorized scope.
    """

    model_config = ConfigDict(from_attributes=True)

    scope_level: str = Field(..., description="Nivel de alcance aplicado (NATIONAL, DEPARTMENT, MUNICIPALITY, INSTITUTION)")
    jurisdiction_name: str = Field(..., description="Nombre de la jurisdicción consultada (e.g. 'República de Colombia', 'Antioquia')")
    total_departments: int = Field(0, description="Total de departamentos bajo la jurisdicción")
    total_municipalities: int = Field(0, description="Total de municipios bajo la jurisdicción")
    total_institutions: int = Field(0, description="Total de instituciones en el catálogo oficial")
    provisioned_institutions: int = Field(0, description="Total de instituciones aprovisionadas en la plataforma")
    provisioning_rate_percent: float = Field(0.0, description="Porcentaje de instituciones aprovisionadas")
    total_campuses: int = Field(0, description="Total de sedes educativas")
    active_students: int = Field(0, description="Total de estudiantes matriculados en la plataforma")
    active_teachers: int = Field(0, description="Total de docentes activos vinculados")
    active_groups: int = Field(0, description="Total de grupos / salones de clase activos")
    sector_breakdown: TerritorialSectorBreakdown = Field(
        default_factory=TerritorialSectorBreakdown,
        description="Distribución por sector oficial vs no oficial",
    )
    zone_breakdown: TerritorialZoneBreakdown = Field(
        default_factory=TerritorialZoneBreakdown,
        description="Distribución por zona urbana vs rural",
    )
    computed_at: datetime = Field(..., description="Estampa de tiempo UTC del cálculo de métricas")


class DepartmentAnalyticsItem(BaseModel):
    """Department-level aggregation item."""

    model_config = ConfigDict(from_attributes=True)

    department_code: str = Field(..., description="Código DANE de 2 dígitos")
    department_name: str = Field(..., description="Nombre del departamento")
    total_municipalities: int = Field(0, description="Cantidad de municipios")
    total_institutions: int = Field(0, description="Instituciones oficiales en el catálogo")
    official_institutions: int = Field(0, description="Instituciones públicas")
    non_official_institutions: int = Field(0, description="Instituciones privadas")
    total_campuses: int = Field(0, description="Total de sedes educativas")
    provisioned_institutions: int = Field(0, description="Instituciones activas en PEvN")


class DepartmentAnalyticsResponse(BaseModel):
    """Response containing departmental distribution list."""

    model_config = ConfigDict(from_attributes=True)

    items: list[DepartmentAnalyticsItem] = Field(default_factory=list)
    total_count: int = Field(0, description="Cantidad de departamentos listados")
    computed_at: datetime = Field(..., description="Estampa de tiempo UTC")


class MunicipalityAnalyticsItem(BaseModel):
    """Municipality-level aggregation item."""

    model_config = ConfigDict(from_attributes=True)

    municipality_code: str = Field(..., description="Código DANE de 5 dígitos")
    municipality_name: str = Field(..., description="Nombre del municipio")
    department_code: str = Field(..., description="Código DANE de departamento")
    department_name: str = Field(..., description="Nombre del departamento")
    total_institutions: int = Field(0, description="Instituciones en catálogo")
    official_institutions: int = Field(0, description="Instituciones públicas")
    non_official_institutions: int = Field(0, description="Instituciones privadas")
    total_campuses: int = Field(0, description="Total de sedes")
    provisioned_institutions: int = Field(0, description="Instituciones aprovisionadas")


class MunicipalityAnalyticsResponse(BaseModel):
    """Response containing municipal distribution list."""

    model_config = ConfigDict(from_attributes=True)

    department_code: str | None = Field(None, description="Código de departamento filtrado, si aplica")
    items: list[MunicipalityAnalyticsItem] = Field(default_factory=list)
    total_count: int = Field(0, description="Cantidad de municipios listados")
    computed_at: datetime = Field(..., description="Estampa de tiempo UTC")


class InstitutionalKPIResponse(BaseModel):
    """Institutional-level KPIs."""

    model_config = ConfigDict(from_attributes=True)

    institution_id: uuid.UUID = Field(..., description="Identificador único de la institución")
    dane_code: str = Field(..., description="Código DANE institucional de 12 dígitos")
    name: str = Field(..., description="Nombre de la institución educativa")
    department_name: str = Field(..., description="Departamento")
    municipality_name: str = Field(..., description="Municipio")
    total_campuses: int = Field(0, description="Sedes adscritas registradas")
    total_groups: int = Field(0, description="Grupos académicos activos")
    total_students: int = Field(0, description="Estudiantes activos")
    total_teachers: int = Field(0, description="Docentes activos")
    total_enrollments: int = Field(0, description="Matrículas activas en el año lectivo")
    computed_at: datetime = Field(..., description="Estampa de tiempo UTC")
