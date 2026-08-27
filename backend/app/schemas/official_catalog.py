"""
PEVN Backend — Official DANE / MEN Institutional Resolution Schemas

Defines request and response data contracts for authoritative government
data resolution, provenance tracking, and campus relationships.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class OfficialProvenanceSchema(BaseModel):
    """Data provenance tracking schema."""

    model_config = ConfigDict(from_attributes=True)

    source_system: str = Field(..., description="Authoritative government source name (e.g. MEN_DUE / DANE DIREDU)")
    source_dataset: str = Field(..., description="Official dataset identifier (e.g. datos.gov.co/c36d-tcj8)")
    source_record_id: str | None = Field(None, description="Original record ID in government dataset")
    source_updated_at: datetime | None = Field(None, description="Last date when government updated this record")
    synced_at: datetime = Field(..., description="Timestamp when PEvN catalog synced this record")


class OfficialCampusResponse(BaseModel):
    """Campus / Sede Educativa information resolved from official catalog."""

    model_config = ConfigDict(from_attributes=True)

    dane_sede_code: str = Field(..., description="Official 12-digit DANE sede code")
    name: str = Field(..., description="Official campus name (e.g. Sede Principal)")
    is_main: bool = Field(False, description="Whether this is the principal campus")
    zone: str | None = Field(None, description="URBANA or RURAL")
    address: str | None = Field(None, description="Physical address of the campus")
    status: str = Field("ACTIVA", description="Operating status (ACTIVA/INACTIVA)")
    is_active: bool = Field(True, description="Whether campus is operational")


class OfficialInstitutionResolutionResponse(BaseModel):
    """
    Authoritative institutional identity resolved from official government catalog.
    Strictly distinguishes official read-only data from PEvN operational requirements.
    """

    model_config = ConfigDict(from_attributes=True)

    dane_code: str = Field(..., description="Official 12-digit DANE establishment code")
    name: str = Field(..., description="Official establishment name registered in DUE")
    department_code: str = Field(..., description="DANE 2-digit department code")
    department_name: str = Field(..., description="Department name")
    municipality_code: str = Field(..., description="DANE 5-digit municipality code")
    municipality_name: str = Field(..., description="Municipality name")
    secretaria_code: str | None = Field(None, description="Certified territorial entity (ETC) code")
    secretaria_name: str | None = Field(None, description="Secretaría de Educación authority name")
    sector: str = Field(..., description="OFICIAL (Public) or NO OFICIAL (Private)")
    zone: str = Field(..., description="URBANA or RURAL")
    calendar: str = Field(..., description="Academic calendar (A, B, or CONTINUO)")
    academic_character: str = Field(..., description="ACADÉMICO, TÉCNICO, or NORMALISTA")
    official_address: str | None = Field(None, description="Official address in DUE")
    official_phone: str | None = Field(None, description="Official phone in DUE")
    official_email: str | None = Field(None, description="Official email in DUE (if registered)")
    educational_levels: list[str] = Field(default_factory=list, description="Levels offered (PREESCOLAR, PRIMARIA, etc.)")
    status: str = Field(..., description="ACTIVO, CIERRE TEMPORAL, or CIERRE DEFINITIVO")
    is_active: bool = Field(True, description="Whether establishment is currently active")
    campuses: list[OfficialCampusResponse] = Field(default_factory=list, description="Associated official campuses")
    provenance: OfficialProvenanceSchema = Field(..., description="Government data provenance metadata")
    pevn_required_fields: list[str] = Field(
        default_factory=list,
        description="Fields that must be provided by administrator for operational use if missing from official source (e.g. email)",
    )


class OfficialCatalogSyncStatusResponse(BaseModel):
    """Metrics and provenance status of the local official MEN/DANE catalog."""

    model_config = ConfigDict(from_attributes=True)

    catalog_status: Literal[
        "DEVELOPMENT_SEED",
        "PARTIAL_NATIONAL_DATA",
        "NATIONAL_CATALOG_INCOMPLETE",
        "NATIONAL_CATALOG_SYNCED",
        "EMPTY",
    ] = Field(..., description="Current deployment classification of the local catalog")
    sync_batch_id: str | None = Field(None, description="UUID of the most recent sync batch")
    last_successful_batch_id: str | None = Field(None, description="UUID of the last successful sync batch")
    source_system: str = Field("MINISTERIO DE EDUCACION NACIONAL (DUE) / DANE", description="Government source name")
    source_dataset: str = Field("datos.gov.co/c36d-tcj8", description="Primary government dataset ID")
    source_version: str | None = Field("2026-Q1", description="Dataset version / period")
    last_sync_at: datetime | None = Field(None, description="Timestamp of the most recent catalog sync")
    total_source_records: int = Field(0, description="Total source records processed in last batch")
    valid_records: int = Field(0, description="Total valid source records")
    rejected_records: int = Field(0, description="Total rejected source records")
    duplicate_records: int = Field(0, description="Total duplicate source records detected")
    total_valid_records: int = Field(0, description="Total valid records (alias)")
    total_rejected_records: int = Field(0, description="Total rejected records (alias)")
    total_duplicates: int = Field(0, description="Total duplicates detected (alias)")
    total_institutions: int = Field(..., description="Total official institutions currently cached in DB")
    total_campuses: int = Field(..., description="Total official campuses currently cached in DB")
    principal_campuses: int = Field(0, description="Total principal campuses")
    annex_campuses: int = Field(0, description="Total attached/annex campuses")
    principal_campuses_count: int = Field(0, description="Total principal campuses (alias)")
    attached_campuses_count: int = Field(0, description="Total attached campuses (alias)")
    departments_covered: int = Field(0, description="Total Colombian departments covered (out of 33)")
    municipalities_covered: int = Field(0, description="Total Colombian municipalities covered")
    is_stale: bool = Field(False, description="Whether the catalog exceeds the freshness threshold")
    freshness_warning: str | None = Field(None, description="Warning message if catalog data is stale")
    quality_gate_status: str = Field("PASSED", description="Status of Forensic Quality Gates (A through G)")
    synchronization_status: str | None = Field(None, description="Status of last sync batch (e.g. SUCCESS)")
    dataset_checksum: str | None = Field(None, description="SHA-256 checksum of the ingested source payload")
    accounting_reconciled: bool = Field(True, description="Whether source records = valid + rejected + duplicate")
    ingestion_progress: float = Field(100.0, description="Percentage completion of chunked ingestion")
    total_chunks: int = Field(0, description="Total chunks in the synchronization run")
    processed_chunks: int = Field(0, description="Total successfully processed chunks")
    failed_chunks: int = Field(0, description="Total failed chunks")
    audit_status: str = Field("VERIFIED", description="Forensic audit status of the catalog")


class OfficialCatalogSyncRequest(BaseModel):
    """Payload for triggering official catalog synchronization."""

    source_system: str = Field(
        "MINISTERIO DE EDUCACION NACIONAL (DUE) / DANE",
        description="Government source name",
    )
    source_dataset: str = Field(
        "datos.gov.co/c36d-tcj8",
        description="Official dataset identifier",
    )
    source_version: str | None = Field("2026-Q1", description="Dataset version / period")
    chunk_size: int = Field(
        1000,
        ge=1,
        le=10000,
        description="Batch chunk size for staging and transaction processing (default: 1000)",
    )
    max_rejection_percentage: float = Field(
        20.0,
        ge=0.0,
        le=100.0,
        description="Maximum allowed rejection percentage before triggering rollback",
    )
    strict_mode: bool = Field(
        False,
        description="If True, any validation failure aborts and rolls back the sync",
    )
    force_certified_dataset: bool = Field(
        False,
        description="If True, verifies that the payload represents the complete certified national dataset",
    )


class OfficialCatalogSyncResponse(BaseModel):
    """Result of an official catalog synchronization run."""

    batch_id: str = Field(..., description="Unique ID of the synchronization batch")
    status: str = Field(..., description="SUCCESS, FAILED, or ROLLED_BACK")
    quality_gate_status: str = Field("PASSED", description="Forensic Quality Gates evaluation")
    total_processed: int = Field(..., description="Total source records processed")
    valid_records: int = Field(..., description="Total valid records")
    rejected_records: int = Field(..., description="Total rejected records")
    duplicate_records: int = Field(..., description="Total duplicate records")
    institutions_synced: int = Field(..., description="Total institutions created or updated")
    campuses_synced: int = Field(..., description="Total campuses created or updated")
    departments_covered: int = Field(0, description="Total departments covered")
    municipalities_covered: int = Field(0, description="Total municipalities covered")
    total_chunks: int = Field(1, description="Total chunks executed")
    processed_chunks: int = Field(1, description="Total successful chunks")
    failed_chunks: int = Field(0, description="Total failed chunks")
    ingestion_progress: float = Field(100.0, description="Percentage of ingestion completed")
    audit_status: str = Field("VERIFIED", description="Forensic audit verdict")
    dataset_checksum: str | None = Field(None, description="SHA-256 checksum of the source dataset")
    accounting_reconciled: bool = Field(True, description="Reconciliation check")
    validation_errors: list[str] = Field(default_factory=list, description="Sample error details if any")
    completed_at: datetime = Field(..., description="Timestamp of batch completion")


class PromotionGateResultSchema(BaseModel):
    """Evaluation result for a single promotion quality gate."""

    gate_id: str
    criterion: str
    expected: str
    observed: str
    status: Literal["PASSED", "FAILED", "BLOCKED", "NOT_APPLICABLE"]
    evidence: str


class PromotionPreflightResponse(BaseModel):
    """Machine-readable Promotion Preflight Audit Certificate."""

    execution_id: str
    timestamp: datetime
    certificate_hash: str
    promotion_preflight_status: Literal["PASSED", "FAILED"]
    technical_gates_passed: bool
    total_institutions: int
    total_campuses: int
    principal_campuses: int
    annex_campuses: int
    departments_covered: int
    municipalities_covered: int
    governance_status: dict[str, Any]
    gates: list[PromotionGateResultSchema]


class PromotionAuthorizationRequest(BaseModel):
    """Explicit promotion authorization request payload."""

    preflight_certificate_hash: str = Field(..., description="Certificate hash from the preflight / final certification audit")
    catalog_hash: str = Field(..., description="Current canonical catalog hash")
    plan_hash: str | None = Field(None, description="Deterministic dry-run plan hash")
    snapshot_id: str | None = Field(None, description="Checkpoint snapshot ID bound to authorization")
    reason: str = Field(..., min_length=5, description="Administrative justification for promotion")
    confirm_governance: bool = Field(..., description="Explicit acknowledgement and confirmation of governance terms")


class PromotionAuthorizationResponse(BaseModel):
    """Response returned upon granting/denying promotion authorization."""

    authorization_id: str
    actor_id: str | None
    actor_email: str
    actor_role: str
    decision: Literal["AUTHORIZED", "REJECTED"]
    status: str
    catalog_hash: str
    preflight_certificate_hash: str
    plan_hash: str | None = None
    snapshot_id: str | None = None
    reason: str | None
    consumed_at: datetime | None = None
    created_at: datetime
    expires_at: datetime | None


class PromotionDryRunResponse(BaseModel):
    """Simulation dry-run results showing deterministic plan without mutating data."""

    dry_run_id: str
    dry_run_status: Literal["PASSED", "FAILED"]
    timestamp: datetime
    current_institutions: int
    current_campuses: int
    planned_institutions: int
    planned_campuses: int
    planned_inserts: int
    planned_updates: int
    planned_deletions: int
    duplicates: int
    orphans: int
    dane_conflicts: int
    fk_conflicts: int
    synthetic_records: int
    promotion_safe: bool
    plan_hash: str
    details: dict[str, Any]


class PromotionExecuteRequest(BaseModel):
    """Controlled promotion execution request."""

    authorization_id: str = Field(..., description="UUID of granted authorization")
    preflight_certificate_hash: str = Field(..., description="Verified preflight hash")
    plan_hash: str = Field(..., description="Verified dry-run plan hash")
    confirm_irreversible_step: bool = Field(..., description="Explicit double-confirmation")


class PromotionExecuteResponse(BaseModel):
    """Result of controlled catalog promotion execution."""

    promotion_id: str
    status: Literal["SUCCESS", "ALREADY_COMPLETED", "FAILED", "ROLLED_BACK"]
    catalog_status: str
    institutions_promoted: int
    campuses_promoted: int
    snapshot_hash: str
    execution_time_ms: float
    completed_at: datetime
    message: str


class PromotionRollbackRequest(BaseModel):
    """Request to rollback a promotion run to a specified snapshot."""

    snapshot_id: str = Field(..., description="UUID of the snapshot to restore to")
    reason: str = Field(..., min_length=5, description="Justification for rollback")
    confirm_rollback: bool = Field(..., description="Explicit rollback confirmation")


class PromotionRollbackResponse(BaseModel):
    """Rollback execution result."""

    rollback_id: str
    status: Literal["SUCCESS", "FAILED"]
    restored_snapshot_id: str
    catalog_status: str
    message: str
    timestamp: datetime


class PromotionStatusGovernanceResponse(BaseModel):
    """Consolidated state machine status of the promotion governance system."""

    current_state: Literal[
        "NATIONAL_CATALOG_INCOMPLETE",
        "READY_FOR_AUTHORIZATION",
        "AUTHORIZED",
        "DRY_RUN_PASSED",
        "SNAPSHOT_READY",
        "PROMOTION_IN_PROGRESS",
        "POST_PROMOTION_VALIDATION",
        "NATIONAL_CATALOG_SYNCED",
        "PROMOTION_FAILED",
        "ROLLBACK_AVAILABLE",
    ]
    catalog_status: str
    promotion_authorized: bool
    authorization_required: bool
    final_decision: Literal["GO", "NO-GO"]
    preflight_status: str
    last_certificate_hash: str | None
    last_authorization: PromotionAuthorizationResponse | None
    last_snapshot_hash: str | None
    last_dry_run_hash: str | None
    total_institutions: int
    total_campuses: int
    rollback_available: bool
    concurrency_locked: bool


class FinalCertificationGateResultSchema(BaseModel):
    """Result for an individual final pre-authorization certification gate."""

    gate_id: str
    criterion: str
    expected: str
    observed: str
    status: Literal["PASSED", "FAILED", "BLOCKED", "NOT_APPLICABLE"]
    evidence: str
    timestamp: datetime


class NationalCatalogFinalCertificationResponse(BaseModel):
    """Machine-readable Final Pre-Authorization Certification Audit Result."""

    execution_id: str
    timestamp: datetime
    certification_status: Literal["PASSED", "FAILED"]
    final_certification_hash: str
    catalog_hash: str
    total_institutions: int
    total_campuses: int
    principal_campuses: int
    annex_campuses: int
    georeferenced_campuses: int
    departments_covered: int
    municipalities_covered: int
    historical_campuses: int
    synthetic_records: int
    duplicate_records: int
    orphan_records: int
    rejected_records: int
    hash_stability: Literal["PASSED", "FAILED"]
    dry_run_status: Literal["PASSED", "FAILED"]
    snapshot_integrity: Literal["PASSED", "FAILED"]
    rollback_readiness: Literal["PASSED", "FAILED"]
    idempotency_readiness: Literal["PASSED", "FAILED"]
    concurrency_protection: Literal["PASSED", "FAILED"]
    authorization_enforcement: Literal["PASSED", "FAILED"]
    audit_trail_integrity: Literal["PASSED", "FAILED"]
    rbac_security: Literal["PASSED", "FAILED"]
    governance_state: dict[str, Any]
    gates: list[FinalCertificationGateResultSchema]
    machine_readable_verdict: str


