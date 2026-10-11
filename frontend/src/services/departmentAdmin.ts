/**
 * PEVN Frontend — Department Administrator & Territorial Provisioning API Service
 *
 * Encapsulates backend HTTP calls for the DEPARTMENT_ADMIN lifecycle:
 *   - Fetch canonical Colombian departments from backend API (never hardcoded)
 *   - List, filter, search department administrators
 *   - Create new department administrator with canonical department binding
 *   - Edit administrator profile details
 *   - Reassign department with session revocation
 *   - Activate / deactivate administrators
 */

import apiClient from '@/services/api/client'
import type {
  DepartmentAdmin,
  DepartmentAdminCreateRequest,
  DepartmentAdminInvitationResponse,
  DepartmentAdminKPIs,
  DepartmentAdminListResponse,
  DepartmentAdminReassignDepartmentRequest,
  DepartmentAdminStatusUpdateRequest,
  DepartmentAdminUpdateRequest,
  DepartmentOption,
  ListDepartmentAdminsParams,
} from '@/types'

export const departmentAdminApi = {
  /**
   * Fetch canonical active Colombian departments.
   * UI department selector is strictly populated from this endpoint.
   */
  async listDepartments(): Promise<DepartmentOption[]> {
    const response = await apiClient.get<DepartmentOption[]>('/api/v1/departments')
    return response.data
  },

  /**
   * Fetch authoritative server-side KPI metrics for departmental administrators.
   */
  async getKPIs(): Promise<DepartmentAdminKPIs> {
    const response = await apiClient.get<DepartmentAdminKPIs>('/api/v1/department-admins/kpis')
    return response.data
  },

  /**
   * List departmental administrators with optional filters (department, status, search, pagination).
   */
  async listDepartmentAdmins(
    params: ListDepartmentAdminsParams = {}
  ): Promise<DepartmentAdminListResponse> {
    const queryParams = new URLSearchParams()
    if (params.department_id) queryParams.set('department_id', params.department_id)
    if (params.is_active !== undefined) queryParams.set('is_active', String(params.is_active))
    if (params.search && params.search.trim()) queryParams.set('search', params.search.trim())
    if (params.page) queryParams.set('page', String(params.page))
    if (params.page_size) queryParams.set('page_size', String(params.page_size))

    const url = `/api/v1/department-admins${queryParams.toString() ? `?${queryParams.toString()}` : ''}`
    const response = await apiClient.get<DepartmentAdminListResponse>(url)
    return response.data
  },

  /**
   * Get single department administrator by user UUID.
   */
  async getDepartmentAdmin(userId: string): Promise<DepartmentAdmin> {
    const response = await apiClient.get<DepartmentAdmin>(`/api/v1/department-admins/${userId}`)
    return response.data
  },

  /**
   * Create a new DEPARTMENT_ADMIN user with transactional territorial binding.
   */
  async createDepartmentAdmin(
    payload: DepartmentAdminCreateRequest
  ): Promise<DepartmentAdmin> {
    const response = await apiClient.post<DepartmentAdmin>(
      '/api/v1/department-admins',
      payload
    )
    return response.data
  },

  /**
   * Update profile fields (first_name, last_name, email, username) of a DEPARTMENT_ADMIN.
   */
  async updateDepartmentAdmin(
    userId: string,
    payload: DepartmentAdminUpdateRequest
  ): Promise<DepartmentAdmin> {
    const response = await apiClient.patch<DepartmentAdmin>(
      `/api/v1/department-admins/${userId}`,
      payload
    )
    return response.data
  },

  /**
   * Explicitly reassign the administrator to another Colombian department.
   * Revokes existing active sessions so next login immediately resolves the new territorial scope.
   */
  async reassignDepartment(
    userId: string,
    payload: DepartmentAdminReassignDepartmentRequest
  ): Promise<DepartmentAdmin> {
    const response = await apiClient.patch<DepartmentAdmin>(
      `/api/v1/department-admins/${userId}/department`,
      payload
    )
    return response.data
  },

  /**
   * Activate or deactivate a departmental administrator account.
   */
  async updateStatus(
    userId: string,
    payload: DepartmentAdminStatusUpdateRequest
  ): Promise<DepartmentAdmin> {
    const response = await apiClient.patch<DepartmentAdmin>(
      `/api/v1/department-admins/${userId}/status`,
      payload
    )
    return response.data
  },

  /**
   * Resend onboarding invitation for a department administrator.
   */
  async resendInvitation(userId: string): Promise<DepartmentAdminInvitationResponse> {
    const response = await apiClient.post<DepartmentAdminInvitationResponse>(
      `/api/v1/department-admins/${userId}/resend-invitation`
    )
    return response.data
  },
}
