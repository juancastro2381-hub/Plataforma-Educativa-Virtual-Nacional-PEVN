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

export interface CampusResponse {
  id: string
  institution_id: string
  dane_sede_code: string
  name: string
  is_main: boolean
  is_active: boolean
}

