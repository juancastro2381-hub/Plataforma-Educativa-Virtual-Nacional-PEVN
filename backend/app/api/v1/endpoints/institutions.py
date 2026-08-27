"""
PEVN Backend — Institutions API Endpoints

Handles institutional provisioning, tenant queries, operational status transitions,
and rector onboarding invitations for National Administrators.
"""

from __future__ import annotations

import uuid
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
from app.core.security.authorization import authorization_service
from app.core.security.interfaces import OrganizationalScope, SystemRole
from app.exceptions.errors import AuthorizationError, NotFoundError
from app.models.institution import Institution
from app.schemas.institution import (
    InstitutionCreate,
    InstitutionListResponse,
    InstitutionResponse,
    InstitutionStatusUpdateRequest,
)
from app.schemas.invitation import (
    RectorInvitationCreateRequest,
    RectorInvitationResponse,
)
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
    # Security: Require national scope or superadmin
    if not (auth.scope.is_national() or SystemRole.SUPERADMIN in auth.roles or SystemRole.NATIONAL_ADMIN in auth.roles):
        raise AuthorizationError(
            "Se requiere alcance nacional para consultar el catálogo general de instituciones.",
            code="PERMISSION_DENIED",
        )

    service = InstitutionService(session=db)
    items, total = await service.list_institutions(
        department_id=department_id,
        municipality_id=municipality_id,
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
    db: SessionDep,
) -> InstitutionResponse:
    if not current_user.institution_id:
        raise NotFoundError("El usuario no tiene una institución educativa asociada.")

    query = (
        select(Institution)
        .where(Institution.id == current_user.institution_id)
        .options(selectinload(Institution.campuses), selectinload(Institution.municipality))
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
    description="Devuelve la información de una institución verificando permisos organizacionales.",
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

    service = InstitutionService(session=db)
    institution = await service.get_institution_by_id(institution_id=institution_id)
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


@router.post(
    "/{institution_id}/rector-invitation",
    response_model=RectorInvitationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generar invitación de onboarding para Rector",
    description="Pre-registra la cuenta del Rector y genera un token criptográfico de un solo uso.",
)
async def invite_rector_endpoint(
    institution_id: uuid.UUID,
    payload: RectorInvitationCreateRequest,
    current_user: CurrentUserDep,
    auth: Annotated[
        AuthContextDep, Depends(require_permission("users", "create"))
    ],
    db: SessionDep,
    request: Request,
) -> RectorInvitationResponse:
    if not (auth.scope.is_national() or SystemRole.SUPERADMIN in auth.roles or SystemRole.NATIONAL_ADMIN in auth.roles):
        raise AuthorizationError(
            "Solo administradores nacionales pueden emitir invitaciones para Rectores.",
            code="PERMISSION_DENIED",
        )

    onboarding_service = RectorOnboardingService(session=db)
    invitation, raw_token = await onboarding_service.invite_rector(
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
    )
    await db.commit()

    return RectorInvitationResponse(
        invitation_id=invitation.id,
        institution_id=invitation.institution_id,
        user_id=invitation.user_id,
        email=payload.email,
        expires_at=invitation.expires_at,
        is_used=invitation.is_used,
        raw_invitation_token=raw_token,
    )
