/**
 * PEVN Frontend — Authentication & Authorization Types
 *
 * Defines TypeScript interfaces matching the backend Phase 2 auth contracts.
 * Strictly adheres to zero-PII persistence and in-memory access token management.
 */

export type DocumentType =
  | 'CC'
  | 'TI'
  | 'CE'
  | 'PASSPORT'
  | 'PEP'
  | 'PPT'
  | 'OTHER'

export interface ScopeResponse {
  country_code: string | null
  department_id: string | null
  municipality_id: string | null
  institution_id: string | null
  campus_id: string | null
  is_national: boolean
  is_institution: boolean
}

export interface User {
  id: string
  email: string
  username: string
  first_name: string
  last_name: string
  full_name: string
  document_type: DocumentType
  document_number: string | null
  institution_id: string | null
  is_active: boolean
  is_verified: boolean
  must_change_password: boolean
  roles: string[]
  permissions: string[]
  scope: ScopeResponse
}

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  expires_in: number
  user: User
}

export interface RefreshTokenResponse {
  access_token: string
  token_type: string
  expires_in: number
  user: User
}

export interface ChangePasswordRequest {
  current_password: string
  new_password: string
}

export interface PasswordResetRequest {
  email: string
}

export interface PasswordResetConfirmRequest {
  token: string
  new_password: string
}

export interface PasswordResetVerifyRequest {
  token: string
}

export interface PasswordResetVerifyResponse {
  valid: boolean
  message: string
}

export interface CampusResponse {
  id: string
  institution_id: string
  dane_sede_code: string
  name: string
  is_main: boolean
  is_active: boolean
}

export interface UserResponse {
  id: string
  email: string
  username: string
  first_name: string
  last_name: string
  full_name: string
  document_type: DocumentType
  document_number: string
  institution_id: string | null
  is_active: boolean
  is_verified: boolean
  created_at: string
  updated_at: string
}

export interface UserListResponse {
  items: UserResponse[]
  total: number
  page: number
  page_size: number
}

// ---------------------------------------------------------------------------
// Guardian Public Self-Activation Types
// ---------------------------------------------------------------------------

export interface GuardianActivationRequest {
  student_code_simat: string
  guardian_document_type: DocumentType
  guardian_document_number: string
  email: string
}

export interface GuardianActivationResponse {
  message: string
  raw_activation_token?: string | null
}

export interface VerifyGuardianTokenRequest {
  token: string
}

export interface VerifyGuardianTokenResponse {
  valid: boolean
  guardian_name: string
  student_name: string
  institution_name: string
  expires_at: string
}

export interface GuardianAcceptActivationRequest {
  token: string
  password: string
  password_confirmation: string
}

export interface GuardianAcceptActivationResponse {
  message: string
  user_id: string
  email: string
  is_active: boolean
}

