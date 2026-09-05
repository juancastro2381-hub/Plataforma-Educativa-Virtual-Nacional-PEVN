/**
 * PEVN Frontend — HTTP API Client
 *
 * Centralized Axios instance for all backend API calls.
 *
 * Security & Design:
 *   - Access token stored STRICTLY in memory (never localStorage or sessionStorage)
 *   - Automatic request correlation ID injection
 *   - withCredentials: true ensures HttpOnly refresh token cookie is sent
 *   - Single-Flight Refresh Coordinator prevents race conditions and token family revocation
 *   - Zero PII logging
 */

import axios, {
  type AxiosError,
  type AxiosResponse,
  type InternalAxiosRequestConfig,
} from 'axios'
import config, { API_V1_URL } from '@config/index'
import type { ApiError, ApiErrorDetail, ApiErrorResponse, RefreshTokenResponse } from '@/types'

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
// In-Memory Access Token Store (Zero-Persistence)
// ---------------------------------------------------------------------------

let inMemoryAccessToken: string | null = null
let onAuthFailureCallback: (() => void) | null = null

export function setAccessToken(token: string | null): void {
  inMemoryAccessToken = token
}

export function getAccessToken(): string | null {
  return inMemoryAccessToken
}

export function setOnAuthFailure(callback: (() => void) | null): void {
  onAuthFailureCallback = callback
}

// ---------------------------------------------------------------------------
// Raw Non-Intercepted Client (For Auth Refresh Loop Prevention)
// ---------------------------------------------------------------------------

export const rawAuthClient = axios.create({
  baseURL: config.apiBaseUrl,
  timeout: config.apiTimeoutMs,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
})

// ---------------------------------------------------------------------------
// Single-Flight Refresh Coordinator
// ---------------------------------------------------------------------------

let refreshPromise: Promise<string> | null = null

/**
 * Executes a single-flight token refresh operation.
 * All concurrent callers await the same Promise, guaranteeing exactly one in-flight
 * refresh HTTP request and preventing accidental token family revocation.
 */
export async function requestTokenRefresh(): Promise<string> {
  if (refreshPromise) {
    return await refreshPromise
  }

  refreshPromise = (async () => {
    try {
      const response = await rawAuthClient.post<RefreshTokenResponse>(
        `${API_V1_URL}/auth/refresh`,
        {}
      )
      const newAccessToken = response.data.access_token
      setAccessToken(newAccessToken)
      return newAccessToken
    } catch (err: unknown) {
      setAccessToken(null)
      if (onAuthFailureCallback) {
        onAuthFailureCallback()
      }
      throw normalizeError(err)
    } finally {
      refreshPromise = null
    }
  })()

  return await refreshPromise
}

// ---------------------------------------------------------------------------
// Client Instance
// ---------------------------------------------------------------------------

export const apiClient = axios.create({
  baseURL: config.apiBaseUrl,
  timeout: config.apiTimeoutMs,
  withCredentials: true, // Send HttpOnly cookies for refresh / auth endpoints
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
})

// ---------------------------------------------------------------------------
// Request Interceptor
// ---------------------------------------------------------------------------

apiClient.interceptors.request.use(
  (requestConfig: InternalAxiosRequestConfig) => {
    // Generate correlation ID for end-to-end tracing
    if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
      requestConfig.headers['X-Correlation-ID'] = crypto.randomUUID()
    }

    // Attach in-memory JWT Access Token if present
    if (inMemoryAccessToken && !requestConfig.headers.Authorization) {
      requestConfig.headers.Authorization = `Bearer ${inMemoryAccessToken}`
    }

    return requestConfig
  },
  (error: unknown) => Promise.reject(normalizeError(error))
)

// ---------------------------------------------------------------------------
// Response Interceptor & Single-Flight Retry
// ---------------------------------------------------------------------------

apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error: unknown) => {
    if (!axios.isAxiosError(error)) {
      return Promise.reject(normalizeError(error))
    }

    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }
    const status = error.response?.status

    // Explicitly bypass retry on authentication endpoints to prevent recursion
    const isAuthBypassEndpoint =
      originalRequest.url?.includes('/api/v1/auth/login') ||
      originalRequest.url?.includes('/api/v1/auth/refresh') ||
      originalRequest.url?.includes('/api/v1/auth/logout')

    if (status === 401 && !originalRequest._retry && !isAuthBypassEndpoint) {
      originalRequest._retry = true

      try {
        const newAccessToken = await requestTokenRefresh()
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
        return await apiClient(originalRequest)
      } catch (refreshErr: unknown) {
        return await Promise.reject(normalizeError(refreshErr))
      }
    }

    return await Promise.reject(normalizeError(error))
  }
)

// ---------------------------------------------------------------------------
// Error Normalization
// ---------------------------------------------------------------------------

export function normalizeError(error: unknown): AppApiError {
  if (error instanceof AppApiError) {
    return error
  }

  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<ApiErrorResponse>

    // Backend returned a structured error response
    const resData = axiosError.response?.data as unknown
    if (
      typeof resData === 'object' &&
      resData !== null &&
      'error' in resData
    ) {
      return new AppApiError((resData as ApiErrorResponse).error)
    }

    // FastAPI standard validation errors { detail: [{ loc, msg, type }] }
    if (
      typeof resData === 'object' &&
      resData !== null &&
      'detail' in resData &&
      Array.isArray((resData as { detail: unknown }).detail)
    ) {
      const detailArray = (resData as { detail: Array<{ loc?: string[]; msg?: string; type?: string }> }).detail
      const detailsList: ApiErrorDetail[] = detailArray.map((d) => ({
        field: Array.isArray(d.loc) ? d.loc.slice(1).join('.') || 'body' : 'body',
        message: d.msg || 'Valor inválido',
        type: d.type || 'validation_error',
      }))
      const combinedMsg = detailsList.map((d) => `${d.field}: ${d.message}`).join(', ')
      return new AppApiError({
        code: 'VALIDATION_ERROR',
        message: combinedMsg || 'Error de validación en la solicitud.',
        correlation_id: (axiosError.response?.headers?.['x-correlation-id'] as string) || '-',
        details: detailsList,
      })
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
