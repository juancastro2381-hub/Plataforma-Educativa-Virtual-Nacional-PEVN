"""
PEVN Backend — Institutions API Endpoints

Handles institutional provisioning, tenant queries, operational status transitions,
and rector onboarding invitations for National Administrators.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import (
    AuthContextDep,
    CurrentUserDep,
    SessionDep,
    require_permission,
)
from app.core.config import get_settings
from app.core.security.authorization import authorization_service
from app.core.security.interfaces import (
    OrganizationalScope,
    Permission as SecurityPermission,
    SystemRole,
)
from app.exceptions.errors import AuthorizationError, NotFoundError
from app.models.institution import Institution
from app.models.territory import Department, Municipality
from app.schemas.institution import (
    CoordinatorDelegationSettingResponse,
    CoordinatorDelegationSettingUpdateRequest,
    InstitutionCreate,
    InstitutionListResponse,
    InstitutionResponse,
    InstitutionStatusUpdateRequest,
    OfficialCatalogListResponse,
    ProvisionCatalogInstitutionRequest,
)
from app.schemas.invitation import (
    RectorInvitationCreateRequest,
    RectorInvitationResponse,
    RectorRevocationRequest,
    RectorRevocationResponse,
)
from app.services.email_service import EmailDeliveryStatus
from app.schemas.official_catalog import (
    OfficialCatalogSyncRequest,
    OfficialCatalogSyncResponse,
    OfficialCatalogSyncStatusResponse,
    OfficialInstitutionResolutionResponse,
    PromotionAuthorizationRequest,
    PromotionAuthorizationResponse,
    PromotionDryRunResponse,
    PromotionExecuteRequest,
    PromotionExecuteResponse,
    PromotionPreflightResponse,
    PromotionRollbackRequest,
    PromotionRollbackResponse,
    PromotionStatusGovernanceResponse,
    NationalCatalogFinalCertificationResponse,
)
from app.services.institution_service import InstitutionService
from app.services.national_catalog_controlled_promotion_service import (
    NationalCatalogControlledPromotionService,
)
from app.services.national_catalog_final_certification_service import (
    NationalCatalogFinalCertificationService,
)
from app.services.official_catalog_sync_service import OfficialCatalogSyncService
from app.services.promotion_authorization_service import PromotionAuthorizationService
from app.services.rector_onboarding_service import RectorOnboardingService

router = APIRouter(prefix="/institutions", tags=["Institutions"])


@router.get(
    "/catalog/sync-status",
    response_model=OfficialCatalogSyncStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar estado y métricas de sincronización del catálogo oficial DANE/MEN",
    description="Devuelve métricas reales del catálogo oficial local, conteo de sedes, frescura y advertencias de obsolescencia.",
)
async def get_catalog_sync_status(
    auth: Annotated[
        AuthContextDep, Depends(require_permission("institutions", "read"))
    ],
    db: SessionDep,
    max_freshness_days: int = Query(180, ge=1, le=730, description="Días máximos permitidos antes de advertir obsolescencia"),
) -> OfficialCatalogSyncStatusResponse:
    if not (auth.scope.is_national() or SystemRole.SUPERADMIN in auth.roles or SystemRole.NATIONAL_ADMIN in auth.roles):
        raise AuthorizationError(
            "Se requiere alcance nacional para consultar el estado del catálogo oficial.",
            code="PERMISSION_DENIED",
        )

    # Ensure catalog is seeded/ingested
    inst_service = InstitutionService(session=db)
    await inst_service.seed_official_catalog_if_empty()

    sync_service = OfficialCatalogSyncService(session=db)
    return await sync_service.get_catalog_sync_status(max_freshness_days=max_freshness_days)


@router.post(
    "/catalog/sync",
    response_model=OfficialCatalogSyncResponse,
    status_code=status.HTTP_200_OK,
    summary="Ejecutar sincronización del catálogo nacional oficial MEN/DANE",
    description="Inicia la ingestión y validación del catálogo nacional con staging, quality gates y promoción transaccional.",
)
async def sync_official_catalog(
    payload: OfficialCatalogSyncRequest,
    auth: Annotated[
        AuthContextDep, Depends(require_permission("institutions", "create"))
    ],
    db: SessionDep,
) -> OfficialCatalogSyncResponse:
    if not (auth.scope.is_national() or SystemRole.SUPERADMIN in auth.roles or SystemRole.NATIONAL_ADMIN in auth.roles):
        raise AuthorizationError(
            "Solo administradores nacionales pueden ejecutar la sincronización del catálogo oficial.",
            code="PERMISSION_DENIED",
        )

    sync_service = OfficialCatalogSyncService(session=db)
    stats = await sync_service.sync_national_catalog(
        source_system=payload.source_system,
        source_dataset=payload.source_dataset,
        source_version=payload.source_version or "2026-Q1",
        chunk_size=payload.chunk_size,
        max_rejection_percentage=payload.max_rejection_percentage,
        strict_mode=payload.strict_mode,
        force_certified_dataset=payload.force_certified_dataset,
    )
    await db.commit()

    return OfficialCatalogSyncResponse(
        batch_id=str(stats.batch_id),
        status=stats.status,
        quality_gate_status=stats.quality_gate_status,
        total_processed=stats.total_records_processed,
        valid_records=stats.valid_records,
        rejected_records=stats.rejected_records,
        duplicate_records=stats.duplicate_institutions + stats.duplicate_campuses,
        institutions_synced=stats.total_institutions_synced,
        campuses_synced=stats.total_campuses_synced,
        departments_covered=stats.departments_count,
        municipalities_covered=stats.municipalities_count,
        total_chunks=stats.total_chunks,
        processed_chunks=stats.processed_chunks,
        failed_chunks=stats.failed_chunks,
        ingestion_progress=stats.ingestion_progress,
        audit_status=stats.audit_status,
        dataset_checksum=stats.dataset_checksum,
        accounting_reconciled=stats.accounting_reconciled,
        validation_errors=stats.validation_errors[:20],
        completed_at=stats.completed_at or stats.started_at,
    )


# --------------------------------------------------------------------------
# Promotion Governance Endpoints
# --------------------------------------------------------------------------

@router.get(
    "/catalog/promotion/status",
    response_model=PromotionStatusGovernanceResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar estado de gobernanza de promoción del catálogo nacional",
    description="Devuelve el estado de la máquina de estados de promoción, estado de autorización, snapshots y bloqueos.",
)
async def get_promotion_governance_status(
    auth: Annotated[
        AuthContextDep, Depends(require_permission("institutions", "read"))
    ],
    db: SessionDep,
) -> PromotionStatusGovernanceResponse:
    if not (auth.scope.is_national() or SystemRole.SUPERADMIN in auth.roles or SystemRole.NATIONAL_ADMIN in auth.roles):
        raise AuthorizationError(
            "Se requiere alcance nacional para consultar la gobernanza de promoción.",
            code="PERMISSION_DENIED",
        )
    service = PromotionAuthorizationService(session=db)
    res = await service.get_governance_status()
    return PromotionStatusGovernanceResponse(**res)


@router.post(
    "/catalog/promotion/preflight",
    response_model=PromotionPreflightResponse,
    status_code=status.HTTP_200_OK,
    summary="Ejecutar auditoría preflight de compuertas de promoción (Gates A-T)",
    description="Evalúa determinísticamente las 20 compuertas de calidad en modo de solo lectura y emite el certificado SHA-256.",
)
async def evaluate_promotion_preflight(
    auth: Annotated[
        AuthContextDep, Depends(require_permission("institutions", "create"))
    ],
    db: SessionDep,
) -> PromotionPreflightResponse:
    if not (auth.scope.is_national() or SystemRole.SUPERADMIN in auth.roles or SystemRole.NATIONAL_ADMIN in auth.roles):
        raise AuthorizationError(
            "Solo administradores nacionales pueden ejecutar la auditoría preflight de promoción.",
            code="PERMISSION_DENIED",
        )
    service = PromotionAuthorizationService(session=db)
    cert = await service.evaluate_preflight(actor_id=str(auth.user_id) if auth.user_id else "SUPERADMIN")
    await db.commit()
    return PromotionPreflightResponse(
        execution_id=cert["execution_id"],
        timestamp=cert["timestamp"],
        certificate_hash=cert["certificate_hash"],
        promotion_preflight_status=cert["promotion_preflight_status"],
        technical_gates_passed=cert["technical_gates_passed"],
        total_institutions=cert["total_institutions"],
        total_campuses=cert["total_campuses"],
        principal_campuses=cert["principal_campuses"],
        annex_campuses=cert["annex_campuses"],
        departments_covered=cert["departments_covered"],
        municipalities_covered=cert["municipalities_covered"],
        governance_status=cert["governance_status"],
        gates=cert["gates"],
    )


@router.post(
    "/catalog/promotion/authorize",
    response_model=PromotionAuthorizationResponse,
    status_code=status.HTTP_200_OK,
    summary="Otorgar autorización explícita para la promoción del catálogo nacional",
    description="Registra la autorización formal con firma criptográfica, justificación administrativa y fecha de expiración.",
)
async def authorize_promotion(
    payload: PromotionAuthorizationRequest,
    current_user: CurrentUserDep,
    auth: Annotated[
        AuthContextDep, Depends(require_permission("institutions", "create"))
    ],
    db: SessionDep,
) -> PromotionAuthorizationResponse:
    if not (auth.scope.is_national() and (SystemRole.SUPERADMIN in auth.roles or SystemRole.NATIONAL_ADMIN in auth.roles)):
        raise AuthorizationError(
            "Solo administradores nacionales pueden autorizar la promoción del catálogo oficial.",
            code="PERMISSION_DENIED",
        )
    service = PromotionAuthorizationService(session=db)
    actor_role_str = (
        auth.roles[0].value
        if auth.roles and hasattr(auth.roles[0], "value")
        else (str(auth.roles[0]) if auth.roles else "NATIONAL_ADMIN")
    )
    auth_rec = await service.authorize_promotion(
        actor_id=str(current_user.id),
        actor_email=current_user.email,
        actor_role=actor_role_str,
        preflight_certificate_hash=payload.preflight_certificate_hash,
        catalog_hash=payload.catalog_hash,
        reason=payload.reason,
        confirm_governance=payload.confirm_governance,
        plan_hash=payload.plan_hash,
        snapshot_id=uuid.UUID(payload.snapshot_id) if payload.snapshot_id else None,
    )
    await db.commit()
    return PromotionAuthorizationResponse(
        authorization_id=str(auth_rec.id),
        actor_id=auth_rec.actor_id,
        actor_email=auth_rec.actor_email,
        actor_role=auth_rec.actor_role,
        decision=auth_rec.decision,
        status=auth_rec.status,
        catalog_hash=auth_rec.catalog_hash,
        preflight_certificate_hash=auth_rec.preflight_certification_hash,
        plan_hash=auth_rec.plan_hash,
        snapshot_id=str(auth_rec.snapshot_id) if auth_rec.snapshot_id else None,
        reason=auth_rec.reason,
        consumed_at=auth_rec.consumed_at,
        created_at=auth_rec.created_at,
        expires_at=auth_rec.expires_at,
    )


@router.post(
    "/catalog/promotion/dry-run",
    response_model=PromotionDryRunResponse,
    status_code=status.HTTP_200_OK,
    summary="Ejecutar simulación dry-run de promoción sin mutar datos de producción",
    description="Simula la promoción, calcula cambios planeados y genera un hash determinístico de plan.",
)
async def execute_promotion_dry_run(
    auth: Annotated[
        AuthContextDep, Depends(require_permission("institutions", "create"))
    ],
    db: SessionDep,
) -> PromotionDryRunResponse:
    if not (auth.scope.is_national() and (SystemRole.SUPERADMIN in auth.roles or SystemRole.NATIONAL_ADMIN in auth.roles)):
        raise AuthorizationError(
            "Solo administradores nacionales pueden ejecutar la simulación dry-run de promoción.",
            code="PERMISSION_DENIED",
        )
    service = PromotionAuthorizationService(session=db)
    res = await service.execute_dry_run(actor_id=str(auth.user_id) if auth.user_id else None)
    await db.commit()
    return PromotionDryRunResponse(**res)


@router.post(
    "/catalog/promotion/execute",
    response_model=PromotionExecuteResponse,
    status_code=status.HTTP_200_OK,
    summary="Ejecutar promoción controlada del catálogo nacional a NATIONAL_CATALOG_SYNCED",
    description="Aplica la transición transaccional con snapshot previo, bloqueo de concurrencia y validación post-promoción.",
)
async def execute_controlled_promotion(
    payload: PromotionExecuteRequest,
    current_user: CurrentUserDep,
    auth: Annotated[
        AuthContextDep, Depends(require_permission("institutions", "create"))
    ],
    db: SessionDep,
) -> PromotionExecuteResponse:
    if not (auth.scope.is_national() and (SystemRole.SUPERADMIN in auth.roles or SystemRole.NATIONAL_ADMIN in auth.roles)):
        raise AuthorizationError(
            "Solo administradores nacionales pueden ejecutar la promoción del catálogo nacional.",
            code="PERMISSION_DENIED",
        )
    service = PromotionAuthorizationService(session=db)
    actor_role_str = (
        auth.roles[0].value
        if auth.roles and hasattr(auth.roles[0], "value")
        else (str(auth.roles[0]) if auth.roles else "NATIONAL_ADMIN")
    )
    res = await service.execute_promotion(
        authorization_id=uuid.UUID(payload.authorization_id),
        actor_id=str(current_user.id),
        actor_email=current_user.email,
        actor_role=actor_role_str,
        preflight_certificate_hash=payload.preflight_certificate_hash,
        plan_hash=payload.plan_hash,
        confirm_irreversible_step=payload.confirm_irreversible_step,
    )
    await db.commit()
    return PromotionExecuteResponse(**res)


@router.post(
    "/catalog/promotion/finalize",
    response_model=PromotionExecuteResponse,
    status_code=status.HTTP_200_OK,
    summary="Ceremonia de promoción final controlada del catálogo nacional a producción",
    description="Orquesta la verificación de compuertas, deriva de catálogo, bloqueo distribuido, consumo único de autorización y verificación post-promoción.",
)
async def finalize_controlled_promotion(
    payload: PromotionExecuteRequest,
    current_user: CurrentUserDep,
    auth: Annotated[
        AuthContextDep, Depends(require_permission("institutions", "create"))
    ],
    db: SessionDep,
) -> PromotionExecuteResponse:
    if not (auth.scope.is_national() and (SystemRole.SUPERADMIN in auth.roles or SystemRole.NATIONAL_ADMIN in auth.roles)):
        raise AuthorizationError(
            "Solo administradores nacionales pueden ejecutar la ceremonia final de promoción del catálogo nacional.",
            code="PERMISSION_DENIED",
        )
    service = NationalCatalogControlledPromotionService(session=db)
    actor_role_str = (
        auth.roles[0].value
        if auth.roles and hasattr(auth.roles[0], "value")
        else (str(auth.roles[0]) if auth.roles else "NATIONAL_ADMIN")
    )
    res = await service.execute_promotion_ceremony(
        authorization_id=uuid.UUID(payload.authorization_id),
        actor_id=str(current_user.id),
        actor_email=current_user.email,
        actor_role=actor_role_str,
        preflight_certificate_hash=payload.preflight_certificate_hash,
        plan_hash=payload.plan_hash,
        confirm_irreversible_step=payload.confirm_irreversible_step,
    )
    await db.commit()
    return PromotionExecuteResponse(**res)


@router.post(
    "/catalog/promotion/rollback",
    response_model=PromotionRollbackResponse,
    status_code=status.HTTP_200_OK,
    summary="Revertir el estado de promoción del catálogo nacional a un snapshot previo",
    description="Restaura de forma segura y auditable el estado del catálogo a NATIONAL_CATALOG_INCOMPLETE.",
)
async def execute_promotion_rollback(
    payload: PromotionRollbackRequest,
    current_user: CurrentUserDep,
    auth: Annotated[
        AuthContextDep, Depends(require_permission("institutions", "create"))
    ],
    db: SessionDep,
) -> PromotionRollbackResponse:
    if not (auth.scope.is_national() and (SystemRole.SUPERADMIN in auth.roles or SystemRole.NATIONAL_ADMIN in auth.roles)):
        raise AuthorizationError(
            "Solo administradores nacionales pueden revertir la promoción del catálogo.",
            code="PERMISSION_DENIED",
        )
    service = PromotionAuthorizationService(session=db)
    res = await service.execute_rollback(
        snapshot_id=uuid.UUID(payload.snapshot_id),
        actor_id=str(current_user.id),
        reason=payload.reason,
        confirm_rollback=payload.confirm_rollback,
    )
    await db.commit()
    return PromotionRollbackResponse(**res)


@router.get(
    "/catalog/promotion/audit",
    response_model=list[dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Consultar registro inmutable de eventos de auditoría de promoción",
    description="Devuelve el historial cronológico de todas las acciones y transiciones de la máquina de estados de promoción.",
)
async def get_promotion_audit_events(
    auth: Annotated[
        AuthContextDep, Depends(require_permission("institutions", "read"))
    ],
    db: SessionDep,
    limit: int = Query(50, ge=1, le=500),
) -> list[dict[str, Any]]:
    if not (auth.scope.is_national() and (SystemRole.SUPERADMIN in auth.roles or SystemRole.NATIONAL_ADMIN in auth.roles)):
        raise AuthorizationError(
            "Se requiere alcance nacional para consultar la auditoría de promoción.",
            code="PERMISSION_DENIED",
        )
    service = PromotionAuthorizationService(session=db)
    return await service.get_audit_events(limit=limit)


@router.get(
    "/catalog/promotion/final-certification",
    response_model=NationalCatalogFinalCertificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Auditoría forense de certificación final pre-autorización (Gates U–AN)",
    description="Ejecuta en modo estrictamente de solo lectura la verificación de las 20 compuertas finales y emite el dictamen forense.",
)
async def get_final_preauthorization_certification(
    auth: Annotated[
        AuthContextDep, Depends(require_permission("institutions", "read"))
    ],
    db: SessionDep,
) -> NationalCatalogFinalCertificationResponse:
    if not (auth.scope.is_national() and (SystemRole.SUPERADMIN in auth.roles or SystemRole.NATIONAL_ADMIN in auth.roles)):
        raise AuthorizationError(
            "Se requiere alcance nacional para consultar la certificación final de promoción.",
            code="PERMISSION_DENIED",
        )
    service = NationalCatalogFinalCertificationService(session=db)
    res = await service.execute_final_certification(
        actor_id=str(auth.user_id) if auth.user_id else "SUPERADMIN"
    )
    return NationalCatalogFinalCertificationResponse(**res)


@router.post(
    "",
    response_model=InstitutionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Aprovisionar nueva institución educativa",
    description="Crea una institución educativa con su código DANE y su sede principal.",
)
async def create_institution(
    payload: InstitutionCreate,
    current_user: CurrentUserDep,
    auth: Annotated[
        AuthContextDep, Depends(require_permission("institutions", "create"))
    ],
    db: SessionDep,
    request: Request,
) -> InstitutionResponse:
    # Security: Restrict to National Scope (NATIONAL_ADMIN or SUPERADMIN)
    if not (auth.scope.is_national() or SystemRole.SUPERADMIN in auth.roles or SystemRole.NATIONAL_ADMIN in auth.roles):
        raise AuthorizationError(
            "Solo administradores nacionales pueden aprovisionar instituciones educativas.",
            code="PERMISSION_DENIED",
        )

    service = InstitutionService(session=db)
    institution = await service.provision_institution(
        dane_code=payload.dane_code,
        name=payload.name,
        email=payload.email,
        municipality_id=payload.municipality_id,
        phone=payload.phone,
        address=payload.address,
        main_campus_name=payload.main_campus_name,
        main_campus_dane=payload.main_campus_dane,
        actor_id=current_user.id,
        actor_ip=request.client.host if request.client else "0.0.0.0",
        correlation_id=request.headers.get("X-Correlation-ID"),
    )
    await db.commit()
    return InstitutionResponse.model_validate(institution)


@router.get(
    "",
    response_model=InstitutionListResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar instituciones educativas (Nivel Nacional)",
    description="Devuelve el catálogo nacional de instituciones paginado y filtrable.",
)
async def list_institutions(
    auth: Annotated[
        AuthContextDep, Depends(require_permission("institutions", "read"))
    ],
    db: SessionDep,
    department_id: uuid.UUID | None = Query(None, description="Filtrar por departamento"),
    municipality_id: uuid.UUID | None = Query(None, description="Filtrar por municipio"),
    is_active: bool | None = Query(None, description="Filtrar por estado activo"),
    search: str | None = Query(None, description="Búsqueda por nombre o código DANE"),
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(20, ge=1, le=100, description="Tamaño de página"),
) -> InstitutionListResponse:
    effective_department_id = department_id
    effective_municipality_id = municipality_id

    # Territorial isolation enforcement
    if auth.scope.is_municipality():
        actor_muni_uuid = uuid.UUID(auth.scope.municipality_id)
        actor_dept_uuid = uuid.UUID(auth.scope.department_id) if auth.scope.department_id else None
        if municipality_id is not None and municipality_id != actor_muni_uuid:
            raise AuthorizationError(
                "No está autorizado para consultar instituciones fuera de su jurisdicción municipal.",
                code="PERMISSION_DENIED",
            )
        if department_id is not None and actor_dept_uuid and department_id != actor_dept_uuid:
            raise AuthorizationError(
                "No está autorizado para consultar instituciones fuera de su jurisdicción departamental.",
                code="PERMISSION_DENIED",
            )
        effective_municipality_id = actor_muni_uuid
        effective_department_id = actor_dept_uuid
    elif auth.scope.is_department():
        actor_dept_uuid = uuid.UUID(auth.scope.department_id)
        if department_id is not None and department_id != actor_dept_uuid:
            raise AuthorizationError(
                "No está autorizado para consultar instituciones fuera de su jurisdicción departamental.",
                code="PERMISSION_DENIED",
            )
        effective_department_id = actor_dept_uuid
    elif not (auth.scope.is_national() or SystemRole.SUPERADMIN in auth.roles or SystemRole.NATIONAL_ADMIN in auth.roles):
        raise AuthorizationError(
            "Se requiere alcance territorial o nacional para consultar el catálogo general de instituciones.",
            code="PERMISSION_DENIED",
        )

    service = InstitutionService(session=db)
    items, total = await service.list_institutions(
        department_id=effective_department_id,
        municipality_id=effective_municipality_id,
        is_active=is_active,
        search=search,
        page=page,
        page_size=page_size,
    )
    return InstitutionListResponse(
        items=[InstitutionResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/catalog-explorer",
    response_model=OfficialCatalogListResponse,
    status_code=status.HTTP_200_OK,
    summary="Explorador del catálogo oficial ministerial con estado de aprovisionamiento en tiempo real",
    description="Permite a los administradores territoriales y nacionales descubrir los establecimientos educativos oficiales de su jurisdicción con sus sedes y estado PEVN.",
)
async def list_catalog_explorer(
    auth: Annotated[
        AuthContextDep, Depends(require_permission("institutions", "read"))
    ],
    db: SessionDep,
    department_code: str | None = Query(None, description="Filtrar por código DANE departamental"),
    municipality_code: str | None = Query(None, description="Filtrar por código DANE municipal"),
    search: str | None = Query(None, description="Búsqueda por nombre o código DANE"),
    status_filter: str | None = Query(None, description="Filtrar por estado del ciclo de vida"),
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(20, ge=1, le=100, description="Tamaño de página"),
) -> OfficialCatalogListResponse:
    effective_dept_code = department_code
    effective_muni_code = municipality_code

    # Territorial isolation enforcement
    if auth.scope.is_municipality():
        actor_muni_uuid = uuid.UUID(auth.scope.municipality_id)
        muni_obj = (await db.execute(select(Municipality).where(Municipality.id == actor_muni_uuid))).scalar_one_or_none()
        if not muni_obj:
            raise AuthorizationError("Jurisdicción municipal no encontrada.", code="PERMISSION_DENIED")
        if municipality_code is not None and municipality_code != muni_obj.code:
            raise AuthorizationError(
                "No está autorizado para consultar el catálogo fuera de su jurisdicción municipal.",
                code="PERMISSION_DENIED",
            )
        effective_muni_code = muni_obj.code
        if department_code is not None:
            dept_obj = (await db.execute(select(Department).where(Department.id == muni_obj.department_id))).scalar_one_or_none()
            if dept_obj and department_code != dept_obj.code:
                raise AuthorizationError(
                    "No está autorizado para consultar el catálogo fuera de su departamento.",
                    code="PERMISSION_DENIED",
                )
    elif auth.scope.is_department():
        actor_dept_uuid = uuid.UUID(auth.scope.department_id)
        dept_obj = (await db.execute(select(Department).where(Department.id == actor_dept_uuid))).scalar_one_or_none()
        if not dept_obj:
            raise AuthorizationError("Jurisdicción departamental no encontrada.", code="PERMISSION_DENIED")
        if department_code is not None and department_code != dept_obj.code:
            raise AuthorizationError(
                "No está autorizado para consultar el catálogo fuera de su jurisdicción departamental.",
                code="PERMISSION_DENIED",
            )
        effective_dept_code = dept_obj.code
    elif not (auth.scope.is_national() or SystemRole.SUPERADMIN in auth.roles or SystemRole.NATIONAL_ADMIN in auth.roles):
        raise AuthorizationError(
            "Se requiere alcance territorial o nacional para consultar el catálogo de instituciones.",
            code="PERMISSION_DENIED",
        )

    service = InstitutionService(session=db)
    return await service.list_official_catalog_with_status(
        department_code=effective_dept_code,
        municipality_code=effective_muni_code,
        search=search,
        status_filter=status_filter,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/provision-catalog",
    response_model=InstitutionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Aprovisionar establecimiento educativo oficial desde el catálogo gubernamental",
    description="Convierte un establecimiento oficial validado del DANE/MEN en un tenant operacional PEVN con sus sedes registradas.",
)
async def provision_institution_from_catalog(
    payload: ProvisionCatalogInstitutionRequest,
    current_user: CurrentUserDep,
    auth: Annotated[
        AuthContextDep, Depends(require_permission("institutions", "read"))
    ],
    db: SessionDep,
    request: Request,
) -> InstitutionResponse:
    # Security: Only authorized administrative roles may provision
    allowed_roles = {
        SystemRole.SUPERADMIN,
        SystemRole.NATIONAL_ADMIN,
        SystemRole.DEPARTMENT_ADMIN,
        SystemRole.MUNICIPALITY_ADMIN,
    }
    if not any(r in allowed_roles for r in auth.roles):
        raise AuthorizationError(
            "No posee facultades para aprovisionar instituciones educativas.",
            code="PERMISSION_DENIED",
        )

    service = InstitutionService(session=db)
    actor_ip = request.client.host if request.client else "0.0.0.0"
    correlation_id = getattr(request.state, "correlation_id", None)

    institution = await service.provision_from_catalog(
        dane_code=payload.dane_code,
        auth_context=auth,
        actor_id=current_user.id,
        actor_ip=actor_ip,
        correlation_id=correlation_id,
        contact_email=payload.contact_email,
        contact_phone=payload.contact_phone,
    )
    await db.commit()
    return InstitutionResponse.model_validate(institution)


@router.get(
    "/resolve-dane/{dane_code}",
    response_model=OfficialInstitutionResolutionResponse,
    status_code=status.HTTP_200_OK,
    summary="Resolver institución por código DANE oficial",
    description="Consulta y resuelve los datos oficiales de un establecimiento educativo desde el catálogo gubernamental DANE/MEN.",
)
async def resolve_dane_institution(
    dane_code: str,
    current_user: CurrentUserDep,
    auth: Annotated[
        AuthContextDep, Depends(require_permission("institutions", "create"))
    ],
    db: SessionDep,
    request: Request,
) -> OfficialInstitutionResolutionResponse:
    # Security: Restrict resolution to National Scope (NATIONAL_ADMIN or SUPERADMIN)
    if not (auth.scope.is_national() or SystemRole.SUPERADMIN in auth.roles or SystemRole.NATIONAL_ADMIN in auth.roles):
        raise AuthorizationError(
            "Se requiere alcance nacional para resolver códigos DANE en el catálogo oficial.",
            code="PERMISSION_DENIED",
        )

    service = InstitutionService(session=db)
    resolved = await service.resolve_official_dane(
        dane_code=dane_code,
        actor_id=current_user.id,
        actor_ip=request.client.host if request.client else "0.0.0.0",
        correlation_id=request.headers.get("X-Correlation-ID"),
    )
    await db.commit()
    return resolved


@router.get(
    "/me",
    response_model=InstitutionResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener institución del usuario autenticado",
    description="Devuelve la información de la institución educativa a la cual pertenece el usuario en sesión.",
)
async def get_my_institution(
    current_user: CurrentUserDep,
    auth: AuthContextDep,
    db: SessionDep,
) -> InstitutionResponse:
    effective_inst_id = current_user.institution_id
    if not effective_inst_id and auth.scope.institution_id:
        try:
            effective_inst_id = uuid.UUID(auth.scope.institution_id)
        except (ValueError, TypeError):
            pass

    if not effective_inst_id:
        raise NotFoundError("El usuario no tiene una institución educativa asociada.")

    service = InstitutionService(session=db)
    institution = await service.get_institution_by_id(institution_id=effective_inst_id)

    return InstitutionResponse.model_validate(institution)


@router.get(
    "/{institution_id}",
    response_model=InstitutionResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar institución por ID",
    description="Devuelve la información de una institución verificando permisos organizacionales.",
)
async def get_institution_by_id(
    institution_id: uuid.UUID,
    db: SessionDep,
    auth: Annotated[
        AuthContextDep, Depends(require_permission("institutions", "read"))
    ],
) -> InstitutionResponse:
    service = InstitutionService(session=db)
    institution = await service.get_institution_by_id(institution_id=institution_id)

    # Validate organizational scope barrier (prevent cross-tenant access)
    target_dept_id = None
    if institution.municipality and institution.municipality.department_id:
        target_dept_id = str(institution.municipality.department_id)

    target_scope = OrganizationalScope(
        country_code="CO",
        department_id=target_dept_id,
        municipality_id=str(institution.municipality_id) if institution.municipality_id else None,
        institution_id=str(institution.id),
    )
    await authorization_service.require(
        auth,
        required_permission=SecurityPermission(resource="institutions", action="read"),
        target_scope=target_scope,
    )

    return InstitutionResponse.model_validate(institution)


@router.patch(
    "/{institution_id}/status",
    response_model=InstitutionResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar estado operativo de la institución",
    description="Permite activar o suspender una institución educativa a nivel nacional.",
)
async def update_institution_status(
    institution_id: uuid.UUID,
    payload: InstitutionStatusUpdateRequest,
    current_user: CurrentUserDep,
    auth: Annotated[
        AuthContextDep, Depends(require_permission("institutions", "update"))
    ],
    db: SessionDep,
    request: Request,
) -> InstitutionResponse:
    if not (auth.scope.is_national() or SystemRole.SUPERADMIN in auth.roles or SystemRole.NATIONAL_ADMIN in auth.roles):
        raise AuthorizationError(
            "Solo administradores nacionales pueden modificar el estado de una institución.",
            code="PERMISSION_DENIED",
        )

    service = InstitutionService(session=db)
    institution = await service.update_institution_status(
        institution_id=institution_id,
        is_active=payload.is_active,
        actor_id=current_user.id,
        actor_ip=request.client.host if request.client else "0.0.0.0",
        correlation_id=request.headers.get("X-Correlation-ID"),
    )
    await db.commit()
    return InstitutionResponse.model_validate(institution)


async def _assert_rector_management_authority(
    db: SessionDep,
    auth: AuthContextDep,
    institution_id: uuid.UUID,
    action_label: str = "gestionar la titularidad de Rectores",
) -> tuple[Institution, str]:
    """Enforces strict territorial jurisdiction for Rector invitation and revocation, classifying authority level."""
    inst_stmt = (
        select(Institution)
        .where(Institution.id == institution_id)
        .options(selectinload(Institution.municipality))
    )
    inst = (await db.execute(inst_stmt)).scalar_one_or_none()
    if not inst:
        raise NotFoundError(
            f"Institución educativa {institution_id} no encontrada.",
            code="INSTITUTION_NOT_FOUND",
        )

    # 1. Exceptional Platform Infrastructure / Emergency Override
    if SystemRole.SUPERADMIN in auth.roles:
        return inst, "superadmin_emergency"

    # 2. National Supervisory Escalation
    if SystemRole.NATIONAL_ADMIN in auth.roles or auth.scope.is_national():
        return inst, "national_supervisory"

    # 3. Department Supervisory Escalation
    if SystemRole.DEPARTMENT_ADMIN in auth.roles or auth.scope.is_department():
        dept_uuid = uuid.UUID(auth.scope.department_id) if auth.scope.department_id else None
        inst_dept_id = inst.municipality.department_id if inst.municipality else None
        if not dept_uuid or inst_dept_id != dept_uuid:
            raise AuthorizationError(
                f"No está autorizado para {action_label} fuera de su jurisdicción departamental.",
                code="PERMISSION_DENIED",
            )
        return inst, "department_supervisory"

    # 4. Normal Municipal Business Path
    if SystemRole.MUNICIPALITY_ADMIN in auth.roles or auth.scope.is_municipality():
        muni_uuid = uuid.UUID(auth.scope.municipality_id) if auth.scope.municipality_id else None
        if not muni_uuid or inst.municipality_id != muni_uuid:
            raise AuthorizationError(
                f"No está autorizado para {action_label} fuera de su jurisdicción municipal.",
                code="PERMISSION_DENIED",
            )
        return inst, "normal_municipal"

    raise AuthorizationError(
        f"No posee facultades administrativas territoriales para {action_label}.",
        code="PERMISSION_DENIED",
    )


@router.post(
    "/{institution_id}/rector-invitation",
    response_model=RectorInvitationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generar invitación de onboarding para Rector",
    description="Pre-registra la cuenta del Rector y genera un token criptográfico de un solo uso. Proceso de plataforma, no acto administrativo gubernamental.",
)
async def invite_rector_endpoint(
    institution_id: uuid.UUID,
    payload: RectorInvitationCreateRequest,
    current_user: CurrentUserDep,
    auth: Annotated[
        AuthContextDep, Depends(require_permission("users", "create_rector"))
    ],
    db: SessionDep,
    request: Request,
) -> RectorInvitationResponse:
    inst, authority_level = await _assert_rector_management_authority(
        db=db,
        auth=auth,
        institution_id=institution_id,
        action_label="emitir invitaciones para Rectores",
    )

    onboarding_service = RectorOnboardingService(session=db)
    result = await onboarding_service.invite_rector(
        institution_id=institution_id,
        first_name=payload.first_name,
        last_name=payload.last_name,
        document_type=payload.document_type,
        document_number=payload.document_number,
        email=payload.email,
        phone_number=payload.phone_number,
        invited_by_id=current_user.id,
        invited_by_ip=request.client.host if request.client else "0.0.0.0",
        correlation_id=request.headers.get("X-Correlation-ID"),
        authority_level=authority_level,
    )
    invitation, raw_token = result
    await db.commit()

    settings = get_settings()
    raw_token_out = raw_token if settings.is_development else None
    activation_url = getattr(result, "activation_url", None) or settings.build_invitation_url(raw_token)
    invitation_url_out = activation_url if settings.is_development else None

    return RectorInvitationResponse(
        invitation_id=invitation.id,
        institution_id=invitation.institution_id,
        user_id=invitation.user_id,
        email=payload.email,
        expires_at=invitation.expires_at,
        is_used=invitation.is_used,
        raw_invitation_token=raw_token_out,
        email_delivery_status=getattr(result, "delivery_status", EmailDeliveryStatus.EMAIL_NOT_CONFIGURED),
        invitation_url=invitation_url_out,
    )


@router.post(
    "/{institution_id}/rector-invitation/resend",
    response_model=RectorInvitationResponse,
    status_code=status.HTTP_200_OK,
    summary="Reenviar invitación de onboarding para Rector",
    description="Invalida invitaciones pendientes anteriores y genera un nuevo enlace de activación de un solo uso para el Rector pendiente de la institución.",
)
async def resend_rector_invitation_endpoint(
    institution_id: uuid.UUID,
    current_user: CurrentUserDep,
    auth: Annotated[
        AuthContextDep, Depends(require_permission("users", "create_rector"))
    ],
    db: SessionDep,
    request: Request,
) -> RectorInvitationResponse:
    inst, authority_level = await _assert_rector_management_authority(
        db=db,
        auth=auth,
        institution_id=institution_id,
        action_label="reenviar invitaciones para Rectores",
    )

    onboarding_service = RectorOnboardingService(session=db)
    result = await onboarding_service.resend_invitation(
        institution_id=institution_id,
        actor_id=current_user.id,
        actor_ip=request.client.host if request.client else "0.0.0.0",
        correlation_id=request.headers.get("X-Correlation-ID"),
        authority_level=authority_level,
    )
    invitation, raw_token = result
    await db.commit()

    settings = get_settings()
    raw_token_out = raw_token if settings.is_development else None
    activation_url = getattr(result, "activation_url", None) or settings.build_invitation_url(raw_token)
    invitation_url_out = activation_url if settings.is_development else None

    from app.models.user import User
    target_user = await db.get(User, invitation.user_id)
    user_email = target_user.email if target_user else ""

    return RectorInvitationResponse(
        invitation_id=invitation.id,
        institution_id=invitation.institution_id,
        user_id=invitation.user_id,
        email=user_email,
        expires_at=invitation.expires_at,
        is_used=invitation.is_used,
        raw_invitation_token=raw_token_out,
        email_delivery_status=getattr(result, "delivery_status", EmailDeliveryStatus.EMAIL_NOT_CONFIGURED),
        invitation_url=invitation_url_out,
    )


@router.post(
    "/{institution_id}/rector/revoke",
    response_model=RectorRevocationResponse,
    status_code=status.HTTP_200_OK,
    summary="Revocar la titularidad del Rector activo",
    description="Desactiva la asociación de Rector activo para la institución, revocando invitaciones pendientes y habilitando la emisión de una nueva invitación.",
)
async def revoke_rector_endpoint(
    institution_id: uuid.UUID,
    payload: RectorRevocationRequest,
    current_user: CurrentUserDep,
    auth: Annotated[
        AuthContextDep, Depends(require_permission("users", "create_rector"))
    ],
    db: SessionDep,
    request: Request,
) -> RectorRevocationResponse:
    inst, authority_level = await _assert_rector_management_authority(
        db=db,
        auth=auth,
        institution_id=institution_id,
        action_label="revocar la titularidad de un Rector",
    )

    onboarding_service = RectorOnboardingService(session=db)
    revoked_user, reason = await onboarding_service.revoke_rector(
        institution_id=institution_id,
        reason=payload.reason,
        justification=payload.justification,
        revoked_by_id=current_user.id,
        revoked_by_ip=request.client.host if request.client else "0.0.0.0",
        correlation_id=request.headers.get("X-Correlation-ID"),
        authority_level=authority_level,
    )
    await db.commit()

    return RectorRevocationResponse(
        institution_id=institution_id,
        revoked_user_id=revoked_user.id,
        revoked_rector_email=revoked_user.email,
        revoked_rector_name=f"{revoked_user.first_name} {revoked_user.last_name}",
        reason=reason,
        revoked_at=datetime.now(UTC),
        message=f"Titularidad de Rector para {revoked_user.first_name} {revoked_user.last_name} revocada exitosamente. La institución se encuentra disponible para nueva designación.",
    )


# --------------------------------------------------------------------------
# Rector-Controlled Coordinator Operational Delegation Setting Endpoints
# --------------------------------------------------------------------------


@router.get(
    "/{institution_id}/settings/coordinator-delegation",
    response_model=CoordinatorDelegationSettingResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar estado de delegación operativa a coordinadores",
    description="Devuelve el estado de la bandera de delegación institucional para coordinadores.",
)
async def get_coordinator_delegation_setting_endpoint(
    institution_id: uuid.UUID,
    current_user: CurrentUserDep,
    auth: AuthContextDep,
    db: SessionDep,
) -> CoordinatorDelegationSettingResponse:
    role_names = {r.value if isinstance(r, SystemRole) else str(r).lower() for r in auth.roles}
    is_superadmin = "superadmin" in role_names
    is_rector = "rector" in role_names

    if not is_superadmin:
        if is_rector:
            if not current_user.institution_id or current_user.institution_id != institution_id:
                raise AuthorizationError(
                    "No está autorizado para consultar la configuración de otra institución educativa.",
                    code="PERMISSION_DENIED",
                )
        else:
            raise AuthorizationError(
                "Solo el Rector de la institución educativa o SuperAdmin puede consultar la configuración de delegación operativa.",
                code="PERMISSION_DENIED",
            )

    service = InstitutionService(session=db)
    inst = await service.get_institution_by_id(institution_id=institution_id)

    return CoordinatorDelegationSettingResponse(
        institution_id=inst.id,
        coordinator_delegation_enabled=inst.coordinator_delegation_enabled,
        updated_at=inst.updated_at or datetime.now(UTC),
    )


@router.patch(
    "/{institution_id}/settings/coordinator-delegation",
    response_model=CoordinatorDelegationSettingResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar delegación operativa a coordinadores (Exclusivo Rector)",
    description="Permite al Rector habilitar o inhabilitar la facultad de creación/gestión de Docentes, Estudiantes y Acudientes a los Coordinadores de su institución.",
)
async def update_coordinator_delegation_setting_endpoint(
    institution_id: uuid.UUID,
    payload: CoordinatorDelegationSettingUpdateRequest,
    current_user: CurrentUserDep,
    auth: AuthContextDep,
    db: SessionDep,
    request: Request,
) -> CoordinatorDelegationSettingResponse:
    # 1. Authority Check: Only authenticated RECTOR of this institution or SUPERADMIN
    role_names = {r.value if isinstance(r, SystemRole) else str(r).lower() for r in auth.roles}
    is_superadmin = "superadmin" in role_names
    is_rector = "rector" in role_names

    if not (is_superadmin or is_rector):
        raise AuthorizationError(
            "Solo el Rector de la institución educativa o SuperAdmin puede modificar la delegación operativa para coordinadores.",
            code="PERMISSION_DENIED",
        )

    # 2. Strict Tenant Isolation: Rector can ONLY modify their own institution
    if not is_superadmin:
        if not current_user.institution_id:
            raise AuthorizationError(
                "El usuario Rector no tiene una institución educativa asignada.",
                code="PERMISSION_DENIED",
            )
        if institution_id != current_user.institution_id:
            raise AuthorizationError(
                "No está autorizado para modificar la configuración de otra institución educativa.",
                code="PERMISSION_DENIED",
            )
        effective_institution_id = current_user.institution_id
    else:
        effective_institution_id = institution_id

    service = InstitutionService(session=db)
    inst = await service.update_coordinator_delegation_setting(
        institution_id=effective_institution_id,
        enabled=payload.coordinator_delegation_enabled,
        actor_id=current_user.id,
        actor_ip=request.client.host if request.client else "0.0.0.0",
        correlation_id=request.headers.get("X-Correlation-ID"),
    )
    await db.commit()

    return CoordinatorDelegationSettingResponse(
        institution_id=inst.id,
        coordinator_delegation_enabled=inst.coordinator_delegation_enabled,
        updated_at=inst.updated_at or datetime.now(UTC),
    )

