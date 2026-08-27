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
    ConflictError,
    NotFoundError,
    UnprocessableEntityError,
)
from app.models.institution import Campus, Institution
from app.models.official_catalog import (
    OfficialCampusCatalog,
    OfficialInstitutionCatalog,
)
from app.models.territory import Department, Municipality
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
        return result

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
