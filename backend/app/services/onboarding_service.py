"""
PEVN Backend — Institution Onboarding Workflow Domain Service

Implements the NTA-04 National Provisioning Workflow governing the transformation
of official establishments from official_institution_catalog into fully provisioned
PEVN SaaS tenants.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.audit.interfaces import AuditEvent, AuditEventType
from app.audit.service import audit_service
from app.core.logging import get_logger
from app.core.security.interfaces import SystemRole
from app.exceptions.errors import (
    AuthorizationError,
    ConflictError,
    NotFoundError,
    UnprocessableEntityError,
)
from app.models.institution import Campus, Institution
from app.models.official_catalog import (
    OfficialCampusCatalog,
    OfficialInstitutionCatalog,
)
from app.models.onboarding import (
    InstitutionOnboardingRequest,
    OnboardingRequestStatus,
)
from app.models.territory import Department, Municipality
from app.models.user import DocumentType, User
from app.schemas.onboarding import (
    CatalogExplorerItemResponse,
    CatalogExplorerListResponse,
    OnboardingApprovalPayload,
    OnboardingCancellationPayload,
    OnboardingProvisionResultResponse,
    OnboardingRejectionPayload,
    OnboardingRequestCreatePayload,
    OnboardingRequestDetailResponse,
    OnboardingRequestListResponse,
)
from app.services.rector_onboarding_service import RectorOnboardingService

_logger = get_logger(__name__)


class OnboardingService:
    """
    Domain service governing institution onboarding requests and atomic tenant provisioning.
    """

    def __init__(
        self,
        session: AsyncSession,
        audit_svc: audit_service.__class__ = audit_service,
    ) -> None:
        self._session = session
        self._audit = audit_svc

    # --------------------------------------------------------------------------
    # Helper: Territorial Scope & User Context
    # --------------------------------------------------------------------------
    async def _resolve_user_department(self, user: User) -> Department | None:
        """Resolve the Department entity for a scoped Department Admin."""
        for ur in user.user_roles:
            if ur.is_active and getattr(ur, "department_id", None) is not None:
                dept_stmt = select(Department).where(Department.id == ur.department_id)
                return (await self._session.execute(dept_stmt)).scalar_one_or_none()
        return None

    def _is_national_admin(self, user: User) -> bool:
        """Return True if user has national administration authority."""
        for ur in user.user_roles:
            if ur.is_active and ur.role and ur.role.name in {
                SystemRole.SUPERADMIN.value,
                SystemRole.NATIONAL_ADMIN.value,
            }:
                return True
        return False

    def _is_department_admin(self, user: User) -> bool:
        """Return True if user is an active Department Administrator."""
        for ur in user.user_roles:
            if ur.is_active and ur.role and ur.role.name == SystemRole.DEPARTMENT_ADMIN.value:
                return True
        return False

    def _get_primary_role(self, user: User) -> str:
        """Get the primary active role name for a user."""
        for ur in user.user_roles:
            if ur.is_active and ur.role:
                return ur.role.name
        return "authenticated"

    # --------------------------------------------------------------------------
    # 1. Catalog Explorer (onboarding:discover)
    # --------------------------------------------------------------------------
    async def explore_catalog(
        self,
        *,
        actor: User,
        dane_code: str | None = None,
        name: str | None = None,
        department_id: uuid.UUID | None = None,
        municipality_id: uuid.UUID | None = None,
        onboarding_status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> CatalogExplorerListResponse:
        """
        Explore official educational catalog establishments with real-time PEVN status.
        Enforces strict territorial boundaries for Department Admins.
        """
        is_national = self._is_national_admin(actor)
        is_da = self._is_department_admin(actor)

        if not (is_national or is_da):
            raise AuthorizationError(
                "No está autorizado para explorar el catálogo de incorporación.",
                code="PERMISSION_DENIED",
            )

        actor_dept: Department | None = None
        if is_da and not is_national:
            actor_dept = await self._resolve_user_department(actor)
            if not actor_dept:
                raise AuthorizationError(
                    "El Administrador Departamental no tiene una jurisdicción departamental asignada.",
                    code="PERMISSION_DENIED",
                )
            if department_id is not None and department_id != actor_dept.id:
                raise AuthorizationError(
                    "No está autorizado para consultar establecimientos fuera de su jurisdicción departamental.",
                    code="PERMISSION_DENIED",
                )

        # Base query on OfficialInstitutionCatalog
        query = select(OfficialInstitutionCatalog).options(
            selectinload(OfficialInstitutionCatalog.campuses)
        )

        if actor_dept:
            query = query.where(OfficialInstitutionCatalog.department_code == actor_dept.code)
        elif department_id is not None:
            dept_res = (
                await self._session.execute(
                    select(Department).where(Department.id == department_id)
                )
            ).scalar_one_or_none()
            if dept_res:
                query = query.where(OfficialInstitutionCatalog.department_code == dept_res.code)

        if municipality_id is not None:
            muni_res = (
                await self._session.execute(
                    select(Municipality).where(Municipality.id == municipality_id)
                )
            ).scalar_one_or_none()
            if muni_res:
                query = query.where(OfficialInstitutionCatalog.municipality_code == muni_res.code)

        if dane_code:
            query = query.where(OfficialInstitutionCatalog.dane_code.ilike(f"%{dane_code.strip()}%"))

        if name:
            query = query.where(OfficialInstitutionCatalog.name.ilike(f"%{name.strip()}%"))

        # Preload active onboarding requests and provisioned institutions
        active_requests_query = select(InstitutionOnboardingRequest).where(
            InstitutionOnboardingRequest.status.in_(
                [
                    OnboardingRequestStatus.DRAFT.value,
                    OnboardingRequestStatus.SUBMITTED.value,
                    OnboardingRequestStatus.UNDER_REVIEW.value,
                    OnboardingRequestStatus.APPROVED.value,
                ]
            )
        )
        active_req_rows = (await self._session.execute(active_requests_query)).scalars().all()
        active_requests_map: dict[uuid.UUID, InstitutionOnboardingRequest] = {
            req.catalog_institution_id: req for req in active_req_rows
        }

        tenants_query = select(Institution)
        tenants_rows = (await self._session.execute(tenants_query)).scalars().all()
        tenants_by_catalog_id: dict[uuid.UUID, Institution] = {
            t.catalog_institution_id: t for t in tenants_rows if t.catalog_institution_id is not None
        }
        tenants_by_dane: dict[str, Institution] = {t.dane_code: t for t in tenants_rows}

        # Cache DIVIPOLA lookups
        depts_cache = {d.code: d for d in (await self._session.execute(select(Department))).scalars().all()}
        munis_cache = {m.code: m for m in (await self._session.execute(select(Municipality))).scalars().all()}

        # Fetch records
        all_records = (await self._session.execute(query.order_by(OfficialInstitutionCatalog.name))).scalars().all()

        # Classify status and filter
        enriched_items: list[CatalogExplorerItemResponse] = []
        for rec in all_records:
            status_label = "AVAILABLE"
            active_req_id: uuid.UUID | None = None
            active_req_num: str | None = None
            inst_id: uuid.UUID | None = None

            if rec.id in tenants_by_catalog_id or rec.dane_code in tenants_by_dane:
                status_label = "PROVISIONED"
                tenant = tenants_by_catalog_id.get(rec.id) or tenants_by_dane.get(rec.dane_code)
                if tenant:
                    inst_id = tenant.id
            elif rec.id in active_requests_map:
                status_label = "EN_TRAMITE"
                active_req = active_requests_map[rec.id]
                active_req_id = active_req.id
                active_req_num = active_req.request_number
            else:
                status_label = "AVAILABLE"

            if onboarding_status:
                norm_status = onboarding_status.upper().strip()
                if norm_status in {"INCORPORABLE", "AVAILABLE"} and status_label != "AVAILABLE":
                    continue
                if norm_status in {"EN_TRAMITE", "IN_PROGRESS"} and status_label != "EN_TRAMITE":
                    continue
                if norm_status in {"PROVISIONED", "OPERACIONAL"} and status_label != "PROVISIONED":
                    continue

            dept_obj = depts_cache.get(rec.department_code)
            muni_obj = munis_cache.get(rec.municipality_code)
            principal_campus = next((c for c in rec.campuses if c.is_main), None)
            if not principal_campus and rec.campuses:
                principal_campus = rec.campuses[0]

            enriched_items.append(
                CatalogExplorerItemResponse(
                    id=rec.id,
                    dane_code=rec.dane_code,
                    name=rec.name,
                    department_code=rec.department_code,
                    department_name=rec.department_name,
                    department_id=dept_obj.id if dept_obj else None,
                    municipality_code=rec.municipality_code,
                    municipality_name=rec.municipality_name,
                    municipality_id=muni_obj.id if muni_obj else None,
                    official_address=rec.official_address,
                    sector=rec.sector,
                    is_active=rec.is_active,
                    principal_campus_name=principal_campus.name if principal_campus else "Sede Principal",
                    campus_count=len(rec.campuses) if rec.campuses else 1,
                    onboarding_status=status_label,
                    active_request_id=active_req_id,
                    active_request_number=active_req_num,
                    institution_id=inst_id,
                )
            )

        total_items = len(enriched_items)
        total_pages = max(1, (total_items + page_size - 1) // page_size) if total_items > 0 else 1
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_items = enriched_items[start_idx:end_idx]

        return CatalogExplorerListResponse(
            items=paginated_items,
            total=total_items,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    # --------------------------------------------------------------------------
    # 2. Create Onboarding Request (onboarding:create)
    # --------------------------------------------------------------------------
    async def create_request(
        self,
        *,
        payload: OnboardingRequestCreatePayload,
        actor: User,
        actor_ip: str = "0.0.0.0",
        correlation_id: str | None = None,
    ) -> OnboardingRequestDetailResponse:
        """
        Create and file an institution onboarding request.
        """
        is_national = self._is_national_admin(actor)
        is_da = self._is_department_admin(actor)

        if not (is_national or is_da):
            raise AuthorizationError(
                "No está autorizado para radicar solicitudes de incorporación.",
                code="PERMISSION_DENIED",
            )

        # 1. Catalog reference check
        catalog_stmt = (
            select(OfficialInstitutionCatalog)
            .where(OfficialInstitutionCatalog.id == payload.catalog_institution_id)
            .options(selectinload(OfficialInstitutionCatalog.campuses))
        )
        catalog_record = (await self._session.execute(catalog_stmt)).scalar_one_or_none()
        if not catalog_record:
            raise NotFoundError(
                f"Establecimiento educativo {payload.catalog_institution_id} no encontrado en el catálogo oficial.",
                code="CATALOG_RECORD_NOT_FOUND",
            )

        # 2. Check catalog institution is active
        if not catalog_record.is_active:
            raise UnprocessableEntityError(
                "El establecimiento educativo se encuentra reportado como cerrado o inactivo en el catálogo nacional MEN/DANE.",
                code="CATALOG_INSTITUTION_INACTIVE",
            )

        # 3. Territorial Scope & Anti-IDOR check
        actor_dept: Department | None = None
        if is_da and not is_national:
            actor_dept = await self._resolve_user_department(actor)
            if not actor_dept or actor_dept.code != catalog_record.department_code:
                raise AuthorizationError(
                    "No está autorizado para iniciar incorporación de un establecimiento fuera de su jurisdicción departamental.",
                    code="PERMISSION_DENIED",
                )

        # 4. Check if tenant already exists in PEVN
        tenant_stmt = select(Institution).where(
            or_(
                Institution.catalog_institution_id == catalog_record.id,
                Institution.dane_code == catalog_record.dane_code,
            )
        )
        existing_tenant = (await self._session.execute(tenant_stmt)).scalar_one_or_none()
        if existing_tenant:
            raise ConflictError(
                "El establecimiento educativo ya se encuentra aprovisionado como tenant operacional en PEVN.",
                code="INSTITUTION_ALREADY_PROVISIONED",
            )

        # 5. Check if active onboarding request already exists
        active_req_stmt = select(InstitutionOnboardingRequest).where(
            InstitutionOnboardingRequest.catalog_institution_id == catalog_record.id,
            InstitutionOnboardingRequest.status.in_(
                [
                    OnboardingRequestStatus.DRAFT.value,
                    OnboardingRequestStatus.SUBMITTED.value,
                    OnboardingRequestStatus.UNDER_REVIEW.value,
                    OnboardingRequestStatus.APPROVED.value,
                ]
            ),
        )
        active_req = (await self._session.execute(active_req_stmt)).scalar_one_or_none()
        if active_req:
            raise ConflictError(
                f"Ya existe una solicitud activa en trámite para este establecimiento educativo (Radicado {active_req.request_number}).",
                code="ACTIVE_REQUEST_EXISTS",
            )

        # 6. Resolve operational DIVIPOLA entities
        dept_stmt = select(Department).where(Department.code == catalog_record.department_code)
        target_department = (await self._session.execute(dept_stmt)).scalar_one_or_none()

        muni_stmt = select(Municipality).where(Municipality.code == catalog_record.municipality_code)
        target_municipality = (await self._session.execute(muni_stmt)).scalar_one_or_none()

        if not target_department or not target_municipality:
            raise UnprocessableEntityError(
                "Inconsistencia DIVIPOLA: El departamento o municipio del catálogo no existe en la jerarquía territorial de PEVN.",
                code="TERRITORIAL_DIVIPOLA_MISMATCH",
            )

        # 7. Generate friendly filing number
        # Example format: ONB-2026-XXXXXX
        filing_suffix = uuid.uuid4().hex[:6].upper()
        current_year = datetime.now(UTC).year
        request_number = f"ONB-{current_year}-{filing_suffix}"

        initial_status = (
            OnboardingRequestStatus.DRAFT.value
            if payload.is_draft
            else OnboardingRequestStatus.SUBMITTED.value
        )
        primary_role = self._get_primary_role(actor)

        # 8. Create Entity
        onboarding_request = InstitutionOnboardingRequest(
            request_number=request_number,
            catalog_institution_id=catalog_record.id,
            dane_code=catalog_record.dane_code,
            department_id=target_department.id,
            municipality_id=target_municipality.id,
            requested_by_id=actor.id,
            requester_role=primary_role,
            status=initial_status,
            contact_email=payload.contact_email.strip().lower(),
            contact_phone=payload.contact_phone.strip() if payload.contact_phone else None,
            proposed_rector_name=payload.proposed_rector_name.strip() if payload.proposed_rector_name else None,
            proposed_rector_email=payload.proposed_rector_email.strip().lower() if payload.proposed_rector_email else None,
            proposed_rector_doc_type=payload.proposed_rector_doc_type.strip().upper() if payload.proposed_rector_doc_type else None,
            proposed_rector_doc_num=payload.proposed_rector_doc_num.strip() if payload.proposed_rector_doc_num else None,
            justification=payload.justification.strip() if payload.justification else None,
            idempotency_key=payload.idempotency_key.strip() if payload.idempotency_key else None,
        )
        self._session.add(onboarding_request)
        await self._session.flush()
        onboarding_request.department = target_department
        onboarding_request.municipality = target_municipality
        onboarding_request.requested_by = actor
        onboarding_request.catalog_institution = catalog_record

        # 9. Audit Trail
        audit_event_type = (
            AuditEventType.ONBOARDING_REQUEST_CREATED
            if payload.is_draft
            else AuditEventType.ONBOARDING_REQUEST_SUBMITTED
        )
        await self._audit.record(
            AuditEvent(
                event_type=audit_event_type,
                actor_id=str(actor.id),
                actor_ip=actor_ip,
                target_id=str(onboarding_request.id),
                target_type="InstitutionOnboardingRequest",
                correlation_id=correlation_id,
                metadata={
                    "request_number": request_number,
                    "catalog_id": str(catalog_record.id),
                    "dane_code": catalog_record.dane_code,
                    "institution_name": catalog_record.name,
                    "department_id": str(target_department.id),
                    "municipality_id": str(target_municipality.id),
                    "status": initial_status,
                },
            ),
            session=self._session,
        )

        return await self._build_detail_response(onboarding_request, catalog_record=catalog_record)

    # --------------------------------------------------------------------------
    # 3. Read Requests (onboarding:read)
    # --------------------------------------------------------------------------
    async def get_request_by_id(
        self,
        *,
        request_id: uuid.UUID,
        actor: User,
    ) -> OnboardingRequestDetailResponse:
        """
        Retrieve request detail with Anti-IDOR evaluation.
        """
        is_national = self._is_national_admin(actor)
        is_da = self._is_department_admin(actor)

        query = (
            select(InstitutionOnboardingRequest)
            .where(InstitutionOnboardingRequest.id == request_id)
            .options(
                selectinload(InstitutionOnboardingRequest.catalog_institution),
                selectinload(InstitutionOnboardingRequest.department),
                selectinload(InstitutionOnboardingRequest.municipality),
                selectinload(InstitutionOnboardingRequest.requested_by),
                selectinload(InstitutionOnboardingRequest.reviewed_by),
                selectinload(InstitutionOnboardingRequest.approved_by),
                selectinload(InstitutionOnboardingRequest.rejected_by),
                selectinload(InstitutionOnboardingRequest.cancelled_by),
                selectinload(InstitutionOnboardingRequest.provisioned_by),
            )
        )
        req = (await self._session.execute(query)).scalar_one_or_none()
        if not req:
            raise NotFoundError(
                f"Solicitud de incorporación {request_id} no encontrada.",
                code="ONBOARDING_REQUEST_NOT_FOUND",
            )

        if is_da and not is_national:
            actor_dept = await self._resolve_user_department(actor)
            if not actor_dept or actor_dept.id != req.department_id:
                raise AuthorizationError(
                    "No está autorizado para consultar solicitudes fuera de su jurisdicción departamental.",
                    code="PERMISSION_DENIED",
                )
        elif not is_national and req.requested_by_id != actor.id:
            raise AuthorizationError(
                "No está autorizado para consultar esta solicitud.",
                code="PERMISSION_DENIED",
            )

        return await self._build_detail_response(req)

    async def list_requests(
        self,
        *,
        actor: User,
        status: str | None = None,
        department_id: uuid.UUID | None = None,
        municipality_id: uuid.UUID | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> OnboardingRequestListResponse:
        """
        List onboarding requests with strict territorial scoping.
        """
        is_national = self._is_national_admin(actor)
        is_da = self._is_department_admin(actor)

        if not (is_national or is_da):
            raise AuthorizationError(
                "No está autorizado para listar solicitudes de incorporación.",
                code="PERMISSION_DENIED",
            )

        query = select(InstitutionOnboardingRequest).options(
            selectinload(InstitutionOnboardingRequest.catalog_institution),
            selectinload(InstitutionOnboardingRequest.department),
            selectinload(InstitutionOnboardingRequest.municipality),
            selectinload(InstitutionOnboardingRequest.requested_by),
            selectinload(InstitutionOnboardingRequest.reviewed_by),
            selectinload(InstitutionOnboardingRequest.approved_by),
            selectinload(InstitutionOnboardingRequest.rejected_by),
            selectinload(InstitutionOnboardingRequest.cancelled_by),
            selectinload(InstitutionOnboardingRequest.provisioned_by),
        )

        if is_da and not is_national:
            actor_dept = await self._resolve_user_department(actor)
            if not actor_dept:
                raise AuthorizationError(
                    "El Administrador Departamental no tiene una jurisdicción departamental asignada.",
                    code="PERMISSION_DENIED",
                )
            if department_id is not None and department_id != actor_dept.id:
                raise AuthorizationError(
                    "No está autorizado para listar solicitudes de otros departamentos.",
                    code="PERMISSION_DENIED",
                )
            query = query.where(InstitutionOnboardingRequest.department_id == actor_dept.id)
        elif department_id is not None:
            query = query.where(InstitutionOnboardingRequest.department_id == department_id)

        if municipality_id is not None:
            query = query.where(InstitutionOnboardingRequest.municipality_id == municipality_id)

        if status:
            query = query.where(InstitutionOnboardingRequest.status == status.upper().strip())

        if search:
            s = f"%{search.strip()}%"
            query = query.where(
                or_(
                    InstitutionOnboardingRequest.request_number.ilike(s),
                    InstitutionOnboardingRequest.dane_code.ilike(s),
                    InstitutionOnboardingRequest.contact_email.ilike(s),
                )
            )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self._session.execute(count_query)).scalar_one()

        total_pages = max(1, (total + page_size - 1) // page_size) if total > 0 else 1
        query = query.order_by(InstitutionOnboardingRequest.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        rows = (await self._session.execute(query)).scalars().all()
        items = [await self._build_detail_response(r) for r in rows]

        return OnboardingRequestListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    # --------------------------------------------------------------------------
    # 4. State Transitions (review, approve, reject, cancel)
    # --------------------------------------------------------------------------
    async def start_review(
        self,
        *,
        request_id: uuid.UUID,
        actor: User,
        notes: str | None = None,
        actor_ip: str = "0.0.0.0",
        correlation_id: str | None = None,
    ) -> OnboardingRequestDetailResponse:
        """
        Transition request from SUBMITTED to UNDER_REVIEW.
        """
        req = await self._lock_and_validate_scope(request_id=request_id, actor=actor, action_name="revisar")

        if req.status != OnboardingRequestStatus.SUBMITTED.value:
            raise ConflictError(
                f"La solicitud se encuentra en estado '{req.status}'. Solo solicitudes en estado SUBMITTED pueden iniciar revisión.",
                code="ILLEGAL_STATE_TRANSITION",
            )

        req.status = OnboardingRequestStatus.UNDER_REVIEW.value
        req.reviewed_by_id = actor.id
        req.reviewed_by = actor
        req.reviewed_at = datetime.now(UTC)
        if notes:
            req.review_notes = notes.strip()
        req.lock_version += 1
        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.ONBOARDING_REQUEST_REVIEW_STARTED,
                actor_id=str(actor.id),
                actor_ip=actor_ip,
                target_id=str(req.id),
                target_type="InstitutionOnboardingRequest",
                correlation_id=correlation_id,
                metadata={
                    "request_number": req.request_number,
                    "previous_status": OnboardingRequestStatus.SUBMITTED.value,
                    "new_status": OnboardingRequestStatus.UNDER_REVIEW.value,
                },
            ),
            session=self._session,
        )
        return await self._build_detail_response(req)

    async def approve_request(
        self,
        *,
        request_id: uuid.UUID,
        actor: User,
        payload: OnboardingApprovalPayload | None = None,
        actor_ip: str = "0.0.0.0",
        correlation_id: str | None = None,
    ) -> OnboardingRequestDetailResponse:
        """
        Transition request to APPROVED.
        """
        req = await self._lock_and_validate_scope(request_id=request_id, actor=actor, action_name="aprobar")

        if req.status not in {
            OnboardingRequestStatus.SUBMITTED.value,
            OnboardingRequestStatus.UNDER_REVIEW.value,
        }:
            raise ConflictError(
                f"No se puede aprobar una solicitud en estado '{req.status}'. Transición ilegal.",
                code="ILLEGAL_STATE_TRANSITION",
            )

        prev_status = req.status
        req.status = OnboardingRequestStatus.APPROVED.value
        req.approved_by_id = actor.id
        req.approved_by = actor
        req.approved_at = datetime.now(UTC)
        if payload and payload.notes:
            req.review_notes = (
                f"{req.review_notes}\n[Aprobación]: {payload.notes.strip()}"
                if req.review_notes
                else payload.notes.strip()
            )
        req.lock_version += 1
        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.ONBOARDING_REQUEST_APPROVED,
                actor_id=str(actor.id),
                actor_ip=actor_ip,
                target_id=str(req.id),
                target_type="InstitutionOnboardingRequest",
                correlation_id=correlation_id,
                metadata={
                    "request_number": req.request_number,
                    "previous_status": prev_status,
                    "new_status": OnboardingRequestStatus.APPROVED.value,
                },
            ),
            session=self._session,
        )
        return await self._build_detail_response(req)

    async def reject_request(
        self,
        *,
        request_id: uuid.UUID,
        payload: OnboardingRejectionPayload,
        actor: User,
        actor_ip: str = "0.0.0.0",
        correlation_id: str | None = None,
    ) -> OnboardingRequestDetailResponse:
        """
        Transition request to REJECTED with mandatory reason.
        """
        cleaned_reason = payload.rejection_reason.strip()
        if len(cleaned_reason) < 10:
            raise UnprocessableEntityError(
                "La causal de rechazo debe contener un mínimo de 10 caracteres explicativos.",
                code="REJECTION_REASON_REQUIRED",
            )

        req = await self._lock_and_validate_scope(request_id=request_id, actor=actor, action_name="rechazar")

        if req.status in {
            OnboardingRequestStatus.PROVISIONED.value,
            OnboardingRequestStatus.REJECTED.value,
            OnboardingRequestStatus.CANCELLED.value,
        }:
            raise ConflictError(
                f"No se puede rechazar una solicitud en estado terminal '{req.status}'.",
                code="ILLEGAL_STATE_TRANSITION",
            )

        prev_status = req.status
        req.status = OnboardingRequestStatus.REJECTED.value
        req.rejected_by_id = actor.id
        req.rejected_by = actor
        req.rejected_at = datetime.now(UTC)
        req.rejection_reason = cleaned_reason
        req.lock_version += 1
        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.ONBOARDING_REQUEST_REJECTED,
                actor_id=str(actor.id),
                actor_ip=actor_ip,
                target_id=str(req.id),
                target_type="InstitutionOnboardingRequest",
                correlation_id=correlation_id,
                metadata={
                    "request_number": req.request_number,
                    "previous_status": prev_status,
                    "new_status": OnboardingRequestStatus.REJECTED.value,
                    "reason": cleaned_reason,
                },
            ),
            session=self._session,
        )
        return await self._build_detail_response(req)

    async def cancel_request(
        self,
        *,
        request_id: uuid.UUID,
        payload: OnboardingCancellationPayload | None = None,
        actor: User,
        actor_ip: str = "0.0.0.0",
        correlation_id: str | None = None,
    ) -> OnboardingRequestDetailResponse:
        """
        Cancel request. Can only be cancelled by the requester or national admin.
        """
        stmt = (
            select(InstitutionOnboardingRequest)
            .where(InstitutionOnboardingRequest.id == request_id)
            .with_for_update()
        )
        req = (await self._session.execute(stmt)).scalar_one_or_none()
        if not req:
            raise NotFoundError(
                f"Solicitud de incorporación {request_id} no encontrada.",
                code="ONBOARDING_REQUEST_NOT_FOUND",
            )

        is_national = self._is_national_admin(actor)
        if not is_national and req.requested_by_id != actor.id:
            raise AuthorizationError(
                "Solo el usuario solicitante o un Administrador Nacional pueden cancelar esta solicitud.",
                code="PERMISSION_DENIED",
            )

        if req.status in {
            OnboardingRequestStatus.PROVISIONED.value,
            OnboardingRequestStatus.REJECTED.value,
            OnboardingRequestStatus.CANCELLED.value,
        }:
            raise ConflictError(
                f"No se puede cancelar una solicitud en estado terminal '{req.status}'.",
                code="ILLEGAL_STATE_TRANSITION",
            )

        prev_status = req.status
        req.status = OnboardingRequestStatus.CANCELLED.value
        req.cancelled_by_id = actor.id
        req.cancelled_by = actor
        req.cancelled_at = datetime.now(UTC)
        if payload and payload.cancellation_reason:
            req.cancellation_reason = payload.cancellation_reason.strip()
        req.lock_version += 1
        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.ONBOARDING_REQUEST_CANCELLED,
                actor_id=str(actor.id),
                actor_ip=actor_ip,
                target_id=str(req.id),
                target_type="InstitutionOnboardingRequest",
                correlation_id=correlation_id,
                metadata={
                    "request_number": req.request_number,
                    "previous_status": prev_status,
                    "new_status": OnboardingRequestStatus.CANCELLED.value,
                },
            ),
            session=self._session,
        )
        return await self._build_detail_response(req)

    # --------------------------------------------------------------------------
    # 5. Atomic Provisioning (onboarding:provision)
    # --------------------------------------------------------------------------
    async def provision_request(
        self,
        *,
        request_id: uuid.UUID,
        actor: User,
        actor_ip: str = "0.0.0.0",
        correlation_id: str | None = None,
    ) -> OnboardingProvisionResultResponse:
        """
        Execute atomic tenant creation from approved onboarding request.
        Four-Tier concurrency protection (Pessimistic lock + In-memory state check
        + Partial unique index + DANE unique constraint).
        """
        # CAPA 1: SELECT ... FOR UPDATE (Pessimistic row lock)
        req = await self._lock_and_validate_scope(request_id=request_id, actor=actor, action_name="aprovisionar")

        # CAPA 2: Fresh state validation
        if req.status != OnboardingRequestStatus.APPROVED.value:
            raise ConflictError(
                f"La solicitud se encuentra en estado '{req.status}'. Debe encontrarse en estado APPROVED para aprovisionar.",
                code="ILLEGAL_PROVISION_STATE",
            )

        # Catalog record validation
        catalog_stmt = (
            select(OfficialInstitutionCatalog)
            .where(OfficialInstitutionCatalog.id == req.catalog_institution_id)
            .options(selectinload(OfficialInstitutionCatalog.campuses))
        )
        catalog_record = (await self._session.execute(catalog_stmt)).scalar_one_or_none()
        if not catalog_record:
            raise NotFoundError(
                "El establecimiento oficial del catálogo vinculado a la solicitud no existe.",
                code="CATALOG_RECORD_NOT_FOUND",
            )

        # CAPA 3 & 4: Tenant uniqueness check
        tenant_stmt = select(Institution).where(
            or_(
                Institution.catalog_institution_id == req.catalog_institution_id,
                Institution.dane_code == req.dane_code,
            )
        )
        existing_tenant = (await self._session.execute(tenant_stmt)).scalar_one_or_none()
        if existing_tenant:
            raise ConflictError(
                "El establecimiento educativo ya se encuentra aprovisionado como tenant operacional en PEVN.",
                code="INSTITUTION_ALREADY_PROVISIONED",
            )

        # 1. Create Institution (Tenant)
        institution = Institution(
            municipality_id=req.municipality_id,
            catalog_institution_id=req.catalog_institution_id,
            dane_code=req.dane_code,
            name=catalog_record.name.strip(),
            email=req.contact_email.strip().lower(),
            phone=req.contact_phone.strip() if req.contact_phone else None,
            address=catalog_record.official_address.strip() if catalog_record.official_address else None,
            is_active=True,
        )
        self._session.add(institution)
        await self._session.flush()

        # 2. Materialize Campuses (Sedes)
        campuses_created_count = 0
        if catalog_record.campuses:
            for c in catalog_record.campuses:
                campus = Campus(
                    institution_id=institution.id,
                    dane_sede_code=c.dane_sede_code,
                    name=c.name.strip(),
                    address=c.address.strip() if c.address else (catalog_record.official_address.strip() if catalog_record.official_address else None),
                    is_active=c.is_active,
                )
                self._session.add(campus)
                campuses_created_count += 1
            await self._session.flush()
        else:
            # Fallback principal campus
            main_campus = Campus(
                institution_id=institution.id,
                dane_sede_code=f"{req.dane_code}01",
                name="Sede Principal",
                address=catalog_record.official_address.strip() if catalog_record.official_address else None,
                is_active=True,
            )
            self._session.add(main_campus)
            campuses_created_count = 1
            await self._session.flush()

        # 3. Transition request to PROVISIONED
        req.status = OnboardingRequestStatus.PROVISIONED.value
        req.institution_id = institution.id
        req.provisioned_by_id = actor.id
        req.provisioned_by = actor
        req.provisioned_at = datetime.now(UTC)
        req.lock_version += 1
        await self._session.flush()

        # 4. Rector Integration (if proposed rector data was supplied)
        rector_invited = False
        rector_status = "PENDING_ASSIGNMENT"
        rector_inv_id: uuid.UUID | None = None
        activation_url: str | None = None
        raw_invitation_token: str | None = None

        if req.proposed_rector_email:
            try:
                name_parts = (req.proposed_rector_name or "Rector Institucional").strip().split(" ", 1)
                first_name = name_parts[0]
                last_name = name_parts[1] if len(name_parts) > 1 else "Institucional"

                doc_type_val = (req.proposed_rector_doc_type or "CC").strip().upper()
                try:
                    doc_type = DocumentType(doc_type_val)
                except ValueError:
                    doc_type = DocumentType.CC

                doc_num = req.proposed_rector_doc_num.strip() if req.proposed_rector_doc_num else f"CC{institution.dane_code[:8]}"

                rector_service = RectorOnboardingService(session=self._session, audit_svc=self._audit)
                inv_result = await rector_service.invite_rector(
                    institution_id=institution.id,
                    first_name=first_name,
                    last_name=last_name,
                    document_type=doc_type,
                    document_number=doc_num,
                    email=req.proposed_rector_email.strip().lower(),
                    phone_number=req.contact_phone,
                    invited_by_id=actor.id,
                    invited_by_ip=actor_ip,
                    correlation_id=correlation_id,
                )
                rector_inv = inv_result[0]
                raw_invitation_token = inv_result[1]
                rector_inv_id = rector_inv.id
                activation_url = getattr(inv_result, "activation_url", None) or f"/accept-invitation?token={raw_invitation_token}"
                rector_invited = True
                rector_status = "INVITED"
            except Exception as e:
                _logger.error(
                    "Error encadenando invitación rectoral durante aprovisionamiento",
                    error=str(e),
                    request_id=str(req.id),
                )
                # If rector invitation fails due to collision, mark as pending assignment but proceed with tenant
                rector_invited = False
                rector_status = "PENDING_ASSIGNMENT"

        # 5. Immutable Audit Event
        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.INSTITUTION_PROVISIONED_FROM_ONBOARDING,
                actor_id=str(actor.id),
                actor_ip=actor_ip,
                target_id=str(institution.id),
                target_type="Institution",
                institution_id=str(institution.id),
                correlation_id=correlation_id,
                metadata={
                    "request_id": str(req.id),
                    "request_number": req.request_number,
                    "catalog_id": str(req.catalog_institution_id),
                    "dane_code": req.dane_code,
                    "institution_name": institution.name,
                    "campuses_count": campuses_created_count,
                    "rector_invited": rector_invited,
                },
            ),
            session=self._session,
        )

        return OnboardingProvisionResultResponse(
            request_id=req.id,
            request_number=req.request_number,
            institution_id=institution.id,
            institution_name=institution.name,
            dane_code=institution.dane_code,
            campuses_created=campuses_created_count,
            rector_invited=rector_invited,
            rector_status=rector_status,
            rector_invitation_id=rector_inv_id,
            activation_url=activation_url,
            raw_invitation_token=raw_invitation_token,
        )

    # --------------------------------------------------------------------------
    # Helper: Lock and Anti-IDOR evaluation
    # --------------------------------------------------------------------------
    async def _lock_and_validate_scope(
        self,
        *,
        request_id: uuid.UUID,
        actor: User,
        action_name: str,
    ) -> InstitutionOnboardingRequest:
        """
        Acquire pessimistic lock and enforce territorial isolation.
        """
        is_national = self._is_national_admin(actor)
        is_da = self._is_department_admin(actor)

        if not (is_national or is_da):
            raise AuthorizationError(
                f"No está autorizado para {action_name} solicitudes de incorporación.",
                code="PERMISSION_DENIED",
            )

        stmt = (
            select(InstitutionOnboardingRequest)
            .where(InstitutionOnboardingRequest.id == request_id)
            .with_for_update()
        )
        req = (await self._session.execute(stmt)).scalar_one_or_none()
        if not req:
            raise NotFoundError(
                f"Solicitud de incorporación {request_id} no encontrada.",
                code="ONBOARDING_REQUEST_NOT_FOUND",
            )

        if is_da and not is_national:
            actor_dept = await self._resolve_user_department(actor)
            if not actor_dept or actor_dept.id != req.department_id:
                raise AuthorizationError(
                    f"No está autorizado para {action_name} solicitudes fuera de su jurisdicción departamental.",
                    code="PERMISSION_DENIED",
                )

        return req

    # --------------------------------------------------------------------------
    # Helper: Build Detail Response
    # --------------------------------------------------------------------------
    async def _safe_get_user(
        self,
        user_id: uuid.UUID | None,
        rel_name: str,
        req: InstitutionOnboardingRequest,
    ) -> User | None:
        if not user_id:
            return None
        if rel_name in req.__dict__ and req.__dict__[rel_name] is not None:
            return req.__dict__[rel_name]
        return await self._session.get(User, user_id)

    async def _safe_get_department(
        self,
        dept_id: uuid.UUID | None,
        req: InstitutionOnboardingRequest,
    ) -> Department | None:
        if not dept_id:
            return None
        if "department" in req.__dict__ and req.__dict__["department"] is not None:
            return req.__dict__["department"]
        return await self._session.get(Department, dept_id)

    async def _safe_get_municipality(
        self,
        muni_id: uuid.UUID | None,
        req: InstitutionOnboardingRequest,
    ) -> Municipality | None:
        if not muni_id:
            return None
        if "municipality" in req.__dict__ and req.__dict__["municipality"] is not None:
            return req.__dict__["municipality"]
        return await self._session.get(Municipality, muni_id)

    async def _safe_get_catalog(
        self,
        cat_id: uuid.UUID | None,
        req: InstitutionOnboardingRequest,
    ) -> OfficialInstitutionCatalog | None:
        if not cat_id:
            return None
        if "catalog_institution" in req.__dict__ and req.__dict__["catalog_institution"] is not None:
            return req.__dict__["catalog_institution"]
        return await self._session.get(OfficialInstitutionCatalog, cat_id)

    async def _build_detail_response(
        self,
        req: InstitutionOnboardingRequest,
        catalog_record: OfficialInstitutionCatalog | None = None,
    ) -> OnboardingRequestDetailResponse:
        """Serialize an InstitutionOnboardingRequest into full detail schema."""
        catalog_obj = catalog_record or await self._safe_get_catalog(req.catalog_institution_id, req)
        dept_obj = await self._safe_get_department(req.department_id, req)
        muni_obj = await self._safe_get_municipality(req.municipality_id, req)

        requested_by = await self._safe_get_user(req.requested_by_id, "requested_by", req)
        reviewed_by = await self._safe_get_user(req.reviewed_by_id, "reviewed_by", req)
        approved_by = await self._safe_get_user(req.approved_by_id, "approved_by", req)
        rejected_by = await self._safe_get_user(req.rejected_by_id, "rejected_by", req)
        cancelled_by = await self._safe_get_user(req.cancelled_by_id, "cancelled_by", req)
        provisioned_by = await self._safe_get_user(req.provisioned_by_id, "provisioned_by", req)

        dept_name = dept_obj.name if dept_obj else None
        dept_code = dept_obj.code if dept_obj else None
        muni_name = muni_obj.name if muni_obj else None
        muni_code = muni_obj.code if muni_obj else None

        req_user_name = requested_by.full_name if requested_by else None
        req_user_email = requested_by.email if requested_by else None

        reviewed_name = reviewed_by.full_name if reviewed_by else None
        approved_name = approved_by.full_name if approved_by else None
        rejected_name = rejected_by.full_name if rejected_by else None
        cancelled_name = cancelled_by.full_name if cancelled_by else None
        provisioned_name = provisioned_by.full_name if provisioned_by else None

        now = datetime.now(UTC)
        created_val = req.__dict__.get("created_at") or now
        updated_val = req.__dict__.get("updated_at") or now

        return OnboardingRequestDetailResponse(
            id=req.__dict__.get("id", req.id),
            request_number=req.__dict__.get("request_number", req.request_number),
            catalog_institution_id=req.__dict__.get("catalog_institution_id", req.catalog_institution_id),
            dane_code=req.__dict__.get("dane_code", req.dane_code),
            institution_name=catalog_obj.name if catalog_obj else str(req.__dict__.get("dane_code", req.dane_code)),
            department_id=req.__dict__.get("department_id", req.department_id),
            department_name=dept_name,
            department_code=dept_code,
            municipality_id=req.__dict__.get("municipality_id", req.municipality_id),
            municipality_name=muni_name,
            municipality_code=muni_code,
            requested_by_id=req.__dict__.get("requested_by_id", req.requested_by_id),
            requester_name=req_user_name,
            requester_email=req_user_email,
            requester_role=req.__dict__.get("requester_role", req.requester_role),
            status=req.__dict__.get("status", req.status),
            institution_id=req.__dict__.get("institution_id"),
            contact_email=req.__dict__.get("contact_email", req.contact_email),
            contact_phone=req.__dict__.get("contact_phone"),
            proposed_rector_name=req.__dict__.get("proposed_rector_name"),
            proposed_rector_email=req.__dict__.get("proposed_rector_email"),
            proposed_rector_doc_type=req.__dict__.get("proposed_rector_doc_type"),
            proposed_rector_doc_num=req.__dict__.get("proposed_rector_doc_num"),
            justification=req.__dict__.get("justification"),
            reviewed_by_id=req.__dict__.get("reviewed_by_id"),
            reviewed_by_name=reviewed_name,
            reviewed_at=req.__dict__.get("reviewed_at"),
            review_notes=req.__dict__.get("review_notes"),
            approved_by_id=req.__dict__.get("approved_by_id"),
            approved_by_name=approved_name,
            approved_at=req.__dict__.get("approved_at"),
            rejected_by_id=req.__dict__.get("rejected_by_id"),
            rejected_by_name=rejected_name,
            rejected_at=req.__dict__.get("rejected_at"),
            rejection_reason=req.__dict__.get("rejection_reason"),
            cancelled_by_id=req.__dict__.get("cancelled_by_id"),
            cancelled_by_name=cancelled_name,
            cancelled_at=req.__dict__.get("cancelled_at"),
            cancellation_reason=req.__dict__.get("cancellation_reason"),
            provisioned_by_id=req.__dict__.get("provisioned_by_id"),
            provisioned_by_name=provisioned_name,
            provisioned_at=req.__dict__.get("provisioned_at"),
            lock_version=req.__dict__.get("lock_version", 0),
            idempotency_key=req.__dict__.get("idempotency_key"),
            created_at=created_val,
            updated_at=updated_val,
        )

