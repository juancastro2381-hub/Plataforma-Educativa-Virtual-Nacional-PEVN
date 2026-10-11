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


# ===========================================================================
# Phase NTA-05: Territorial Control Center Data Contracts
# ===========================================================================

class Tier1CatalogMetrics(BaseModel):
    """Tier 1: Canonical National MEN Catalog Metrics."""

    model_config = ConfigDict(from_attributes=True)

    total_departments: int = Field(..., description="Cantidad de departamentos en catálogo DIVIPOLA")
    total_municipalities: int = Field(..., description="Cantidad de municipios en catálogo DIVIPOLA")
    total_establishments: int = Field(..., description="Establecimientos oficiales canónicos en catálogo")
    total_campuses: int = Field(..., description="Sedes educativas oficiales en catálogo")
    official_sector_count: int = Field(..., description="Instituciones oficiales (públicas)")
    non_official_sector_count: int = Field(..., description="Instituciones privadas")
    urban_zone_count: int = Field(..., description="Establecimientos en zona urbana")
    rural_zone_count: int = Field(..., description="Establecimientos en zona rural")


class Tier2PipelineMetrics(BaseModel):
    """Tier 2: NTA-04 Onboarding Pipeline Metrics."""

    model_config = ConfigDict(from_attributes=True)

    total_requests: int = Field(..., description="Total de radicados en el flujo NTA-04")
    submitted: int = Field(..., description="Solicitudes radicadas pendientes de revisión")
    under_review: int = Field(..., description="Solicitudes en revisión técnica")
    approved: int = Field(..., description="Solicitudes aprobadas pendientes de aprovisionar")
    provisioned: int = Field(..., description="Solicitudes aprovisionadas exitosamente")
    rejected: int = Field(..., description="Solicitudes rechazadas")
    cancelled: int = Field(..., description="Solicitudes canceladas")


class Tier3TenancyMetrics(BaseModel):
    """Tier 3: PEVN SaaS Operational Tenancy Metrics."""

    model_config = ConfigDict(from_attributes=True)

    total_institutions: int = Field(..., description="Total de tenants registrados en PEVN")
    active_institutions: int = Field(..., description="Tenants activos operacionalmente")
    inactive_institutions: int = Field(..., description="Tenants inactivos o suspendidos")
    catalog_linked_institutions: int = Field(..., description="Tenants reales enlazados al catálogo MEN")
    synthetic_fixture_institutions: int = Field(..., description="Tenants sintéticos de prueba/regresión con catalog_institution_id = NULL")
    provisioned_campuses: int = Field(..., description="Total de sedes aprovisionadas en PEVN")
    active_operational_campuses: int = Field(..., description="Sedes aprovisionadas activas")
    total_users: int = Field(..., description="Total de usuarios operacionales")
    active_students: int = Field(..., description="Estudiantes con matrícula activa")
    active_teachers: int = Field(..., description="Docentes vinculados a instituciones")


class Tier4GovernanceMetrics(BaseModel):
    """Tier 4: Territorial SED Governance Metrics."""

    model_config = ConfigDict(from_attributes=True)

    total_departments: int = Field(..., description="Jurisdicciones departamentales")
    department_admin_users_count: int = Field(..., description="Usuarios distintos con asignación activa de rol DEPARTMENT_ADMIN")
    covered_departments: int = Field(..., description="Departamentos con al menos una asignación activa de Administrador Departamental")
    vacant_departments: int = Field(..., description="Departamentos sin ninguna asignación activa de Administrador Departamental")
    pending_invitations: int = Field(..., description="Invitaciones de Dept Admin en curso")
    coverage_percentage: float = Field(..., description="Porcentaje de cobertura de gobernanza SED sobre departamentos")


class DepartmentMatrixRow(BaseModel):
    """Item representing a single department within the national matrix."""

    model_config = ConfigDict(from_attributes=True)

    department_id: uuid.UUID = Field(..., description="Identificador único del departamento")
    department_code: str = Field(..., description="Código DANE de 2 dígitos")
    department_name: str = Field(..., description="Nombre del departamento")
    governance_status: str = Field(..., description="Estado de gobernanza: COVERED, INVITED, VACANT")
    admin_name: str | None = Field(None, description="Nombre del Administrador Departamental")
    admin_email: str | None = Field(None, description="Email del Administrador Departamental")
    total_establishments: int = Field(..., description="Establecimientos oficiales en el catálogo")
    total_campuses: int = Field(..., description="Sedes oficiales en el catálogo")
    pipeline_in_progress: int = Field(..., description="Solicitudes en trámite (SUBMITTED + UNDER_REVIEW + APPROVED)")
    active_institutions: int = Field(..., description="Tenants activos en PEVN")
    inactive_institutions: int = Field(..., description="Tenants inactivos en PEVN")
    provisioning_rate_percent: float = Field(..., description="Tasa porcentual de aprovisionamiento frente al catálogo")


class TerritorialControlCenterResponse(BaseModel):
    """Consolidated 4-Tier Territorial Control Center Response."""

    model_config = ConfigDict(from_attributes=True)

    scope_level: str = Field(..., description="Nivel de alcance aplicado (NATIONAL o DEPARTMENT)")
    jurisdiction_name: str = Field(..., description="Nombre de la jurisdicción consultada")
    tier1_catalog: Tier1CatalogMetrics = Field(..., description="Métricas de catálogo oficial (Tier 1)")
    tier2_pipeline: Tier2PipelineMetrics = Field(..., description="Métricas de pipeline NTA-04 (Tier 2)")
    tier3_tenancy: Tier3TenancyMetrics = Field(..., description="Métricas de tenancy PEVN (Tier 3)")
    tier4_governance: Tier4GovernanceMetrics = Field(..., description="Métricas de gobernanza SED (Tier 4)")
    department_matrix: list[DepartmentMatrixRow] = Field(..., description="Matriz territorial departamental")
    computed_at: datetime = Field(..., description="Estampa de tiempo UTC del cálculo")


class DepartmentMunicipalityRow(BaseModel):
    """Municipality detail within a specific department inspection drawer."""

    model_config = ConfigDict(from_attributes=True)

    municipality_id: uuid.UUID = Field(..., description="Identificador único del municipio")
    municipality_code: str = Field(..., description="Código DANE de 5 dígitos")
    municipality_name: str = Field(..., description="Nombre del municipio")
    total_establishments: int = Field(0, description="Establecimientos en catálogo")
    total_campuses: int = Field(0, description="Sedes en catálogo")
    active_institutions: int = Field(0, description="Tenants activos en PEVN")
    inactive_institutions: int = Field(0, description="Tenants inactivos en PEVN")
    pipeline_in_progress: int = Field(0, description="Solicitudes en trámite")


class DepartmentDetailControlCenterResponse(BaseModel):
    """Exhaustive department detail response for drawer/modal inspection."""

    model_config = ConfigDict(from_attributes=True)

    department_id: uuid.UUID = Field(..., description="Identificador del departamento")
    department_code: str = Field(..., description="Código DANE de 2 dígitos")
    department_name: str = Field(..., description="Nombre del departamento")
    governance_status: str = Field(..., description="Estado de gobernanza")
    admin_name: str | None = Field(None, description="Nombre del Administrador Departamental")
    admin_email: str | None = Field(None, description="Email del Administrador Departamental")
    total_municipalities: int = Field(0, description="Cantidad de municipios")
    total_establishments: int = Field(0, description="Establecimientos en catálogo")
    total_campuses: int = Field(0, description="Sedes en catálogo")
    active_institutions: int = Field(0, description="Tenants activos en PEVN")
    inactive_institutions: int = Field(0, description="Tenants inactivos en PEVN")
    pipeline_in_progress: int = Field(0, description="Solicitudes en trámite")
    municipalities: list[DepartmentMunicipalityRow] = Field(default_factory=list, description="Desglose por municipio")
    computed_at: datetime = Field(..., description="Estampa de tiempo UTC del cálculo")

