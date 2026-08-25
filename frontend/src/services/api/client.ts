/**
 * PEVN Frontend — HTTP API Client
 *
 * Centralized Axios instance for all backend API calls.
 *
 * Security & Design:
 *   - Access token stored STRICTLY in memory (never localStorage or sessionStorage)
 *   - Automatic request correlation ID injection
 *   - withCredentials: true ensures HttpOnly refresh token cookie is sent
 *   - Silent refresh queue handles concurrent 401s without race conditions
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
// Response Interceptor & Silent Refresh Queue
// ---------------------------------------------------------------------------

interface QueuedRequest {
  resolve: (value?: unknown) => void
  reject: (reason?: unknown) => void
}

let isRefreshing = false
let failedQueue: QueuedRequest[] = []

function processQueue(error: Error | null): void {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve()
    }
  })
  failedQueue = []
}

apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error: unknown) => {
    if (!axios.isAxiosError(error)) {
      return Promise.reject(normalizeError(error))
    }

    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }
    const status = error.response?.status

    // If 401 Unauthorized and not already retried and not auth login/refresh endpoint
    const isAuthEndpoint =
      originalRequest.url?.includes('/api/v1/auth/login') ||
      originalRequest.url?.includes('/api/v1/auth/refresh')

    if (status === 401 && !originalRequest._retry && !isAuthEndpoint) {
      if (isRefreshing) {
        // Queue the request until refresh finishes
        return await new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        })
          .then(async () => {
            if (inMemoryAccessToken) {
              originalRequest.headers.Authorization = `Bearer ${inMemoryAccessToken}`
            }
            return await apiClient(originalRequest)
          })
          .catch(async (err: unknown) => {
            return await Promise.reject(normalizeError(err))
          })
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        // Attempt silent refresh via HttpOnly cookie
        const refreshResponse = await axios.post<RefreshTokenResponse>(
          `${API_V1_URL}/auth/refresh`,
          {},
          { withCredentials: true }
        )

        const newAccessToken = refreshResponse.data.access_token
        setAccessToken(newAccessToken)
        processQueue(null)

        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
        return await apiClient(originalRequest)
      } catch (refreshErr: unknown) {
        setAccessToken(null)
        processQueue(new Error('Session refresh failed'))
        if (onAuthFailureCallback) {
          onAuthFailureCallback()
        }
        return await Promise.reject(normalizeError(refreshErr))
      } finally {
        isRefreshing = false
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
