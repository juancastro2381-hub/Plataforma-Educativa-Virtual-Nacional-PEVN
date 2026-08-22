/**
 * PEVN Frontend — API Service Functions
 *
 * Typed API call wrappers for each backend endpoint.
 * All functions return ApiResult<T> discriminated unions for safe error handling.
 *
 * Phase 1: Health and readiness endpoints only.
 * Phase 2+: Authentication, user management, institution management.
 */

import type { ApiResult, HealthResponse, ReadinessResponse } from '@/types'
import apiClient, { normalizeError } from './client'
import config from '@config/index'

// ---------------------------------------------------------------------------
// Health & Readiness
// ---------------------------------------------------------------------------

/**
 * Check backend application health (liveness).
 * Does not require authentication.
 */
export async function checkHealth(): Promise<ApiResult<HealthResponse>> {
  try {
    const response = await apiClient.get<HealthResponse>(`${config.apiV1Prefix}/health`)
    return { success: true, data: response.data }
  } catch (error) {
    return { success: false, error: normalizeError(error) }
  }
}

/**
 * Check backend readiness (all dependencies available).
 * Does not require authentication.
 */
export async function checkReadiness(): Promise<ApiResult<ReadinessResponse>> {
  try {
    const response = await apiClient.get<ReadinessResponse>(`${config.apiV1Prefix}/ready`)
    return { success: true, data: response.data }
  } catch (error) {
    return { success: false, error: normalizeError(error) }
  }
}

// ---------------------------------------------------------------------------
// Future Phase 2+ API functions (not yet implemented)
// ---------------------------------------------------------------------------
// export async function login(credentials: LoginRequest): Promise<ApiResult<TokenResponse>>
// export async function logout(): Promise<ApiResult<void>>
// export async function getMe(): Promise<ApiResult<UserProfile>>
