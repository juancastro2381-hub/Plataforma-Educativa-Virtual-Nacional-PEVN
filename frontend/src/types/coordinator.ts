/**
 * PEVN Frontend — Coordinator Types
 *
 * Types for Academic Coordinator management, provisioning, and invitation lifecycle.
 */

import type { DocumentType } from './auth'

export interface CoordinatorCampusOption {
  id: string
  institution_id: string
  dane_sede_code: string
  name: string
  is_main: boolean
  is_active: boolean
}

export interface CoordinatorCreateRequest {
  email: string
  first_name: string
  last_name: string
  document_type: DocumentType
  document_number: string
  campus_id?: string | null
  password?: string | null
  is_active?: boolean
}

export interface CoordinatorResponse {
  id: string
  institution_id: string
  campus_id: string | null
  campus_name: string | null
  email: string
  username: string
  first_name: string
  last_name: string
  full_name: string
  document_type: DocumentType
  document_number: string
  role: string
  is_active: boolean
  is_verified: boolean
  created_at: string

  // Invitation metadata
  invitation_id: string | null
  invitation_status: 'pending' | 'accepted' | 'expired' | 'revoked' | 'direct' | string | null
  raw_invitation_token?: string | null
  invitation_url?: string | null
  email_delivery_status?: string | null
}

export interface CoordinatorListResponse {
  items: CoordinatorResponse[]
  total: number
  page: number
  page_size: number
}

export interface CoordinatorStatusUpdateRequest {
  is_active: boolean
  reason?: string | null
}

export interface CoordinatorResendInvitationResponse {
  invitation_id: string
  raw_invitation_token?: string | null
  invitation_url?: string | null
  email_delivery_status: string
  expires_at: string
  message: string
}
