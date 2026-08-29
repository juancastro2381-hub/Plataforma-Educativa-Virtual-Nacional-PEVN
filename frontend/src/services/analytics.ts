/**
 * PEVN Frontend — Territorial Analytics API Service
 *
 * Encapsulates backend HTTP calls related to territorial indicators,
 * departmental and municipal distributions, and institutional KPIs.
 */

import apiClient from '@/services/api/client'
import type {
  DepartmentAnalyticsResponse,
  InstitutionalKPIResponse,
  MunicipalityAnalyticsResponse,
  TerritorialSummaryResponse,
} from '@/types'

export const analyticsApi = {
  /**
   * Get consolidated territorial summary KPIs based on caller scope.
   */
  async getTerritorialSummary(): Promise<TerritorialSummaryResponse> {
    const response = await apiClient.get<TerritorialSummaryResponse>(
      '/api/v1/analytics/territorial/summary'
    )
    return response.data
  },

  /**
   * Get department distribution list.
   */
  async getDepartmentDistribution(): Promise<DepartmentAnalyticsResponse> {
    const response = await apiClient.get<DepartmentAnalyticsResponse>(
      '/api/v1/analytics/territorial/departments'
    )
    return response.data
  },

  /**
   * Get municipality distribution list with optional department code filter.
   */
  async getMunicipalityDistribution(
    departmentCode?: string
  ): Promise<MunicipalityAnalyticsResponse> {
    const params = departmentCode ? { department_code: departmentCode } : undefined
    const response = await apiClient.get<MunicipalityAnalyticsResponse>(
      '/api/v1/analytics/territorial/municipalities',
      { params }
    )
    return response.data
  },

  /**
   * Get specific KPIs for an institution.
   */
  async getInstitutionalKPIs(
    institutionId: string
  ): Promise<InstitutionalKPIResponse> {
    const response = await apiClient.get<InstitutionalKPIResponse>(
      `/api/v1/analytics/territorial/institutions/${institutionId}`
    )
    return response.data
  },
}

export default analyticsApi
