"""
PEVN Backend — Official DANE / MEN Educational Catalog Domain Models

Maintains the authoritative Colombian government educational registry cache
derived from DANE (DIREDU / Educación Formal) and MinEducación (DUE / SIMAT).

Distinguishes:
  - Official Educational Institution / Establishment (Establecimiento Educativo - 12-digit DANE)
  - Official Educational Sites / Campuses (Sedes Educativas: Sede Principal + Sedes Adscritas)
  - Official Catalog Synchronization Batches & Metrics (Audit tracking)
  - Complete data provenance (source system, dataset identifier, synchronization timestamp)
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class OfficialCatalogSyncBatch(Base):
    """
    Tracks and audits every national DANE/MEN educational catalog synchronization run.
    Records provenance, batch metrics, duration, error summaries, and status.
    """

    __tablename__ = "official_catalog_sync_batches"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    source_system: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="MINISTERIO DE EDUCACION NACIONAL (DUE) / DANE",
        doc="Authoritative government source system name.",
    )
    source_dataset: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="datos.gov.co/c36d-tcj8",
        doc="Official dataset identifier.",
    )
    source_version: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Dataset version/period label (e.g. 2026-Q1).",
    )
    source_published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Date when government published the source dataset.",
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="RUNNING",  # SUCCESS, FAILED, ROLLED_BACK
        index=True,
    )
    total_records: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    valid_records: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    rejected_records: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    duplicate_records: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    institutions_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    campuses_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    departments_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    municipalities_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    principal_campuses_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    annex_campuses_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    dataset_checksum: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        doc="SHA-256 checksum of the ingested source payload.",
    )
    quality_gate_status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        default="PASSED",
        doc="Overall Quality Gates status (e.g. PASSED, FAILED_GATE_A, etc.).",
    )
    failed_chunks: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    total_chunks: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    processed_chunks: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    ingestion_progress: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=100.0,
    )
    audit_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="VERIFIED",
    )
    error_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Detailed summary of validation errors or failure reasons.",
    )

    chunks: Mapped[list[OfficialCatalogSyncChunk]] = relationship(
        "OfficialCatalogSyncChunk",
        back_populates="batch",
        cascade="all, delete-orphan",
        order_by="OfficialCatalogSyncChunk.chunk_number",
    )

    def __repr__(self) -> str:
        return f"<OfficialCatalogSyncBatch id={self.id} status={self.status} total={self.total_records}>"


class OfficialCatalogSyncChunk(Base):
    """
    Tracks execution and quality metrics for individual chunks within an ingestion batch.
    Enables deterministic chunk-level retries, rollback, and progress monitoring.
    """

    __tablename__ = "official_catalog_sync_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    batch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("official_catalog_sync_batches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="PENDING",  # PENDING, RUNNING, SUCCESS, FAILED, ROLLED_BACK
        index=True,
    )
    total_records: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    valid_records: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    inserted_records: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_records: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rejected_records: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duplicate_records: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_details: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    batch: Mapped[OfficialCatalogSyncBatch] = relationship(
        "OfficialCatalogSyncBatch",
        back_populates="chunks",
    )

    def __repr__(self) -> str:
        return f"<OfficialCatalogSyncChunk batch={self.batch_id} chunk={self.chunk_number} status={self.status}>"


class OfficialInstitutionCatalog(Base):
    """
    Authoritative Colombian Educational Establishment Catalog Record.
    Derived from MinEducación DUE (Directorio Único de Establecimientos) and DANE DIREDU.
    """

    __tablename__ = "official_institution_catalog"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    dane_code: Mapped[str] = mapped_column(
        String(12),
        unique=True,
        nullable=False,
        index=True,
        doc="Authoritative 12-digit DANE institutional code.",
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        doc="Official registered institution name.",
    )
    department_code: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        index=True,
        doc="DANE 2-digit department code.",
    )
    department_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Department name.",
    )
    municipality_code: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        index=True,
        doc="DANE 5-digit municipality code.",
    )
    municipality_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Municipality name.",
    )
    secretaria_code: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Certified Territorial Entity (ETC) code.",
    )
    secretaria_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
        doc="Secretaría de Educación authority name.",
    )
    sector: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="OFICIAL",
        doc="OFICIAL (Public) or NO OFICIAL (Private).",
    )
    zone: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="URBANA",
        doc="URBANA or RURAL.",
    )
    calendar: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="A",
        doc="Academic calendar (A, B, or CONTINUO).",
    )
    academic_character: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="ACADÉMICO",
        doc="ACADÉMICO, TÉCNICO, or NORMALISTA.",
    )
    official_address: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Official address registered in DUE.",
    )
    official_phone: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Official contact telephone registered in DUE.",
    )
    official_email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Official institutional email in DUE (if available).",
    )
    educational_levels: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        default="PREESCOLAR,PRIMARIA,SECUNDARIA,MEDIA",
        doc="Comma-separated educational levels offered.",
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="ACTIVO",
        doc="ACTIVO, CIERRE TEMPORAL, or CIERRE DEFINITIVO.",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether this establishment is currently active.",
    )

    # Provenance Tracking
    source_system: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="MEN_DUE / DANE DIREDU",
        doc="Authoritative government source system name.",
    )
    source_dataset: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="datos.gov.co/c36d-tcj8",
        doc="Official dataset identifier.",
    )
    source_record_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Original record ID in government dataset.",
    )
    source_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Date when government published/updated the record.",
    )
    synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp when PEvN ingested/synchronized this record.",
    )
    sync_batch_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("official_catalog_sync_batches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Reference to the batch run that synchronized this record.",
    )

    # Relationships
    campuses: Mapped[list[OfficialCampusCatalog]] = relationship(
        "OfficialCampusCatalog",
        back_populates="institution",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<OfficialInstitutionCatalog dane={self.dane_code!r} name={self.name!r}>"


class OfficialCampusCatalog(Base):
    """
    Authoritative Colombian Educational Site / Campus (Sede Educativa) Record.
    Belongs to an Official Institution Establishment.
    """

    __tablename__ = "official_campus_catalog"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    official_institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("official_institution_catalog.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Parent official establishment foreign key.",
    )
    dane_sede_code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
        doc="Official DANE 12-digit sede code.",
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Campus name (e.g. Sede Principal, Sede B).",
    )
    is_main: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether this is the principal campus (Sede Principal).",
    )
    zone: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        default="URBANA",
        doc="URBANA or RURAL.",
    )
    address: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Physical address of the campus.",
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="ACTIVA",
        doc="ACTIVA or INACTIVA.",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether the campus is currently operational.",
    )

    # Relationships
    institution: Mapped[OfficialInstitutionCatalog] = relationship(
        "OfficialInstitutionCatalog",
        back_populates="campuses",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<OfficialCampusCatalog dane_sede={self.dane_sede_code!r} name={self.name!r}>"


class OfficialCatalogPromotionAuthorization(Base):
    """
    Immutable record of an explicit Promotion Authorization decision by a privileged administrator.
    """

    __tablename__ = "official_catalog_promotion_authorizations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    actor_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    actor_email: Mapped[str] = mapped_column(String(255), nullable=False)
    actor_role: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="GRANTED")
    catalog_status_before: Mapped[str] = mapped_column(String(50), nullable=False)
    catalog_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    preflight_certification_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    plan_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    snapshot_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    decision: Mapped[str] = mapped_column(String(20), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    consumed_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    snapshots: Mapped[list[OfficialCatalogPromotionSnapshot]] = relationship(
        "OfficialCatalogPromotionSnapshot",
        back_populates="authorization",
    )


class OfficialCatalogPromotionSnapshot(Base):
    """
    Immutable checkpoint snapshot of the official catalog prior to promotion.
    """

    __tablename__ = "official_catalog_promotion_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    authorization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("official_catalog_promotion_authorizations.id", ondelete="SET NULL"),
        nullable=True,
    )
    snapshot_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    catalog_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    institutions_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    campuses_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    principal_campuses_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    annex_campuses_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    departments_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    municipalities_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    metadata_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    authorization: Mapped[OfficialCatalogPromotionAuthorization | None] = relationship(
        "OfficialCatalogPromotionAuthorization",
        back_populates="snapshots",
    )


class OfficialCatalogPromotionEvent(Base):
    """
    Immutable audit log of all promotion lifecycle actions and state transitions.
    """

    __tablename__ = "official_catalog_promotion_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    correlation_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    actor_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    state_before: Mapped[str] = mapped_column(String(50), nullable=False)
    state_after: Mapped[str] = mapped_column(String(50), nullable=False)
    catalog_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    result: Mapped[str] = mapped_column(String(30), nullable=False)
    details_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class OfficialCatalogPromotionLock(Base):
    """
    Database-backed distributed lock table to prevent concurrent promotions across worker nodes.
    """

    __tablename__ = "official_catalog_promotion_locks"

    lock_key: Mapped[str] = mapped_column(String(50), primary_key=True)
    acquired_by: Mapped[str] = mapped_column(String(100), nullable=False)
    correlation_id: Mapped[str] = mapped_column(String(100), nullable=False)
    acquired_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

