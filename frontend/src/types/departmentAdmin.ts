/**
 * PEVN Frontend — Department Administrator & Territorial Provisioning Types
 *
 * Types matching the backend department admin lifecycle API.
 */

export interface DepartmentOption {
  id: string
  code: string
  name: string
}

export type EmailDeliveryStatus = 'EMAIL_SENT' | 'EMAIL_NOT_CONFIGURED' | 'EMAIL_SEND_FAILED'

export interface DepartmentAdmin {
  id: string
  email: string
  first_name: string
  last_name: string
  full_name: string
  username: string
  role_id: string
  role_code: string
  department_id: string
  department_code: string
  department_name: string
  is_active: boolean
  created_at: string
  updated_at: string | null
  last_login_at: string | null
  raw_invitation_token?: string | null
  invitation_id?: string | null
  email_delivery_status?: EmailDeliveryStatus
  invitation_url?: string | null
}

export interface DepartmentAdminKPIs {
  total: number
  active: number
  inactive: number
  departments_covered: number
  total_canonical_departments: number
}

export interface DepartmentAdminListResponse {
  items: DepartmentAdmin[]
  total: number
  page: number
  page_size: number
  kpis?: DepartmentAdminKPIs
}

export interface DepartmentAdminCreateRequest {
  first_name: string
  last_name: string
  email: string
  username: string
  password?: string
  department_id: string
}

export interface DepartmentAdminInvitationResponse {
  invitation_id: string
  department_id: string
  department_code: string
  department_name: string
  user_id: string
  email: string
  expires_at: string
  is_used: boolean
  raw_invitation_token?: string | null
  email_delivery_status?: EmailDeliveryStatus
  invitation_url?: string | null
}

export interface DepartmentAdminUpdateRequest {
  first_name?: string
  last_name?: string
  email?: string
  username?: string
  is_active?: boolean
}

export interface DepartmentAdminReassignDepartmentRequest {
  new_department_id: string
}

export interface DepartmentAdminStatusUpdateRequest {
  is_active: boolean
}

export interface ListDepartmentAdminsParams {
  department_id?: string
  is_active?: boolean
  search?: string
  page?: number
  page_size?: number
}
