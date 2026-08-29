/**
 * PEVN Frontend — Shared TypeScript Types
 *
 * Defines the shared type contracts used across the frontend application.
 * API response types mirror the backend Pydantic schemas.
 *
 * Phase 1: Foundation types for API communication and error handling.
 * Phase 2+: Domain types (User, Institution, Course, etc.) will be added here.
 */

// ---------------------------------------------------------------------------
// API Error Types
// ---------------------------------------------------------------------------

/** Standard API error payload returned by the backend */
export interface ApiError {
  code: string
  message: string
  correlation_id: string
  details?: ApiErrorDetail[]
}

/** Detail for a single validation error */
export interface ApiErrorDetail {
  field: string
  message: string
  type: string
}

/** Wrapped API error response */
export interface ApiErrorResponse {
  error: ApiError
}

// ---------------------------------------------------------------------------
// API Response Wrapper
// ---------------------------------------------------------------------------

/** Generic API response that may succeed or fail */
export type ApiResult<T> =
  { success: true; data: T; correlationId?: string } | { success: false; error: ApiError }

// ---------------------------------------------------------------------------
// Health & Readiness
// ---------------------------------------------------------------------------

export interface HealthResponse {
  status: 'ok'
  service: string
}

export interface ReadinessResponse {
  status: 'ready' | 'not_ready'
  checks: {
    database: 'ok' | 'error'
    redis: 'ok' | 'error'
  }
}

// ---------------------------------------------------------------------------
// Common UI State Types
// ---------------------------------------------------------------------------

export type LoadingState = 'idle' | 'loading' | 'success' | 'error'

export interface AsyncState<T> {
  state: LoadingState
  data: T | null
  error: ApiError | null
}

// ---------------------------------------------------------------------------
// Auth & Identity Types (Phase 2)
// ---------------------------------------------------------------------------
export * from './auth'

// ---------------------------------------------------------------------------
// Academic Management Types (Phase 3)
// ---------------------------------------------------------------------------
export * from './academic'

// ---------------------------------------------------------------------------
// Virtual Classroom & Meetings Types (Phase 4)
// ---------------------------------------------------------------------------
export * from './virtual_classroom'

// ---------------------------------------------------------------------------
// Institutional Provisioning & Onboarding Types (Phase 3C)
// ---------------------------------------------------------------------------
export * from './institution'

// ---------------------------------------------------------------------------
// Territorial Analytics Types (Phase 7 Step 4)
// ---------------------------------------------------------------------------
export * from './analytics'



