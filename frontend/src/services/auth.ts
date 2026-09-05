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
  GuardianAcceptActivationRequest,
  GuardianAcceptActivationResponse,
  GuardianActivationRequest,
  GuardianActivationResponse,
  InstitutionResponse,
  LoginRequest,
  LoginResponse,
  PasswordResetConfirmRequest,
  PasswordResetRequest,
  PasswordResetVerifyRequest,
  PasswordResetVerifyResponse,
  User,
  VerifyGuardianTokenResponse,
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
   * Request a new access token via the HTTP-only refresh cookie.
   */
  async refreshToken(): Promise<string> {
    return requestTokenRefresh()
  },

  async refresh(): Promise<string> {
    return requestTokenRefresh()
  },

  /**
   * Terminate user session on the server and clear memory token.
   */
  async logout(): Promise<void> {
    try {
      await apiClient.post('/api/v1/auth/logout')
    } finally {
      setAccessToken(null)
    }
  },

  /**
   * Fetch profile of currently authenticated user.
   */
  async getMe(): Promise<User> {
    const response = await apiClient.get<User>('/api/v1/auth/me')
    return response.data
  },

  async getMyProfile(): Promise<User> {
    const response = await apiClient.get<User>('/api/v1/auth/me')
    return response.data
  },

  /**
   * Change user password (authenticated).
   */
  async changePassword(payload: ChangePasswordRequest): Promise<void> {
    await apiClient.post('/api/v1/auth/change-password', payload)
  },

  /**
   * Request a password reset email/link.
   */
  async requestPasswordReset(payload: PasswordResetRequest): Promise<void> {
    await apiClient.post('/api/v1/auth/forgot-password', payload)
  },

  /**
   * Verify a password reset token.
   */
  async verifyPasswordResetToken(
    payload: PasswordResetVerifyRequest
  ): Promise<PasswordResetVerifyResponse> {
    const response = await apiClient.post<PasswordResetVerifyResponse>(
      '/api/v1/auth/verify-reset-token',
      payload
    )
    return response.data
  },

  /**
   * Confirm password reset with new password.
   */
  async confirmPasswordReset(
    payload: PasswordResetConfirmRequest
  ): Promise<void> {
    await apiClient.post('/api/v1/auth/reset-password', payload)
  },

  /**
   * Fetch authenticated user's institution details.
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

  /**
   * Public endpoint to request a guardian activation token.
   */
  async requestGuardianActivation(
    payload: GuardianActivationRequest
  ): Promise<GuardianActivationResponse> {
    const response = await apiClient.post<GuardianActivationResponse>(
      '/api/v1/auth/guardians/request-activation',
      payload
    )
    return response.data
  },

  /**
   * Public endpoint to verify a guardian activation token.
   */
  async verifyGuardianToken(
    token: string
  ): Promise<VerifyGuardianTokenResponse> {
    const response = await apiClient.post<VerifyGuardianTokenResponse>(
      '/api/v1/auth/guardians/verify-token',
      { token }
    )
    return response.data
  },

  /**
   * Public endpoint to redeem a guardian activation token and set password.
   */
  async acceptGuardianActivation(
    payload: GuardianAcceptActivationRequest
  ): Promise<GuardianAcceptActivationResponse> {
    const response = await apiClient.post<GuardianAcceptActivationResponse>(
      '/api/v1/auth/guardians/accept-activation',
      payload
    )
    return response.data
  },
}

export default authApi
