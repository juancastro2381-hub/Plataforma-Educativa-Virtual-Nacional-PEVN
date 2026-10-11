"""
PEVN Backend — Educational Institution Domain Service

Handles institutional provisioning, 12-digit DANE catalog validation,
authoritative government identity resolution (MEN DUE / DANE DIREDU),
automatic main campus and attached campuses initialization, lifecycle state
management, and administrative national queries with full audit logging.
"""

from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.audit.interfaces import AuditEvent, AuditEventType
from app.audit.service import audit_service
from app.core.logging import get_logger
from app.exceptions.errors import (
    AuthorizationError,
    ConflictError,
    NotFoundError,
    UnprocessableEntityError,
)
from app.core.security.interfaces import AuthorizationContext, SystemRole
from app.models.institution import Campus, Institution
from app.models.official_catalog import (
    OfficialCampusCatalog,
    OfficialInstitutionCatalog,
)
from app.models.territory import Department, Municipality
from app.schemas.institution import (
    OfficialCatalogItemResponse,
    OfficialCatalogListResponse,
    OfficialCatalogSummary,
)
from app.schemas.official_catalog import (
    OfficialCampusResponse,
    OfficialInstitutionResolutionResponse,
    OfficialProvenanceSchema,
)

_logger = get_logger(__name__)


class InstitutionService:
    """
    Service responsible for institutional provisioning, authoritative DANE resolution,
    and tenant lifecycle.
    """

    def __init__(
        self,
        session: AsyncSession,
        audit_svc: audit_service.__class__ = audit_service,
    ) -> None:
        self._session = session
        self._audit = audit_svc

    async def seed_official_catalog_if_empty(self) -> int:
        """
        Seed official Colombian government educational catalog records if table is empty
        using the OfficialCatalogSyncService validation pipeline.
        """
        stmt = select(func.count()).select_from(OfficialInstitutionCatalog)
        count = (await self._session.execute(stmt)).scalar_one()
        if count > 0:
            return count

        from app.db.seeds.official_dane_catalog import OFFICIAL_COLOMBIAN_INSTITUTIONS_DATASET
        from app.services.official_catalog_sync_service import OfficialCatalogSyncService

        sync_service = OfficialCatalogSyncService(self._session)
        stats = await sync_service.ingest_official_records(OFFICIAL_COLOMBIAN_INSTITUTIONS_DATASET)
        return stats.total_institutions_synced

    async def resolve_official_dane(
        self,
        dane_code: str,
        *,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",
        correlation_id: str | None = None,
    ) -> OfficialInstitutionResolutionResponse:
        """
        Resolve authoritative Colombian educational establishment from the official catalog.

        Validations:
          1. DANE code must be exactly 12 numeric digits.
          2. Must exist in the official government catalog.
        """
        cleaned_dane = dane_code.strip()
        if not (cleaned_dane.isdigit() and len(cleaned_dane) == 12):
            raise UnprocessableEntityError(
                "El código DANE institucional debe contener exactamente 12 dígitos numéricos.",
                code="INVALID_DANE_CODE",
            )

        # Ensure official catalog seed exists
        await self.seed_official_catalog_if_empty()

        stmt = (
            select(OfficialInstitutionCatalog)
            .where(OfficialInstitutionCatalog.dane_code == cleaned_dane)
            .options(selectinload(OfficialInstitutionCatalog.campuses))
        )
        catalog_record = (await self._session.execute(stmt)).scalar_one_or_none()
        if not catalog_record:
            raise NotFoundError(
                "No encontramos un registro oficial asociado a este Código DANE en el catálogo nacional.",
                code="OFFICIAL_DANE_RECORD_NOT_FOUND",
            )

        # Audit resolution access
        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.OFFICIAL_DANE_RESOLVED,
                actor_id=str(actor_id) if actor_id else None,
                actor_ip=actor_ip,
                target_id=str(catalog_record.id),
                target_type="OfficialInstitutionCatalog",
                correlation_id=correlation_id,
                metadata={
                    "dane_code": cleaned_dane,
                    "name": catalog_record.name,
                    "source_dataset": catalog_record.source_dataset,
                },
            ),
            session=self._session,
        )

        pevn_required: list[str] = []
        if not catalog_record.official_email:
            pevn_required.append("email")

        campuses_resp = [
            OfficialCampusResponse(
                dane_sede_code=c.dane_sede_code,
                name=c.name,
                is_main=c.is_main,
                zone=c.zone,
                address=c.address,
                status=c.status,
                is_active=c.is_active,
            )
            for c in catalog_record.campuses
        ]

        levels = [
            lvl.strip()
            for lvl in (catalog_record.educational_levels or "").split(",")
            if lvl.strip()
        ]

        return OfficialInstitutionResolutionResponse(
            dane_code=catalog_record.dane_code,
            name=catalog_record.name,
            department_code=catalog_record.department_code,
            department_name=catalog_record.department_name,
            municipality_code=catalog_record.municipality_code,
            municipality_name=catalog_record.municipality_name,
            secretaria_code=catalog_record.secretaria_code,
            secretaria_name=catalog_record.secretaria_name,
            sector=catalog_record.sector,
            zone=catalog_record.zone,
            calendar=catalog_record.calendar,
            academic_character=catalog_record.academic_character,
            official_address=catalog_record.official_address,
            official_phone=catalog_record.official_phone,
            official_email=catalog_record.official_email,
            educational_levels=levels,
            status=catalog_record.status,
            is_active=catalog_record.is_active,
            campuses=campuses_resp,
            provenance=OfficialProvenanceSchema(
                source_system=catalog_record.source_system,
                source_dataset=catalog_record.source_dataset,
                source_record_id=catalog_record.source_record_id,
                source_updated_at=catalog_record.source_updated_at,
                synced_at=catalog_record.synced_at,
            ),
            pevn_required_fields=pevn_required,
        )

    async def provision_institution(
        self,
        *,
        dane_code: str,
        name: str,
        email: str,
        municipality_id: uuid.UUID | str,
        phone: str | None = None,
        address: str | None = None,
        main_campus_name: str = "Sede Principal",
        main_campus_dane: str | None = None,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",  # noqa: S104
        correlation_id: str | None = None,
    ) -> Institution:
        """
        Provision a new Educational Institution and its Principal Campus (and attached campuses if found in catalog).

        Validations:
          1. DANE code must be exactly 12 numeric digits.
          2. DANE code must be globally unique across institutions.
          3. Municipality must exist in or authoritatively resolve to the national territory catalog.
        """
        cleaned_dane = dane_code.strip()
        if not (cleaned_dane.isdigit() and len(cleaned_dane) == 12):
            raise UnprocessableEntityError(
                "El código DANE institucional debe contener exactamente 12 dígitos numéricos.",
                code="INVALID_DANE_CODE",
            )

        # Uniqueness check for DANE code
        dane_check = await self._session.execute(
            select(Institution).where(Institution.dane_code == cleaned_dane)
        )
        if dane_check.scalar_one_or_none():
            raise ConflictError(
                f"El código DANE institucional {cleaned_dane} ya se encuentra registrado.",
                code="DUPLICATE_DANE_CODE",
            )

        # Municipality resolution (UUID or 5-digit DANE DIVIPOLA code)
        target_municipality: Municipality | None = None

        if isinstance(municipality_id, uuid.UUID):
            muni_stmt = select(Municipality).where(Municipality.id == municipality_id)
            target_municipality = (await self._session.execute(muni_stmt)).scalar_one_or_none()
        else:
            raw_str = str(municipality_id).strip()
            try:
                parsed_uuid = uuid.UUID(raw_str)
                muni_stmt = select(Municipality).where(Municipality.id == parsed_uuid)
                target_municipality = (await self._session.execute(muni_stmt)).scalar_one_or_none()
            except ValueError:
                muni_stmt = select(Municipality).where(Municipality.code == raw_str)
                target_municipality = (await self._session.execute(muni_stmt)).scalar_one_or_none()

                if not target_municipality:
                    # Authoritative resolution from OfficialInstitutionCatalog
                    cat_stmt = select(OfficialInstitutionCatalog).where(
                        OfficialInstitutionCatalog.municipality_code == raw_str
                    ).limit(1)
                    cat_record = (await self._session.execute(cat_stmt)).scalar_one_or_none()
                    if cat_record:
                        dept_stmt = select(Department).where(Department.code == cat_record.department_code)
                        dept = (await self._session.execute(dept_stmt)).scalar_one_or_none()
                        if not dept:
                            dept = Department(code=cat_record.department_code, name=cat_record.department_name)
                            self._session.add(dept)
                            await self._session.flush()

                        target_municipality = Municipality(
                            department_id=dept.id,
                            code=cat_record.municipality_code,
                            name=cat_record.municipality_name,
                        )
                        self._session.add(target_municipality)
                        await self._session.flush()

        if not target_municipality:
            raise NotFoundError(
                "El municipio especificado no existe en el catálogo territorial.",
                code="MUNICIPALITY_NOT_FOUND",
            )

        # Check official catalog record for provenance
        await self.seed_official_catalog_if_empty()
        catalog_stmt = (
            select(OfficialInstitutionCatalog)
            .where(OfficialInstitutionCatalog.dane_code == cleaned_dane)
            .options(selectinload(OfficialInstitutionCatalog.campuses))
        )
        catalog_record = (await self._session.execute(catalog_stmt)).scalar_one_or_none()

        # 1. Create Institution (strictly using target_municipality.id UUID)
        institution = Institution(
            municipality_id=target_municipality.id,
            dane_code=cleaned_dane,
            name=name.strip(),
            email=email.strip().lower(),
            phone=phone.strip() if phone else None,
            address=address.strip() if address else None,
            is_active=True,
            catalog_institution_id=catalog_record.id if catalog_record else None,
        )
        self._session.add(institution)
        await self._session.flush()

        # 2. Campuses provisioning
        created_campuses: list[Campus] = []
        if catalog_record and catalog_record.campuses:
            # Create campuses from official catalog
            for official_c in catalog_record.campuses:
                campus = Campus(
                    institution_id=institution.id,
                    dane_sede_code=official_c.dane_sede_code,
                    name=official_c.name,
                    address=official_c.address or (address.strip() if address else None),
                    is_active=official_c.is_active,
                )
                self._session.add(campus)
                created_campuses.append(campus)
            await self._session.flush()
        else:
            # Fallback / manual Sede Principal creation
            sede_dane = main_campus_dane.strip() if main_campus_dane else f"{cleaned_dane}01"
            main_campus = Campus(
                institution_id=institution.id,
                dane_sede_code=sede_dane,
                name=main_campus_name.strip(),
                address=address.strip() if address else None,
                is_active=True,
            )
            self._session.add(main_campus)
            created_campuses.append(main_campus)
            await self._session.flush()

        # 3. Record Audit Trail
        audit_event_type = (
            AuditEventType.INSTITUTION_PROVISIONED_FROM_CATALOG
            if catalog_record
            else AuditEventType.INSTITUTION_CREATED
        )
        audit_metadata = {
            "dane_code": cleaned_dane,
            "name": institution.name,
            "municipality_id": str(municipality_id),
            "campuses_count": len(created_campuses),
            "from_official_catalog": catalog_record is not None,
        }
        if catalog_record:
            audit_metadata["source_system"] = catalog_record.source_system
            audit_metadata["source_dataset"] = catalog_record.source_dataset
            audit_metadata["catalog_id"] = str(catalog_record.id)

        await self._audit.record(
            AuditEvent(
                event_type=audit_event_type,
                actor_id=str(actor_id) if actor_id else None,
                actor_ip=actor_ip,
                target_id=str(institution.id),
                target_type="Institution",
                institution_id=str(institution.id),
                correlation_id=correlation_id,
                metadata=audit_metadata,
            ),
            session=self._session,
        )

        # Refresh with campuses loaded
        result = await self._session.execute(
            select(Institution)
            .where(Institution.id == institution.id)
            .options(selectinload(Institution.campuses), selectinload(Institution.municipality))
        )
        return result.scalar_one()

    async def get_institution_by_id(
        self,
        *,
        institution_id: uuid.UUID,
    ) -> Institution:
        """
        Retrieve an institution by ID with campuses loaded.
        """
        stmt = (
            select(Institution)
            .where(Institution.id == institution_id)
            .options(selectinload(Institution.campuses), selectinload(Institution.municipality))
        )
        result = (await self._session.execute(stmt)).scalar_one_or_none()
        if not result:
            raise NotFoundError(
                "La institución especificada no existe.",
                code="INSTITUTION_NOT_FOUND",
            )
        await self._enrich_rector_status([result])
        return result

    async def get_institution_by_dane(
        self,
        *,
        dane_code: str,
    ) -> Institution:
        """
        Retrieve an institution by its 12-digit DANE code.
        """
        cleaned_dane = dane_code.strip()
        stmt = (
            select(Institution)
            .where(Institution.dane_code == cleaned_dane)
            .options(selectinload(Institution.campuses), selectinload(Institution.municipality))
        )
        result = (await self._session.execute(stmt)).scalar_one_or_none()
        if not result:
            raise NotFoundError(
                f"No se encontró una institución con el código DANE {cleaned_dane}.",
                code="INSTITUTION_NOT_FOUND",
            )
        await self._enrich_rector_status([result])
        return result

    async def _enrich_rector_status(self, institutions: Sequence[Institution]) -> None:
        """Enrich institution domain objects with active rector and pending invitation states."""
        if not institutions:
            return

        inst_ids = [inst.id for inst in institutions]
        from app.models.role import Role, UserRole
        from app.models.user import User
        from app.models.invitation import RectorInvitation

        rector_role_stmt = select(Role.id).where(Role.name == "rector")
        rector_role_id = (await self._session.execute(rector_role_stmt)).scalar_one_or_none()

        rector_map: dict[uuid.UUID, User] = {}
        if rector_role_id:
            rector_stmt = (
                select(UserRole.institution_id, User)
                .join(User, UserRole.user_id == User.id)
                .where(
                    UserRole.institution_id.in_(inst_ids),
                    UserRole.role_id == rector_role_id,
                    UserRole.is_active == True,
                    User.is_active == True,
                )
            )
            rector_rows = (await self._session.execute(rector_stmt)).all()
            for inst_id, u in rector_rows:
                if inst_id:
                    rector_map[inst_id] = u

        inv_stmt = (
            select(RectorInvitation.institution_id)
            .where(
                RectorInvitation.institution_id.in_(inst_ids),
                RectorInvitation.is_used == False,
                RectorInvitation.is_revoked == False,
                RectorInvitation.expires_at > func.now(),
            )
        )
        pending_inv_rows = (await self._session.execute(inv_stmt)).scalars().all()
        pending_set = set(pending_inv_rows)

        for inst in institutions:
            active_u = rector_map.get(inst.id)
            if active_u:
                setattr(inst, "has_active_rector", True)
                setattr(inst, "active_rector_name", f"{active_u.first_name} {active_u.last_name}".strip())
                setattr(inst, "active_rector_email", active_u.email)
                setattr(inst, "has_pending_invitation", False)
            else:
                setattr(inst, "has_active_rector", False)
                setattr(inst, "active_rector_name", None)
                setattr(inst, "active_rector_email", None)
                setattr(inst, "has_pending_invitation", inst.id in pending_set)

    async def list_institutions(
        self,
        *,
        search: str | None = None,
        is_active: bool | None = None,
        department_id: uuid.UUID | None = None,
        municipality_id: uuid.UUID | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[Institution], int]:
        """
        List institutions with filtering and pagination.
        """
        query = select(Institution).options(
            selectinload(Institution.campuses),
            selectinload(Institution.municipality),
        )
        count_query = select(func.count()).select_from(Institution)

        if search:
            search_term = f"%{search.strip()}%"
            filter_clause = (Institution.name.ilike(search_term)) | (
                Institution.dane_code.ilike(search_term)
            )
            query = query.where(filter_clause)
            count_query = count_query.where(filter_clause)

        if is_active is not None:
            query = query.where(Institution.is_active == is_active)
            count_query = count_query.where(Institution.is_active == is_active)

        if municipality_id is not None:
            query = query.where(Institution.municipality_id == municipality_id)
            count_query = count_query.where(Institution.municipality_id == municipality_id)
        elif department_id is not None:
            query = query.join(Municipality).where(Municipality.department_id == department_id)
            count_query = count_query.join(Municipality).where(
                Municipality.department_id == department_id
            )

        total = (await self._session.execute(count_query)).scalar_one()

        offset = (page - 1) * page_size
        query = query.order_by(Institution.name.asc()).offset(offset).limit(page_size)
        institutions = (await self._session.execute(query)).scalars().all()
        await self._enrich_rector_status(institutions)

        return institutions, total

    async def update_institution_status(
        self,
        *,
        institution_id: uuid.UUID,
        is_active: bool,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",  # noqa: S104
        correlation_id: str | None = None,
    ) -> Institution:
        """
        Activate or suspend an institution's operational status.
        """
        institution = await self.get_institution_by_id(institution_id=institution_id)
        previous_status = institution.is_active
        institution.is_active = is_active
        await self._session.flush()

        event_type = (
            AuditEventType.INSTITUTION_UPDATED
            if is_active
            else AuditEventType.INSTITUTION_DEACTIVATED
        )
        await self._audit.record(
            AuditEvent(
                event_type=event_type,
                actor_id=str(actor_id) if actor_id else None,
                actor_ip=actor_ip,
                target_id=str(institution.id),
                target_type="Institution",
                institution_id=str(institution.id),
                correlation_id=correlation_id,
                metadata={
                    "dane_code": institution.dane_code,
                    "previous_status": previous_status,
                    "new_status": is_active,
                },
            ),
            session=self._session,
        )

        result = await self._session.execute(
            select(Institution)
            .where(Institution.id == institution.id)
            .options(selectinload(Institution.campuses), selectinload(Institution.municipality))
        )
        return result.scalar_one()

    async def update_coordinator_delegation_setting(
        self,
        *,
        institution_id: uuid.UUID,
        enabled: bool,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",  # noqa: S104
        correlation_id: str | None = None,
    ) -> Institution:
        """
        Update the Coordinator operational delegation setting for an institution.
        Enforces persistence and records full audit trail with previous and new values.
        """
        institution = await self.get_institution_by_id(institution_id=institution_id)
        previous_value = institution.coordinator_delegation_enabled
        institution.coordinator_delegation_enabled = enabled
        await self._session.flush()

        await self._audit.record(
            AuditEvent(
                event_type=AuditEventType.COORDINATOR_DELEGATION_SETTING_UPDATED,
                actor_id=str(actor_id) if actor_id else None,
                actor_ip=actor_ip,
                target_id=str(institution.id),
                target_type="Institution",
                institution_id=str(institution.id),
                correlation_id=correlation_id,
                metadata={
                    "dane_code": institution.dane_code,
                    "previous_value": previous_value,
                    "new_value": enabled,
                    "outcome": "success",
                },
            ),
            session=self._session,
        )

        result = await self._session.execute(
            select(Institution)
            .where(Institution.id == institution.id)
            .options(selectinload(Institution.campuses), selectinload(Institution.municipality))
        )
        return result.scalar_one()

    async def list_official_catalog_with_status(
        self,
        *,
        department_code: str | None = None,
        municipality_code: str | None = None,
        search: str | None = None,
        status_filter: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> OfficialCatalogListResponse:
        """
        List official catalog establishments enriched with real-time PEVN tenant and Rector status.
        Supports discovery within authorized territorial scopes (e.g. municipal, departmental, national).
        """
        await self.seed_official_catalog_if_empty()

        cat_query = select(OfficialInstitutionCatalog).options(
            selectinload(OfficialInstitutionCatalog.campuses)
        )
        if department_code:
            cat_query = cat_query.where(OfficialInstitutionCatalog.department_code == department_code)
        if municipality_code:
            cat_query = cat_query.where(OfficialInstitutionCatalog.municipality_code == municipality_code)
        if search:
            search_term = f"%{search.strip()}%"
            cat_query = cat_query.where(
                (OfficialInstitutionCatalog.name.ilike(search_term))
                | (OfficialInstitutionCatalog.dane_code.ilike(search_term))
            )

        cat_records = (
            await self._session.execute(cat_query.order_by(OfficialInstitutionCatalog.name.asc()))
        ).scalars().all()

        # Query all operational institutions in this territorial scope
        inst_query = select(Institution).options(
            selectinload(Institution.campuses),
            selectinload(Institution.municipality),
        )
        if municipality_code:
            inst_query = inst_query.join(Municipality).where(Municipality.code == municipality_code)
        elif department_code:
            inst_query = inst_query.join(Municipality).join(Department).where(Department.code == department_code)

        inst_rows = (await self._session.execute(inst_query)).scalars().all()
        if inst_rows:
            await self._enrich_rector_status(inst_rows)

        tenants_by_dane = {i.dane_code: i for i in inst_rows}
        tenants_by_cat_id = {i.catalog_institution_id: i for i in inst_rows if i.catalog_institution_id}

        items: list[OfficialCatalogItemResponse] = []
        summary = OfficialCatalogSummary(
            total_catalog=len(cat_records),
            available=0,
            provisioned=0,
            sin_rector=0,
            pending_invite=0,
            active_rector=0,
            inactiva=0,
        )

        for cat in cat_records:
            tenant = tenants_by_cat_id.get(cat.id) or tenants_by_dane.get(cat.dane_code)
            if not tenant:
                is_prov = False
                tenant_id = None
                has_rector = False
                rector_name = None
                rector_email = None
                has_pending = False
                if not cat.is_active or cat.status != "ACTIVO":
                    lifecycle_status = "INACTIVA"
                    summary.inactiva += 1
                else:
                    lifecycle_status = "DISPONIBLE_PARA_APROVISIONAR"
                    summary.available += 1
            else:
                is_prov = True
                tenant_id = tenant.id
                summary.provisioned += 1
                has_rector = getattr(tenant, "has_active_rector", False)
                rector_name = getattr(tenant, "active_rector_name", None)
                rector_email = getattr(tenant, "active_rector_email", None)
                has_pending = getattr(tenant, "has_pending_invitation", False)

                if not tenant.is_active:
                    lifecycle_status = "INACTIVA"
                    summary.inactiva += 1
                elif has_rector:
                    lifecycle_status = "RECTOR_ACTIVO"
                    summary.active_rector += 1
                elif has_pending:
                    lifecycle_status = "INVITACION_RECTOR_PENDIENTE"
                    summary.pending_invite += 1
                else:
                    lifecycle_status = "APROVISIONADA_SIN_RECTOR"
                    summary.sin_rector += 1

            if status_filter:
                norm_sf = status_filter.upper().strip()
                if norm_sf in {"DISPONIBLE", "AVAILABLE", "DISPONIBLE_PARA_APROVISIONAR"} and lifecycle_status != "DISPONIBLE_PARA_APROVISIONAR":
                    continue
                if norm_sf in {"APROVISIONADA", "PROVISIONED"} and not is_prov:
                    continue
                if norm_sf in {"SIN_RECTOR", "APROVISIONADA_SIN_RECTOR"} and lifecycle_status != "APROVISIONADA_SIN_RECTOR":
                    continue
                if norm_sf in {"PENDIENTE", "PENDING", "INVITACION_RECTOR_PENDIENTE"} and lifecycle_status != "INVITACION_RECTOR_PENDIENTE":
                    continue
                if norm_sf in {"ACTIVO", "ACTIVE", "RECTOR_ACTIVO"} and lifecycle_status != "RECTOR_ACTIVO":
                    continue
                if norm_sf in {"INACTIVA", "INACTIVE"} and lifecycle_status != "INACTIVA":
                    continue

            items.append(
                OfficialCatalogItemResponse(
                    id=cat.id,
                    dane_code=cat.dane_code,
                    name=cat.name,
                    department_code=cat.department_code,
                    department_name=cat.department_name,
                    municipality_code=cat.municipality_code,
                    municipality_name=cat.municipality_name,
                    official_address=cat.official_address,
                    official_phone=cat.official_phone,
                    official_email=cat.official_email,
                    sector=cat.sector,
                    zone=cat.zone,
                    campus_count=len(cat.campuses) if cat.campuses else 1,
                    is_active=cat.is_active,
                    is_provisioned=is_prov,
                    institution_id=tenant_id,
                    lifecycle_status=lifecycle_status,
                    has_active_rector=has_rector,
                    active_rector_name=rector_name,
                    active_rector_email=rector_email,
                    has_pending_invitation=has_pending,
                )
            )

        total_filtered = len(items)
        offset = (page - 1) * page_size
        paginated_items = items[offset : offset + page_size]

        return OfficialCatalogListResponse(
            items=paginated_items,
            total=total_filtered,
            page=page,
            page_size=page_size,
            summary=summary,
        )

    async def provision_from_catalog(
        self,
        *,
        dane_code: str,
        auth_context: AuthorizationContext,
        actor_id: uuid.UUID | str | None = None,
        actor_ip: str = "0.0.0.0",
        correlation_id: str | None = None,
        contact_email: str | None = None,
        contact_phone: str | None = None,
    ) -> Institution:
        """
        Provision an official educational establishment from the government catalog into PEVN.
        Enforces strict territorial boundaries for Municipal and Department Administrators.
        """
        cleaned_dane = dane_code.strip()
        if not (cleaned_dane.isdigit() and len(cleaned_dane) == 12):
            raise UnprocessableEntityError(
                "El código DANE institucional debe contener exactamente 12 dígitos numéricos.",
                code="INVALID_DANE_CODE",
            )

        await self.seed_official_catalog_if_empty()
        cat_stmt = (
            select(OfficialInstitutionCatalog)
            .where(OfficialInstitutionCatalog.dane_code == cleaned_dane)
            .options(selectinload(OfficialInstitutionCatalog.campuses))
        )
        cat_record = (await self._session.execute(cat_stmt)).scalar_one_or_none()
        if not cat_record:
            raise NotFoundError(
                f"No se encontró el registro oficial {cleaned_dane} en el catálogo nacional.",
                code="OFFICIAL_DANE_RECORD_NOT_FOUND",
            )

        if not cat_record.is_active or cat_record.status != "ACTIVO":
            raise UnprocessableEntityError(
                f"El establecimiento oficial {cleaned_dane} ({cat_record.name}) no se encuentra activo para aprovisionamiento.",
                code="OFFICIAL_RECORD_INACTIVE",
            )

        # Territorial authorization boundary checks
        if auth_context.scope.is_municipality():
            actor_muni_uuid = uuid.UUID(auth_context.scope.municipality_id)
            muni_obj = (
                await self._session.execute(select(Municipality).where(Municipality.id == actor_muni_uuid))
            ).scalar_one_or_none()
            if not muni_obj or muni_obj.code != cat_record.municipality_code:
                raise AuthorizationError(
                    "No está autorizado para aprovisionar establecimientos educativos fuera de su jurisdicción municipal.",
                    code="PERMISSION_DENIED",
                )
        elif auth_context.scope.is_department():
            actor_dept_uuid = uuid.UUID(auth_context.scope.department_id)
            dept_obj = (
                await self._session.execute(select(Department).where(Department.id == actor_dept_uuid))
            ).scalar_one_or_none()
            if not dept_obj or dept_obj.code != cat_record.department_code:
                raise AuthorizationError(
                    "No está autorizado para aprovisionar establecimientos educativos fuera de su jurisdicción departamental.",
                    code="PERMISSION_DENIED",
                )
        elif not (
            auth_context.scope.is_national()
            or SystemRole.SUPERADMIN in auth_context.roles
            or SystemRole.NATIONAL_ADMIN in auth_context.roles
        ):
            raise AuthorizationError(
                "No posee facultades administrativas territoriales para aprovisionar establecimientos.",
                code="PERMISSION_DENIED",
            )

        # Anti-duplication check
        dup_stmt = select(Institution).where(
            (Institution.dane_code == cleaned_dane) | (Institution.catalog_institution_id == cat_record.id)
        )
        existing = (await self._session.execute(dup_stmt)).scalar_one_or_none()
        if existing:
            raise ConflictError(
                f"El establecimiento educativo con código DANE {cleaned_dane} ya se encuentra aprovisionado en PEVN.",
                code="DUPLICATE_DANE_CODE",
            )

        # Resolve or create municipality
        muni_stmt = select(Municipality).where(Municipality.code == cat_record.municipality_code)
        target_muni = (await self._session.execute(muni_stmt)).scalar_one_or_none()
        if not target_muni:
            dept_stmt = select(Department).where(Department.code == cat_record.department_code)
            target_dept = (await self._session.execute(dept_stmt)).scalar_one_or_none()
            if not target_dept:
                target_dept = Department(code=cat_record.department_code, name=cat_record.department_name)
                self._session.add(target_dept)
                await self._session.flush()
            target_muni = Municipality(
                department_id=target_dept.id,
                code=cat_record.municipality_code,
                name=cat_record.municipality_name,
            )
            self._session.add(target_muni)
            await self._session.flush()

        email = (contact_email or cat_record.official_email or f"contacto.{cleaned_dane}@colegio.edu.co").strip().lower()
        phone = contact_phone or cat_record.official_phone
        address = cat_record.official_address

        return await self.provision_institution(
            dane_code=cleaned_dane,
            name=cat_record.name,
            email=email,
            municipality_id=target_muni.id,
            phone=phone,
            address=address,
            actor_id=actor_id,
            actor_ip=actor_ip,
            correlation_id=correlation_id,
        )

