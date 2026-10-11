/**
 * PEVN Frontend — Academic Coordinator API Service
 *
 * Encapsulates backend HTTP calls for the COORDINATOR lifecycle:
 *   - List, filter, and search institutional coordinators
 *   - List active campuses of the institution for scope assignment
 *   - Transactionally provision or invite coordinators with institutional or campus scope
 *   - Resend/regenerate time-limited invitation tokens
 *   - Activate / suspend coordinators with automatic session token revocation
 */

import apiClient from '@/services/api/client'
import type {
  CoordinatorCampusOption,
  CoordinatorCreateRequest,
  CoordinatorListResponse,
  CoordinatorResendInvitationResponse,
  CoordinatorResponse,
} from '@/types'

export interface ListCoordinatorsParams {
  is_active?: boolean
  search?: string
  page?: number
  page_size?: number
}

export const coordinatorApi = {
  /**
   * List coordinators for the active institution with optional status, search, and pagination.
   */
  async listCoordinators(params: ListCoordinatorsParams = {}): Promise<CoordinatorListResponse> {
    const queryParams = new URLSearchParams()
    if (params.is_active !== undefined) queryParams.set('is_active', String(params.is_active))
    if (params.search && params.search.trim()) queryParams.set('search', params.search.trim())
    if (params.page) queryParams.set('page', String(params.page))
    if (params.page_size) queryParams.set('page_size', String(params.page_size))

    const url = `/api/v1/coordinators${queryParams.toString() ? `?${queryParams.toString()}` : ''}`
    const response = await apiClient.get<CoordinatorListResponse>(url)
    return response.data
  },

  /**
   * Retrieve single coordinator details by UUID.
   */
  async getCoordinator(id: string): Promise<CoordinatorResponse> {
    const response = await apiClient.get<CoordinatorResponse>(`/api/v1/coordinators/${id}`)
    return response.data
  },

  /**
   * List active campuses belonging to the institution for assignment selectors.
   */
  async listCampuses(): Promise<CoordinatorCampusOption[]> {
    const response = await apiClient.get<CoordinatorCampusOption[]>('/api/v1/coordinators/campuses')
    return response.data
  },

  /**
   * Provision or invite a new coordinator with institutional or campus scope.
   */
  async createCoordinator(payload: CoordinatorCreateRequest): Promise<CoordinatorResponse> {
    const response = await apiClient.post<CoordinatorResponse>('/api/v1/coordinators', payload)
    return response.data
  },

  /**
   * Resend / regenerate an active invitation token for a pending coordinator.
   */
  async resendInvitation(coordinatorId: string): Promise<CoordinatorResendInvitationResponse> {
    const response = await apiClient.post<CoordinatorResendInvitationResponse>(
      `/api/v1/coordinators/${coordinatorId}/resend-invitation`
    )
    return response.data
  },

  /**
   * Update active status of a coordinator (activate or suspend) with session invalidation.
   */
  async updateCoordinatorStatus(
    coordinatorId: string,
    isActive: boolean,
    reason?: string
  ): Promise<CoordinatorResponse> {
    const response = await apiClient.patch<CoordinatorResponse>(
      `/api/v1/coordinators/${coordinatorId}/status`,
      {
        is_active: isActive,
        reason: reason || null,
      }
    )
    return response.data
  },
}
