/**
 * PEVN Frontend — Authentication & User API Service
 *
 * Encapsulates all backend HTTP calls related to identity,
 * session lifecycle, password management, and institutional profile.
 */

import apiClient, { requestTokenRefresh, setAccessToken } from '@/services/api/client'
import type {
  AcceptInvitationRequest,
  AcceptInvitationResponse,
  ChangePasswordRequest,
  InstitutionResponse,
  LoginRequest,
  LoginResponse,
  PasswordResetConfirmRequest,
  PasswordResetRequest,
  PasswordResetVerifyRequest,
  PasswordResetVerifyResponse,
  User,
  VerifyInvitationResponse,
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
   * Request silent token refresh using the single-flight coordinator.
   */
  async refresh(): Promise<string> {
    return await requestTokenRefresh()
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
   * Verify password reset token validity before showing reset form.
   */
  async verifyPasswordResetToken(
    data: PasswordResetVerifyRequest
  ): Promise<PasswordResetVerifyResponse> {
    const response = await apiClient.post<PasswordResetVerifyResponse>(
      '/api/v1/auth/password/reset/verify-token',
      data
    )
    return response.data
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

  /**
   * Public endpoint to verify cryptographic rector invitation token.
   */
  async verifyInvitation(token: string): Promise<VerifyInvitationResponse> {
    const response = await apiClient.post<VerifyInvitationResponse>(
      '/api/v1/auth/verify-invitation',
      { token }
    )
    return response.data
  },

  /**
   * Public endpoint to redeem invitation, set password with Argon2id and activate account.
   */
  async acceptInvitation(
    payload: AcceptInvitationRequest
  ): Promise<AcceptInvitationResponse> {
    const response = await apiClient.post<AcceptInvitationResponse>(
      '/api/v1/auth/accept-invitation',
      payload
    )
    return response.data
  },
}

export default authApi
