"""
PEVN Backend — Technical Operations & Platform Observability Endpoints

REST Controller exclusively reserved for SUPER_ADMIN (Level 100).
Provides platform health, security audit monitoring, technical support ticket
management, and audited tenant diagnostic inspection.
"""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthContextDep
from app.core.security.interfaces import AuthorizationContext
from app.db.session import get_async_session
from app.schemas.technical_incident import (
    TechnicalIncidentCreateRequest,
    TechnicalIncidentListResponse,
    TechnicalIncidentResponse,
    TechnicalIncidentUpdateRequest,
)
from app.services.system_operations_service import system_operations_service

router = APIRouter(
    prefix="/system/operations",
    tags=["Platform Operations (Level 100)"],
)


async def require_superadmin_operator(auth: AuthContextDep) -> AuthorizationContext:
    """
    Enforce that the authenticated actor is strictly SUPER_ADMIN (Level 100).
    Rejects NATIONAL_ADMIN (Level 90), Department Admin, Rector, etc. with HTTP 403.
    Rejects unauthenticated or locked accounts with HTTP 401.
    """
    if not auth.user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión no autenticada.",
        )

    # Check for superadmin role equivalence
    is_superadmin = any(
        str(getattr(r, "value", r)).lower() in ("superadmin", "super_admin")
        for r in auth.roles
    )

    if not is_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado: este módulo es exclusivo para el Operador Técnico Global (SUPER_ADMIN Nivel 100).",
        )

    return auth


SuperAdminDep = Annotated[AuthorizationContext, Depends(require_superadmin_operator)]


@router.get(
    "/overview",
    summary="Resumen ejecutivo de telemetría y salud de plataforma",
    description="Retorna el estado de conectividad DB, Redis, contadores de incidentes y eventos de seguridad.",
)
async def get_platform_overview_endpoint(
    auth: SuperAdminDep,
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    return await system_operations_service.get_platform_overview(db)


@router.get(
    "/health",
    summary="Sonda exhaustiva de dependencias e infraestructura",
    description="Inspecciona cada subsistema (API, PostgreSQL, Redis, MEN Open Data, Auditoría).",
)
async def get_platform_health_endpoint(
    auth: SuperAdminDep,
) -> dict[str, Any]:
    return await system_operations_service.get_platform_health()


@router.get(
    "/audit-feed",
    summary="Feed de auditoría de seguridad y eventos administrativos",
    description="Consulta registros reales de la tabla audit_logs con filtros de eventos de seguridad.",
)
async def get_audit_feed_endpoint(
    auth: SuperAdminDep,
    db: AsyncSession = Depends(get_async_session),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    only_security: bool = Query(True),
) -> dict[str, Any]:
    return await system_operations_service.get_security_audit_feed(
        session=db,
        limit=limit,
        offset=offset,
        only_security=only_security,
    )


@router.get(
    "/support-cases",
    response_model=TechnicalIncidentListResponse,
    summary="Listar casos de soporte técnico e incidencias de plataforma",
    description="Retorna incidencias técnicas filtradas por estado y severidad con conteos consolidados.",
)
async def list_support_cases_endpoint(
    auth: SuperAdminDep,
    db: AsyncSession = Depends(get_async_session),
    status_filter: str | None = Query(None, alias="status"),
    severity: str | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> TechnicalIncidentListResponse:
    data = await system_operations_service.list_support_cases(
        session=db,
        status=status_filter,
        severity=severity,
        limit=limit,
        offset=offset,
    )
    return TechnicalIncidentListResponse(
        items=[TechnicalIncidentResponse.model_validate(c) for c in data["items"]],
        total=data["total"],
        open_count=data["open_count"],
        critical_count=data["critical_count"],
    )


@router.post(
    "/support-cases",
    response_model=TechnicalIncidentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un nuevo caso o incidente técnico",
    description="Crea un ticket de soporte técnico y emite un registro inmutable en audit_logs.",
)
async def create_support_case_endpoint(
    payload: TechnicalIncidentCreateRequest,
    auth: SuperAdminDep,
    db: AsyncSession = Depends(get_async_session),
) -> TechnicalIncidentResponse:
    incident = await system_operations_service.create_support_case(
        session=db,
        actor_id=uuid.UUID(auth.user_id),
        payload=payload.model_dump(),
    )
    return TechnicalIncidentResponse.model_validate(incident)


@router.patch(
    "/support-cases/{case_id}",
    response_model=TechnicalIncidentResponse,
    summary="Actualizar estado o resolución de una incidencia técnica",
    description="Modifica ciclo de vida, operador asignado o notas de resolución con trazabilidad de auditoría.",
)
async def update_support_case_endpoint(
    case_id: uuid.UUID,
    payload: TechnicalIncidentUpdateRequest,
    auth: SuperAdminDep,
    db: AsyncSession = Depends(get_async_session),
) -> TechnicalIncidentResponse:
    incident = await system_operations_service.update_support_case(
        session=db,
        case_id=case_id,
        actor_id=uuid.UUID(auth.user_id),
        payload=payload.model_dump(exclude_unset=True),
    )
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incidente técnico con ID {case_id} no encontrado.",
        )
    return TechnicalIncidentResponse.model_validate(incident)


@router.get(
    "/tenant-diagnostics/{institution_id}",
    summary="Diagnóstico técnico de inquilino institucional",
    description="Inspecciona configuración, sedes y usuarios de un colegio específico. Registra auditoría técnica obligatoria.",
)
async def get_tenant_diagnostics_endpoint(
    institution_id: uuid.UUID,
    auth: SuperAdminDep,
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    diag = await system_operations_service.get_tenant_diagnostics(
        session=db,
        institution_id=institution_id,
        actor_id=uuid.UUID(auth.user_id),
    )
    if not diag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Institución educativa con ID {institution_id} no encontrada.",
        )
    return diag


@router.get(
    "/integrations",
    summary="Catálogo de integraciones y servicios configurados",
    description="Describe el estado de adaptadores y conexiones externas sin exponer contraseñas ni secretos.",
)
async def get_platform_integrations_endpoint(
    auth: SuperAdminDep,
) -> dict[str, Any]:
    return await system_operations_service.get_platform_integrations()
