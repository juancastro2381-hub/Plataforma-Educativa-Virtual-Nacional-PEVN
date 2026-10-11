/**
 * PEVN Frontend — Municipality Administrator & Territorial Provisioning API Service
 *
 * Encapsulates backend HTTP calls for the MUNICIPALITY_ADMIN lifecycle:
 *   - Fetch canonical Colombian municipalities filtered by department scope
 *   - Fetch canonical Colombian departments (for national administrators)
 *   - List, filter, and search municipality administrators
 *   - Transactionally provision new municipality administrators with strict territorial assignment
 *   - Activate / deactivate administrators with automatic session revocation
 *   - Controlled municipality reassignment with automatic session revocation
 */

import apiClient from '@/services/api/client'
import type {
  DepartmentOption,
  ListMunicipalityAdminsParams,
  MunicipalityAdmin,
  MunicipalityAdminCreateRequest,
  MunicipalityAdminInvitationResponse,
  MunicipalityAdminListResponse,
  MunicipalityAdminReassignMunicipalityRequest,
  MunicipalityAdminStatusUpdateRequest,
  MunicipalityOption,
} from '@/types'

export const municipalityAdminApi = {
  /**
   * Fetch canonical active Colombian municipalities, optionally scoped to a department.
   * If caller is a Department Admin, the backend automatically scopes this to their assigned department.
   */
  async listMunicipalities(departmentId?: string): Promise<MunicipalityOption[]> {
    const queryParams = new URLSearchParams()
    if (departmentId) queryParams.set('department_id', departmentId)
    const url = `/api/v1/municipality-admins/municipalities${queryParams.toString() ? `?${queryParams.toString()}` : ''}`
    const response = await apiClient.get<MunicipalityOption[]>(url)
    return response.data
  },

  /**
   * Fetch canonical active Colombian departments (for supervisory / national selectors).
   */
  async listDepartments(): Promise<DepartmentOption[]> {
    const response = await apiClient.get<DepartmentOption[]>('/api/v1/departments')
    return response.data
  },

  /**
   * List municipality administrators with territorial filters, search, and pagination.
   */
  async listMunicipalityAdmins(
    params: ListMunicipalityAdminsParams = {}
  ): Promise<MunicipalityAdminListResponse> {
    const queryParams = new URLSearchParams()
    if (params.department_id) queryParams.set('department_id', params.department_id)
    if (params.municipality_id) queryParams.set('municipality_id', params.municipality_id)
    if (params.is_active !== undefined) queryParams.set('is_active', String(params.is_active))
    if (params.search && params.search.trim()) queryParams.set('search', params.search.trim())
    if (params.page) queryParams.set('page', String(params.page))
    if (params.page_size) queryParams.set('page_size', String(params.page_size))

    const url = `/api/v1/municipality-admins${queryParams.toString() ? `?${queryParams.toString()}` : ''}`
    const response = await apiClient.get<MunicipalityAdminListResponse>(url)
    return response.data
  },

  /**
   * Get single municipality administrator by user UUID.
   */
  async getMunicipalityAdmin(userId: string): Promise<MunicipalityAdmin> {
    const response = await apiClient.get<MunicipalityAdmin>(`/api/v1/municipality-admins/${userId}`)
    return response.data
  },

  /**
   * Provision a new MUNICIPALITY_ADMIN user with transactional territorial binding.
   */
  async createMunicipalityAdmin(
    payload: MunicipalityAdminCreateRequest
  ): Promise<MunicipalityAdmin> {
    const response = await apiClient.post<MunicipalityAdmin>(
      '/api/v1/municipality-admins',
      payload
    )
    return response.data
  },

  /**
   * Update active status of a MUNICIPALITY_ADMIN (revokes active sessions upon deactivation).
   */
  async updateStatus(
    userId: string,
    payload: MunicipalityAdminStatusUpdateRequest
  ): Promise<MunicipalityAdmin> {
    const response = await apiClient.patch<MunicipalityAdmin>(
      `/api/v1/municipality-admins/${userId}/status`,
      payload
    )
    return response.data
  },

  /**
   * Explicitly reassign the administrator to another canonical municipality.
   * Automatically invalidates active session tokens.
   */
  async reassignMunicipality(
    userId: string,
    payload: MunicipalityAdminReassignMunicipalityRequest
  ): Promise<MunicipalityAdmin> {
    const response = await apiClient.patch<MunicipalityAdmin>(
      `/api/v1/municipality-admins/${userId}/municipality`,
      payload
    )
    return response.data
  },

  /**
   * Resend a single-use invitation token for a municipality administrator.
   */
  async resendInvitation(userId: string): Promise<MunicipalityAdminInvitationResponse> {
    const response = await apiClient.post<MunicipalityAdminInvitationResponse>(
      `/api/v1/municipality-admins/${userId}/resend-invitation`
    )
    return response.data
  },
}

