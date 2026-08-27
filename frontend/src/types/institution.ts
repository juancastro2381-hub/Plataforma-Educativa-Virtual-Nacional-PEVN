/**
 * PEVN Frontend — Institution & Rector Onboarding Types
 *
 * TypeScript definitions matching backend Phase 3C contracts:
 *   - Institution provisioning and status lifecycle
 *   - Rector invitation token dispatch and verification
 *   - Rector self-service password onboarding (Argon2id)
 */

import type { CampusResponse, DocumentType } from './auth'

export interface InstitutionCreateRequest {
  dane_code: string
  name: string
  email: string
  phone?: string | null
  address?: string | null
  municipality_id: string
  main_campus_name?: string | null
  main_campus_dane?: string | null
}

export interface InstitutionStatusUpdateRequest {
  is_active: boolean
}

export interface InstitutionResponse {
  id: string
  municipality_id: string
  dane_code: string
  name: string
  email: string
  phone: string | null
  address: string | null
  is_active: boolean
  campuses: CampusResponse[]
  created_at: string
  updated_at: string
}

export interface InstitutionListResponse {
  items: InstitutionResponse[]
  total: number
  page: number
  page_size: number
}

export interface RectorInvitationCreateRequest {
  first_name: string
  last_name: string
  document_type: DocumentType
  document_number: string
  email: string
  phone_number?: string | null
}

export interface RectorInvitationResponse {
  invitation_id: string
  institution_id: string
  user_id: string
  email: string
  expires_at: string
  raw_invitation_token: string | null
  invitation_url: string | null
}

export interface VerifyInvitationRequest {
  token: string
}

export interface VerifyInvitationResponse {
  valid: boolean
  institution_name: string
  first_name: string
  email: string
  expires_at: string
}

export interface AcceptInvitationRequest {
  token: string
  password: string
  password_confirmation: string
}

export interface AcceptInvitationResponse {
  message: string
  user_id: string
  email: string
  is_active: boolean
}

export interface OfficialProvenance {
  source_system: string
  source_dataset: string
  source_record_id?: string | null
  source_updated_at?: string | null
  synced_at: string
}

export interface OfficialCampus {
  dane_sede_code: string
  name: string
  is_main: boolean
  zone?: string | null
  address?: string | null
  status: string
  is_active: boolean
}

export interface OfficialInstitutionResolution {
  dane_code: string
  name: string
  department_code: string
  department_name: string
  municipality_code: string
  municipality_name: string
  secretaria_code?: string | null
  secretaria_name?: string | null
  sector: string
  zone: string
  calendar: string
  academic_character: string
  official_address?: string | null
  official_phone?: string | null
  official_email?: string | null
  educational_levels: string[]
  status: string
  is_active: boolean
  campuses: OfficialCampus[]
  provenance: OfficialProvenance
  pevn_required_fields: string[]
}

export interface OfficialCatalogSyncStatus {
  catalog_status: 'DEVELOPMENT_SEED' | 'PARTIAL_NATIONAL_DATA' | 'NATIONAL_CATALOG_INCOMPLETE' | 'NATIONAL_CATALOG_SYNCED' | 'EMPTY'
  sync_batch_id?: string | null
  last_successful_batch_id?: string | null
  source_system: string
  source_dataset: string
  source_version?: string | null
  last_sync_at: string | null
  total_source_records: number
  valid_records: number
  rejected_records: number
  duplicate_records: number
  total_valid_records?: number
  total_rejected_records?: number
  total_duplicates?: number
  total_institutions: number
  total_campuses: number
  principal_campuses: number
  annex_campuses: number
  departments_covered: number
  municipalities_covered: number
  is_stale: boolean
  freshness_warning: string | null
  quality_gate_status: string
  synchronization_status: string | null
  dataset_checksum?: string | null
  accounting_reconciled: boolean
  ingestion_progress?: number
  total_chunks?: number
  processed_chunks?: number
  failed_chunks?: number
  audit_status?: string
}

export interface OfficialCatalogSyncRequest {
  source_system?: string
  source_dataset?: string
  source_version?: string
  chunk_size?: number
  max_rejection_percentage?: number
  strict_mode?: boolean
  force_certified_dataset?: boolean
}

export interface OfficialCatalogSyncResponse {
  batch_id: string
  status: string
  quality_gate_status: string
  total_processed: number
  valid_records: number
  rejected_records: number
  duplicate_records: number
  institutions_synced: number
  campuses_synced: number
  departments_covered: number
  municipalities_covered: number
  total_chunks?: number
  processed_chunks?: number
  failed_chunks?: number
  ingestion_progress?: number
  audit_status?: string
  dataset_checksum?: string | null
  accounting_reconciled: boolean
  validation_errors: string[]
  completed_at: string
}

export interface PromotionGateResult {
  gate_id: string
  criterion: string
  expected: string
  observed: string
  status: 'PASSED' | 'FAILED' | 'BLOCKED' | 'NOT_APPLICABLE'
  evidence: string
}

export interface PromotionPreflightResponse {
  execution_id: string
  timestamp: string
  certificate_hash: string
  promotion_preflight_status: 'PASSED' | 'FAILED'
  technical_gates_passed: boolean
  total_institutions: number
  total_campuses: number
  principal_campuses: number
  annex_campuses: number
  departments_covered: number
  municipalities_covered: number
  governance_status: Record<string, unknown>
  gates: PromotionGateResult[]
}

export interface PromotionAuthorizationRequest {
  preflight_certificate_hash: string
  catalog_hash: string
  reason: string
  confirm_governance: boolean
}

export interface PromotionAuthorizationResponse {
  authorization_id: string
  actor_id?: string | null
  actor_email: string
  actor_role: string
  decision: 'AUTHORIZED' | 'REJECTED'
  status: string
  catalog_hash: string
  preflight_certificate_hash: string
  reason?: string | null
  created_at: string
  expires_at?: string | null
}

export interface PromotionDryRunResponse {
  dry_run_id: string
  dry_run_status: 'PASSED' | 'FAILED'
  timestamp: string
  current_institutions: number
  current_campuses: number
  planned_institutions: number
  planned_campuses: number
  planned_inserts: number
  planned_updates: number
  planned_deletions: number
  duplicates: number
  orphans: number
  dane_conflicts: number
  fk_conflicts: number
  synthetic_records: number
  promotion_safe: boolean
  plan_hash: string
  details: Record<string, unknown>
}

export interface PromotionExecuteRequest {
  authorization_id: string
  preflight_certificate_hash: string
  plan_hash: string
  confirm_irreversible_step: boolean
}

export interface PromotionExecuteResponse {
  promotion_id: string
  status: 'SUCCESS' | 'ALREADY_COMPLETED' | 'FAILED' | 'ROLLED_BACK'
  catalog_status: string
  institutions_promoted: number
  campuses_promoted: number
  snapshot_hash: string
  execution_time_ms: number
  completed_at: string
  message: string
}

export interface PromotionRollbackRequest {
  snapshot_id: string
  reason: string
  confirm_rollback: boolean
}

export interface PromotionRollbackResponse {
  rollback_id: string
  status: 'SUCCESS' | 'FAILED'
  restored_snapshot_id: string
  catalog_status: string
  message: string
  timestamp: string
}

export interface PromotionStatusGovernance {
  current_state:
    | 'NATIONAL_CATALOG_INCOMPLETE'
    | 'READY_FOR_AUTHORIZATION'
    | 'AUTHORIZED'
    | 'DRY_RUN_PASSED'
    | 'SNAPSHOT_READY'
    | 'PROMOTION_IN_PROGRESS'
    | 'POST_PROMOTION_VALIDATION'
    | 'NATIONAL_CATALOG_SYNCED'
    | 'PROMOTION_FAILED'
    | 'ROLLBACK_AVAILABLE'
  catalog_status: string
  promotion_authorized: boolean
  authorization_required: boolean
  final_decision: 'GO' | 'NO-GO'
  preflight_status: string
  last_certificate_hash?: string | null
  last_authorization?: PromotionAuthorizationResponse | null
  last_snapshot_hash?: string | null
  last_dry_run_hash?: string | null
  total_institutions: number
  total_campuses: number
  rollback_available: boolean
  concurrency_locked: boolean
}

export interface FinalCertificationGateResult {
  gate_id: string
  criterion: string
  expected: string
  observed: string
  status: 'PASSED' | 'FAILED' | 'BLOCKED' | 'NOT_APPLICABLE'
  evidence: string
  timestamp: string
}

export interface NationalCatalogFinalCertificationResponse {
  execution_id: string
  timestamp: string
  certification_status: 'PASSED' | 'FAILED'
  final_certification_hash: string
  catalog_hash: string
  total_institutions: number
  total_campuses: number
  principal_campuses: number
  annex_campuses: number
  georeferenced_campuses: number
  departments_covered: number
  municipalities_covered: number
  historical_campuses: number
  synthetic_records: number
  duplicate_records: number
  orphan_records: number
  rejected_records: number
  hash_stability: 'PASSED' | 'FAILED'
  dry_run_status: 'PASSED' | 'FAILED'
  snapshot_integrity: 'PASSED' | 'FAILED'
  rollback_readiness: 'PASSED' | 'FAILED'
  idempotency_readiness: 'PASSED' | 'FAILED'
  concurrency_protection: 'PASSED' | 'FAILED'
  authorization_enforcement: 'PASSED' | 'FAILED'
  audit_trail_integrity: 'PASSED' | 'FAILED'
  rbac_security: 'PASSED' | 'FAILED'
  governance_state: Record<string, unknown>
  gates: FinalCertificationGateResult[]
  machine_readable_verdict: string
}

export interface PromotionAuditEvent {
  id: string
  correlation_id: string
  actor_id?: string | null
  action: string
  state_before: string
  state_after: string
  catalog_hash?: string | null
  result: string
  details: Record<string, unknown>
  created_at: string
}




