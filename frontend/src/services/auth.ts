/**
 * PEVN Frontend — Authentication & User API Service
 *
 * Encapsulates all backend HTTP calls related to identity,
 * session lifecycle, password management, and institutional profile.
 */

import apiClient, { setAccessToken } from '@/services/api/client'
import type {
  ChangePasswordRequest,
  InstitutionResponse,
  LoginRequest,
  LoginResponse,
  PasswordResetConfirmRequest,
  PasswordResetRequest,
  RefreshTokenResponse,
  User,
} from '@/types'

export const authApi = {
  /**
   * Authenticate user with credentials.
   * On success, registers the access token in memory.
   */
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await apiClient.post<LoginResponse>(
      '/api/v1/auth/login',
      credentials
    )
    setAccessToken(response.data.access_token)
    return response.data
  },

  /**
   * Request silent token refresh using the HttpOnly cookie.
   */
  async refresh(): Promise<RefreshTokenResponse> {
    const response = await apiClient.post<RefreshTokenResponse>(
      '/api/v1/auth/refresh',
      {}
    )
    setAccessToken(response.data.access_token)
    return response.data
  },

  /**
   * Invalidate active session and clear in-memory token.
   */
  async logout(): Promise<void> {
    try {
      await apiClient.post('/api/v1/auth/logout', {})
    } finally {
      setAccessToken(null)
    }
  },

  /**
   * Fetch current authenticated user profile.
   */
  async getMyProfile(): Promise<User> {
    const response = await apiClient.get<User>('/api/v1/auth/me')
    return response.data
  },

  /**
   * Change password for the current user.
   */
  async changePassword(data: ChangePasswordRequest): Promise<void> {
    await apiClient.post('/api/v1/auth/password/change', data)
  },

  /**
   * Request password reset link.
   */
  async requestPasswordReset(data: PasswordResetRequest): Promise<void> {
    await apiClient.post('/api/v1/auth/password/reset/request', data)
  },

  /**
   * Confirm password reset with token.
   */
  async confirmPasswordReset(data: PasswordResetConfirmRequest): Promise<void> {
    await apiClient.post('/api/v1/auth/password/reset/confirm', data)
  },

  /**
   * Fetch user's assigned institution details.
   */
  async getMyInstitution(): Promise<InstitutionResponse> {
    const response = await apiClient.get<InstitutionResponse>(
      '/api/v1/institutions/me'
    )
    return response.data
  },

  /**
   * Fetch institution by ID (enforces territorial scope).
   */
  async getInstitutionById(id: string): Promise<InstitutionResponse> {
    const response = await apiClient.get<InstitutionResponse>(
      `/api/v1/institutions/${id}`
    )
    return response.data
  },
}

export default authApi
