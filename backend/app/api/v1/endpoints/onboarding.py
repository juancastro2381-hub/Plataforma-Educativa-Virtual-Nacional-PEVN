"""
PEVN Backend — Institution Onboarding API Controller

REST Controller for the NTA-04 National Provisioning Workflow:
  - Explore official catalog enriched with PEVN onboarding/operational state
  - File/submit institution onboarding requests
  - List and search onboarding requests with territorial scoping
  - Technical review lifecycle (start-review, approve, reject, cancel)
  - Atomic four-tier transactional tenant provisioning
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status

from app.api.deps import (
    AuthContextDep,
    ClientIpDep,
    CurrentUserDep,
    SessionDep,
)
from app.core.security.interfaces import SystemRole
from app.exceptions.errors import AuthorizationError
from app.schemas.onboarding import (
    CatalogExplorerListResponse,
    OnboardingApprovalPayload,
    OnboardingCancellationPayload,
    OnboardingProvisionResultResponse,
    OnboardingRejectionPayload,
    OnboardingRequestCreatePayload,
    OnboardingRequestDetailResponse,
    OnboardingRequestListResponse,
)
from app.services.onboarding_service import OnboardingService

router = APIRouter()


def _require_onboarding_access(auth: AuthContextDep) -> None:
    """Validate that actor belongs to an authorized administrative role."""
    allowed = {
        SystemRole.SUPERADMIN,
        SystemRole.NATIONAL_ADMIN,
        SystemRole.DEPARTMENT_ADMIN,
    }
    if not any(role in allowed for role in auth.roles):
        raise AuthorizationError(
            "Acceso denegado: El flujo de incorporación y aprovisionamiento está reservado a las autoridades administrativas.",
            code="PERMISSION_DENIED",
        )


# ==============================================================================
# 1. Catalog Explorer (onboarding:discover)
# ==============================================================================
@router.get(
    "/catalog",
    response_model=CatalogExplorerListResponse,
    status_code=status.HTTP_200_OK,
    summary="Explorar catálogo oficial para incorporación a PEVN",
    description=(
        "Consulta el universo oficial de establecimientos educativos enriquecido "
        "con el estado de incorporación en PEVN (AVAILABLE, EN_TRAMITE, PROVISIONED). "
        "Aplica aislamiento territorial estricto para Administradores Departamentales."
    ),
)
async def explore_catalog_endpoint(
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    dane_code: Annotated[str | None, Query(description="Filtrar por código DANE")] = None,
    name: Annotated[str | None, Query(description="Búsqueda por nombre")] = None,
    department_id: Annotated[uuid.UUID | None, Query(description="Filtrar por departamento")] = None,
    municipality_id: Annotated[uuid.UUID | None, Query(description="Filtrar por municipio")] = None,
    onboarding_status: Annotated[
        str | None,
        Query(description="Estado de incorporación (AVAILABLE, EN_TRAMITE, PROVISIONED)"),
    ] = None,
    page: Annotated[int, Query(ge=1, description="Número de página")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Registros por página")] = 20,
) -> CatalogExplorerListResponse:
    _require_onboarding_access(auth)
    service = OnboardingService(session=db)
    return await service.explore_catalog(
        actor=current_user,
        dane_code=dane_code,
        name=name,
        department_id=department_id,
        municipality_id=municipality_id,
        onboarding_status=onboarding_status,
        page=page,
        page_size=page_size,
    )


# ==============================================================================
# 2. Onboarding Requests Management (onboarding:create, onboarding:read)
# ==============================================================================
@router.post(
    "/requests",
    response_model=OnboardingRequestDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Radicar solicitud de incorporación institucional",
    description=(
        "Crea una solicitud de incorporación a partir de un establecimiento del catálogo oficial. "
        "Verifica unicidad, vigencia oficial y jurisdicción territorial Anti-IDOR."
    ),
)
async def create_onboarding_request_endpoint(
    payload: OnboardingRequestCreatePayload,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    client_ip: ClientIpDep,
    request: Request,
) -> OnboardingRequestDetailResponse:
    _require_onboarding_access(auth)
    correlation_id = getattr(request.state, "correlation_id", None)
    service = OnboardingService(session=db)
    res = await service.create_request(
        payload=payload,
        actor=current_user,
        actor_ip=client_ip,
        correlation_id=correlation_id,
    )
    await db.commit()
    return res


@router.get(
    "/requests",
    response_model=OnboardingRequestListResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar solicitudes de incorporación institucional",
    description="Lista y filtra las solicitudes de incorporación con gobernanza y alcance territorial.",
)
async def list_onboarding_requests_endpoint(
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    status_filter: Annotated[str | None, Query(alias="status", description="Filtrar por estado")] = None,
    department_id: Annotated[uuid.UUID | None, Query(description="Filtrar por departamento")] = None,
    municipality_id: Annotated[uuid.UUID | None, Query(description="Filtrar por municipio")] = None,
    search: Annotated[str | None, Query(description="Buscar por radicado, DANE o correo")] = None,
    page: Annotated[int, Query(ge=1, description="Número de página")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Registros por página")] = 20,
) -> OnboardingRequestListResponse:
    _require_onboarding_access(auth)
    service = OnboardingService(session=db)
    return await service.list_requests(
        actor=current_user,
        status=status_filter,
        department_id=department_id,
        municipality_id=municipality_id,
        search=search,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/requests/{id}",
    response_model=OnboardingRequestDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar detalle de solicitud de incorporación",
    description="Devuelve el detalle integral de una solicitud de incorporación validando aislamiento Anti-IDOR.",
)
async def get_onboarding_request_endpoint(
    id: uuid.UUID,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
) -> OnboardingRequestDetailResponse:
    _require_onboarding_access(auth)
    service = OnboardingService(session=db)
    return await service.get_request_by_id(
        request_id=id,
        actor=current_user,
    )


# ==============================================================================
# 3. Lifecycle State Machine Transitions
# ==============================================================================
@router.post(
    "/requests/{id}/start-review",
    response_model=OnboardingRequestDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Iniciar revisión técnica de la solicitud",
    description="Asigna la solicitud al revisor y transiciona de SUBMITTED a UNDER_REVIEW.",
)
async def start_review_endpoint(
    id: uuid.UUID,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    client_ip: ClientIpDep,
    request: Request,
    notes: Annotated[str | None, Query(description="Notas iniciales de revisión")] = None,
) -> OnboardingRequestDetailResponse:
    _require_onboarding_access(auth)
    correlation_id = getattr(request.state, "correlation_id", None)
    service = OnboardingService(session=db)
    res = await service.start_review(
        request_id=id,
        actor=current_user,
        notes=notes,
        actor_ip=client_ip,
        correlation_id=correlation_id,
    )
    await db.commit()
    return res


@router.post(
    "/requests/{id}/approve",
    response_model=OnboardingRequestDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Aprobar formalmente la solicitud de incorporación",
    description="Otorga aprobación formal administrativa (APPROVED) a la solicitud.",
)
async def approve_request_endpoint(
    id: uuid.UUID,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    client_ip: ClientIpDep,
    request: Request,
    payload: OnboardingApprovalPayload | None = None,
) -> OnboardingRequestDetailResponse:
    _require_onboarding_access(auth)
    correlation_id = getattr(request.state, "correlation_id", None)
    service = OnboardingService(session=db)
    res = await service.approve_request(
        request_id=id,
        actor=current_user,
        payload=payload,
        actor_ip=client_ip,
        correlation_id=correlation_id,
    )
    await db.commit()
    return res


@router.post(
    "/requests/{id}/reject",
    response_model=OnboardingRequestDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Rechazar formalmente la solicitud de incorporación",
    description="Rechaza la solicitud (REJECTED) exigiendo motivo formal no menor a 10 caracteres.",
)
async def reject_request_endpoint(
    id: uuid.UUID,
    payload: OnboardingRejectionPayload,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    client_ip: ClientIpDep,
    request: Request,
) -> OnboardingRequestDetailResponse:
    _require_onboarding_access(auth)
    correlation_id = getattr(request.state, "correlation_id", None)
    service = OnboardingService(session=db)
    res = await service.reject_request(
        request_id=id,
        payload=payload,
        actor=current_user,
        actor_ip=client_ip,
        correlation_id=correlation_id,
    )
    await db.commit()
    return res


@router.post(
    "/requests/{id}/cancel",
    response_model=OnboardingRequestDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Desistir / cancelar la solicitud de incorporación",
    description="Permite al solicitante original o al administrador nacional cancelar una solicitud.",
)
async def cancel_request_endpoint(
    id: uuid.UUID,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    client_ip: ClientIpDep,
    request: Request,
    payload: OnboardingCancellationPayload | None = None,
) -> OnboardingRequestDetailResponse:
    _require_onboarding_access(auth)
    correlation_id = getattr(request.state, "correlation_id", None)
    service = OnboardingService(session=db)
    res = await service.cancel_request(
        request_id=id,
        payload=payload,
        actor=current_user,
        actor_ip=client_ip,
        correlation_id=correlation_id,
    )
    await db.commit()
    return res


# ==============================================================================
# 4. Atomic Tenant Provisioning (onboarding:provision)
# ==============================================================================
@router.post(
    "/requests/{id}/provision",
    response_model=OnboardingProvisionResultResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Aprovisionar tenant institucional de manera atómica",
    description=(
        "Ejecuta la materialización del tenant institucional, sedes educativas e "
        "invitación criptográfica del rector bajo una única transacción de base de datos."
    ),
)
async def provision_request_endpoint(
    id: uuid.UUID,
    db: SessionDep,
    auth: AuthContextDep,
    current_user: CurrentUserDep,
    client_ip: ClientIpDep,
    request: Request,
) -> OnboardingProvisionResultResponse:
    _require_onboarding_access(auth)
    correlation_id = getattr(request.state, "correlation_id", None)
    service = OnboardingService(session=db)
    res = await service.provision_request(
        request_id=id,
        actor=current_user,
        actor_ip=client_ip,
        correlation_id=correlation_id,
    )
    await db.commit()
    return res
