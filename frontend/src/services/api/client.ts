/**
 * PEVN Frontend — HTTP API Client
 *
 * Centralized Axios instance for all backend API calls.
 *
 * Features:
 *   - Automatic base URL from configuration
 *   - Request correlation ID injection
 *   - Standardized error response transformation
 *   - Timeout enforcement
 *   - Content-Type defaults
 *
 * Security:
 *   - Never log response data that may contain PII
 *   - Never store tokens in localStorage (Phase 2: use HttpOnly cookies or memory)
 *   - Authorization headers will be added in Phase 2 via interceptors
 */

import axios, { type AxiosError, type AxiosResponse } from 'axios'
import config from '@config/index'
import type { ApiError, ApiErrorDetail, ApiErrorResponse } from '@/types'

// ---------------------------------------------------------------------------
// Error Class
// ---------------------------------------------------------------------------

export class AppApiError extends Error implements ApiError {
  readonly code: string
  readonly correlation_id: string
  readonly details?: ApiErrorDetail[]

  constructor(error: ApiError) {
    super(error.message)
    this.name = 'AppApiError'
    this.code = error.code
    this.correlation_id = error.correlation_id
    this.details = error.details
    Object.setPrototypeOf(this, AppApiError.prototype)
  }
}

// ---------------------------------------------------------------------------
// Client instance
// ---------------------------------------------------------------------------

export const apiClient = axios.create({
  baseURL: config.apiBaseUrl,
  timeout: config.apiTimeoutMs,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
})

// ---------------------------------------------------------------------------
// Request interceptor — add correlation ID
// ---------------------------------------------------------------------------

apiClient.interceptors.request.use(
  (requestConfig) => {
    // Generate a client-side correlation ID for tracing requests
    if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
      requestConfig.headers['X-Correlation-ID'] = crypto.randomUUID()
    }

    // Phase 2: Add Authorization header here
    // const token = getAccessToken()
    // if (token) { requestConfig.headers['Authorization'] = `Bearer ${token}` }

    return requestConfig
  },
  (error: unknown) => Promise.reject(normalizeError(error))
)

// ---------------------------------------------------------------------------
// Response interceptor — normalize errors
// ---------------------------------------------------------------------------

apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: unknown) => Promise.reject(normalizeError(error))
)

// ---------------------------------------------------------------------------
// Error normalization
// ---------------------------------------------------------------------------

/**
 * Normalize any error into a consistent AppApiError structure.
 * Ensures the rest of the application always deals with the same error shape.
 */
export function normalizeError(error: unknown): AppApiError {
  if (error instanceof AppApiError) {
    return error
  }

  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<ApiErrorResponse>

    // Backend returned a structured error response
    if (axiosError.response?.data.error) {
      return new AppApiError(axiosError.response.data.error)
    }

    // Network error or timeout
    if (axiosError.code === 'ECONNABORTED') {
      return new AppApiError({
        code: 'REQUEST_TIMEOUT',
        message: 'La solicitud tardó demasiado. Verifique su conexión e intente de nuevo.',
        correlation_id: '-',
      })
    }

    if (!axiosError.response) {
      return new AppApiError({
        code: 'NETWORK_ERROR',
        message: 'No se pudo conectar con el servidor. Verifique su conexión a internet.',
        correlation_id: '-',
      })
    }

    // HTTP error without structured body
    return new AppApiError({
      code: `HTTP_${String(axiosError.response.status)}`,
      message: `Error del servidor (${String(axiosError.response.status)})`,
      correlation_id: '-',
    })
  }

  // Unknown error
  const message = error instanceof Error ? error.message : 'Ha ocurrido un error inesperado.'
  return new AppApiError({
    code: 'UNKNOWN_ERROR',
    message,
    correlation_id: '-',
  })
}

export default apiClient
