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
// Future Domain Types (Phase 2+)
// ---------------------------------------------------------------------------
// These will be added as the educational domain is implemented.
// Do not add placeholder types that don't map to real implementations.

// export interface User { ... }           // Phase 2
// export interface Institution { ... }    // Phase 2
// export interface Course { ... }         // Phase 3
// export interface Student { ... }        // Phase 3
