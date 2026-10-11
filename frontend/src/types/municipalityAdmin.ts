/**
 * PEVN Frontend — Municipality Administrator & Territorial Provisioning Types
 *
 * Types matching the backend municipality admin lifecycle API (NTA-07, NTA-08, NTA-09).
 */

export interface MunicipalityOption {
  id: string
  code: string
  name: string
  department_id: string
  department_code?: string | null
  department_name?: string | null
  display_label: string
}

export interface MunicipalityAdmin {
  id: string
  email: string
  username: string
  first_name: string
  last_name: string
  full_name: string
  document_type: string
  document_number: string
  is_active: boolean
  is_verified: boolean
  roles: string[]
  municipality_id: string
  municipality_code: string
  municipality_name: string
  department_id: string
  department_code: string
  department_name: string
  created_at: string
  raw_invitation_token?: string | null
  invitation_id?: string | null
  email_delivery_status?: string | null
  invitation_url?: string | null
}

export interface MunicipalityAdminListResponse {
  items: MunicipalityAdmin[]
  total: number
  page: number
  page_size: number
}

export interface MunicipalityAdminCreateRequest {
  municipality_id: string
  email: string
  username: string
  first_name: string
  last_name: string
  document_type?: string
  document_number?: string
}

export interface MunicipalityAdminInvitationResponse {
  invitation_id: string
  municipality_id: string
  municipality_code: string
  municipality_name: string
  user_id: string
  email: string
  expires_at: string
  is_used: boolean
  raw_invitation_token?: string | null
  email_delivery_status?: string
  invitation_url?: string | null
}

export interface MunicipalityAdminStatusUpdateRequest {
  is_active: boolean
  reason?: string
}

export interface MunicipalityAdminReassignMunicipalityRequest {
  new_municipality_id: string
  reason?: string
}

export interface ListMunicipalityAdminsParams {
  department_id?: string
  municipality_id?: string
  is_active?: boolean
  search?: string
  page?: number
  page_size?: number
}
