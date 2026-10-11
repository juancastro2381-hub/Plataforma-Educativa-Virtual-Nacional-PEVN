/**
 * PEVN Frontend — Institution Onboarding Domain Types (NTA-04)
 */

export type OnboardingRequestStatus =
  | 'DRAFT'
  | 'SUBMITTED'
  | 'UNDER_REVIEW'
  | 'APPROVED'
  | 'REJECTED'
  | 'CANCELLED'
  | 'PROVISIONED'

export type CatalogOnboardingStatus = 'AVAILABLE' | 'EN_TRAMITE' | 'PROVISIONED'

export interface CatalogExplorerItem {
  id: string
  dane_code: string
  name: string
  department_code: string
  department_name: string
  department_id?: string | null
  municipality_code: string
  municipality_name: string
  municipality_id?: string | null
  official_address?: string | null
  sector?: string | null
  is_active: boolean
  principal_campus_name?: string | null
  campus_count: number
  onboarding_status: CatalogOnboardingStatus
  active_request_id?: string | null
  active_request_number?: string | null
  institution_id?: string | null
}

export interface CatalogExplorerListResponse {
  items: CatalogExplorerItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface OnboardingRequestCreatePayload {
  catalog_institution_id: string
  contact_email: string
  contact_phone?: string | null
  proposed_rector_name?: string | null
  proposed_rector_email?: string | null
  proposed_rector_doc_type?: string | null
  proposed_rector_doc_num?: string | null
  justification?: string | null
  is_draft?: boolean
  idempotency_key?: string | null
}

export interface OnboardingApprovalPayload {
  notes?: string | null
}

export interface OnboardingRejectionPayload {
  rejection_reason: string
}

export interface OnboardingCancellationPayload {
  cancellation_reason?: string | null
}

export interface OnboardingRequestDetail {
  id: string
  request_number: string
  catalog_institution_id: string
  dane_code: string
  institution_name?: string | null
  department_id: string
  department_name?: string | null
  department_code?: string | null
  municipality_id: string
  municipality_name?: string | null
  municipality_code?: string | null
  requested_by_id: string
  requester_name?: string | null
  requester_email?: string | null
  requester_role: string
  status: OnboardingRequestStatus
  institution_id?: string | null
  contact_email: string
  contact_phone?: string | null
  proposed_rector_name?: string | null
  proposed_rector_email?: string | null
  proposed_rector_doc_type?: string | null
  proposed_rector_doc_num?: string | null
  justification?: string | null
  reviewed_by_id?: string | null
  reviewed_by_name?: string | null
  reviewed_at?: string | null
  review_notes?: string | null
  approved_by_id?: string | null
  approved_by_name?: string | null
  approved_at?: string | null
  rejected_by_id?: string | null
  rejected_by_name?: string | null
  rejected_at?: string | null
  rejection_reason?: string | null
  cancelled_by_id?: string | null
  cancelled_by_name?: string | null
  cancelled_at?: string | null
  cancellation_reason?: string | null
  provisioned_by_id?: string | null
  provisioned_by_name?: string | null
  provisioned_at?: string | null
  lock_version: number
  idempotency_key?: string | null
  created_at: string
  updated_at: string
}

export interface OnboardingRequestListResponse {
  items: OnboardingRequestDetail[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface OnboardingProvisionResult {
  request_id: string
  request_number: string
  institution_id: string
  institution_name: string
  dane_code: string
  campuses_created: number
  rector_invited: boolean
  rector_status: string
  rector_invitation_id?: string | null
  activation_url?: string | null
  raw_invitation_token?: string | null
}
