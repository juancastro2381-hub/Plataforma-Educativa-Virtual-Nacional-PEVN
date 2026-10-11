/**
 * PEVN Frontend — Institution Onboarding API Service (NTA-04)
 */

import apiClient from '@/services/api/client'
import type {
  CatalogExplorerListResponse,
  OnboardingApprovalPayload,
  OnboardingCancellationPayload,
  OnboardingProvisionResult,
  OnboardingRejectionPayload,
  OnboardingRequestCreatePayload,
  OnboardingRequestDetail,
  OnboardingRequestListResponse,
} from '@/types/onboarding'

export interface ExploreCatalogParams {
  dane_code?: string
  name?: string
  department_id?: string
  municipality_id?: string
  onboarding_status?: string
  page?: number
  page_size?: number
}

export interface ListOnboardingRequestsParams {
  status?: string
  department_id?: string
  municipality_id?: string
  search?: string
  page?: number
  page_size?: number
}

export const onboardingApi = {
  /**
   * Explore the official educational catalog enriched with PEVN onboarding status.
   */
  async exploreCatalog(params: ExploreCatalogParams = {}): Promise<CatalogExplorerListResponse> {
    const queryParams = new URLSearchParams()
    if (params.dane_code) queryParams.set('dane_code', params.dane_code.trim())
    if (params.name) queryParams.set('name', params.name.trim())
    if (params.department_id) queryParams.set('department_id', params.department_id)
    if (params.municipality_id) queryParams.set('municipality_id', params.municipality_id)
    if (params.onboarding_status) queryParams.set('onboarding_status', params.onboarding_status)
    if (params.page) queryParams.set('page', String(params.page))
    if (params.page_size) queryParams.set('page_size', String(params.page_size))

    const url = `/api/v1/onboarding/catalog${queryParams.toString() ? `?${queryParams.toString()}` : ''}`
    const response = await apiClient.get<CatalogExplorerListResponse>(url)
    return response.data
  },

  /**
   * Create and file a new institution onboarding request.
   */
  async createRequest(payload: OnboardingRequestCreatePayload): Promise<OnboardingRequestDetail> {
    const response = await apiClient.post<OnboardingRequestDetail>('/api/v1/onboarding/requests', payload)
    return response.data
  },

  /**
   * List onboarding requests with territorial and status filters.
   */
  async listRequests(params: ListOnboardingRequestsParams = {}): Promise<OnboardingRequestListResponse> {
    const queryParams = new URLSearchParams()
    if (params.status) queryParams.set('status', params.status)
    if (params.department_id) queryParams.set('department_id', params.department_id)
    if (params.municipality_id) queryParams.set('municipality_id', params.municipality_id)
    if (params.search) queryParams.set('search', params.search.trim())
    if (params.page) queryParams.set('page', String(params.page))
    if (params.page_size) queryParams.set('page_size', String(params.page_size))

    const url = `/api/v1/onboarding/requests${queryParams.toString() ? `?${queryParams.toString()}` : ''}`
    const response = await apiClient.get<OnboardingRequestListResponse>(url)
    return response.data
  },

  /**
   * Get detail of a specific onboarding request.
   */
  async getRequest(id: string): Promise<OnboardingRequestDetail> {
    const response = await apiClient.get<OnboardingRequestDetail>(`/api/v1/onboarding/requests/${id}`)
    return response.data
  },

  /**
   * Start technical review (transition to UNDER_REVIEW).
   */
  async startReview(id: string, notes?: string): Promise<OnboardingRequestDetail> {
    const query = notes ? `?notes=${encodeURIComponent(notes)}` : ''
    const response = await apiClient.post<OnboardingRequestDetail>(`/api/v1/onboarding/requests/${id}/start-review${query}`)
    return response.data
  },

  /**
   * Approve onboarding request.
   */
  async approveRequest(id: string, payload?: OnboardingApprovalPayload): Promise<OnboardingRequestDetail> {
    const response = await apiClient.post<OnboardingRequestDetail>(`/api/v1/onboarding/requests/${id}/approve`, payload || {})
    return response.data
  },

  /**
   * Reject onboarding request (requires >= 10 chars reason).
   */
  async rejectRequest(id: string, payload: OnboardingRejectionPayload): Promise<OnboardingRequestDetail> {
    const response = await apiClient.post<OnboardingRequestDetail>(`/api/v1/onboarding/requests/${id}/reject`, payload)
    return response.data
  },

  /**
   * Cancel onboarding request.
   */
  async cancelRequest(id: string, payload?: OnboardingCancellationPayload): Promise<OnboardingRequestDetail> {
    const response = await apiClient.post<OnboardingRequestDetail>(`/api/v1/onboarding/requests/${id}/cancel`, payload || {})
    return response.data
  },

  /**
   * Execute atomic tenant provisioning.
   */
  async provisionRequest(id: string): Promise<OnboardingProvisionResult> {
    const response = await apiClient.post<OnboardingProvisionResult>(`/api/v1/onboarding/requests/${id}/provision`)
    return response.data
  },
}
