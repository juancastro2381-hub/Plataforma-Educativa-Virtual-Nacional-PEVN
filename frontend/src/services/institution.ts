/**
 * PEVN Frontend — Institution Provisioning & Rector Invitation API Service
 *
 * Encapsulates all backend HTTP calls related to:
 *   - National institutional catalog listing, filtering, and pagination
 *   - Institutional provisioning with automatic Sede Principal creation
 *   - Operational status lifecycle transitions (active/suspended)
 *   - Cryptographic single-use rector invitation generation and dispatch
 */

import apiClient from '@/services/api/client'
import type {
  InstitutionCreateRequest,
  InstitutionListResponse,
  InstitutionResponse,
  InstitutionStatusUpdateRequest,
  OfficialCatalogSyncRequest,
  OfficialCatalogSyncResponse,
  OfficialCatalogSyncStatus,
  OfficialInstitutionResolution,
  RectorInvitationCreateRequest,
  RectorInvitationResponse,
} from '@/types'

export interface ListInstitutionsParams {
  department_id?: string
  municipality_id?: string
  is_active?: boolean
  search?: string
  page?: number
  page_size?: number
}

export const institutionApi = {
  /**
   * Provision a new educational institution with automatic Sede Principal.
   * Requires NATIONAL_ADMIN or SUPERADMIN role.
   */
  async createInstitution(
    payload: InstitutionCreateRequest
  ): Promise<InstitutionResponse> {
    const response = await apiClient.post<InstitutionResponse>(
      '/api/v1/institutions',
      payload
    )
    return response.data
  },

  /**
   * List educational institutions with search, status, and territorial filters.
   * Requires national scope.
   */
  async listInstitutions(
    params: ListInstitutionsParams = {}
  ): Promise<InstitutionListResponse> {
    const queryParams = new URLSearchParams()
    if (params.department_id) queryParams.set('department_id', params.department_id)
    if (params.municipality_id) queryParams.set('municipality_id', params.municipality_id)
    if (params.is_active !== undefined) queryParams.set('is_active', String(params.is_active))
    if (params.search && params.search.trim()) queryParams.set('search', params.search.trim())
    if (params.page) queryParams.set('page', String(params.page))
    if (params.page_size) queryParams.set('page_size', String(params.page_size))

    const url = `/api/v1/institutions${queryParams.toString() ? `?${queryParams.toString()}` : ''}`
    const response = await apiClient.get<InstitutionListResponse>(url)
    return response.data
  },

  /**
   * Update the operational status (active/suspended) of an educational institution.
   */
  async updateInstitutionStatus(
    institutionId: string,
    isActive: boolean
  ): Promise<InstitutionResponse> {
    const payload: InstitutionStatusUpdateRequest = { is_active: isActive }
    const response = await apiClient.patch<InstitutionResponse>(
      `/api/v1/institutions/${institutionId}/status`,
      payload
    )
    return response.data
  },

  /**
   * Issue a cryptographically secure single-use invitation for a new Rector.
   * Returns the raw invitation token / URL for one-time delivery.
   */
  async inviteRector(
    institutionId: string,
    payload: RectorInvitationCreateRequest
  ): Promise<RectorInvitationResponse> {
    const response = await apiClient.post<RectorInvitationResponse>(
      `/api/v1/institutions/${institutionId}/rector-invitation`,
      payload
    )
    return response.data
  },

  /**
   * Fetch current user's institution details.
   */
  async getMyInstitution(): Promise<InstitutionResponse> {
    const response = await apiClient.get<InstitutionResponse>(
      '/api/v1/institutions/me'
    )
    return response.data
  },

  /**
   * Fetch specific institution by ID.
   */
  async getInstitutionById(institutionId: string): Promise<InstitutionResponse> {
    const response = await apiClient.get<InstitutionResponse>(
      `/api/v1/institutions/${institutionId}`
    )
    return response.data
  },

  /**
   * Resolve authoritative Colombian educational entity data by 12-digit DANE code.
   * Queries PEvN official government catalog.
   */
  async resolveDaneInstitution(
    daneCode: string
  ): Promise<OfficialInstitutionResolution> {
    const response = await apiClient.get<OfficialInstitutionResolution>(
      `/api/v1/institutions/resolve-dane/${daneCode.trim()}`
    )
    return response.data
  },

  /**
   * Fetch official DANE/MEN catalog synchronization metrics, completeness, and freshness.
   */
  async getCatalogSyncStatus(): Promise<OfficialCatalogSyncStatus> {
    const response = await apiClient.get<OfficialCatalogSyncStatus>(
      '/api/v1/institutions/catalog/sync-status'
    )
    return response.data
  },

  /**
   * Trigger official national MEN/DANE catalog ingestion and synchronization.
   * Requires NATIONAL_ADMIN or SUPERADMIN role.
   */
  async syncNationalCatalog(
    payload: OfficialCatalogSyncRequest = {}
  ): Promise<OfficialCatalogSyncResponse> {
    const response = await apiClient.post<OfficialCatalogSyncResponse>(
      '/api/v1/institutions/catalog/sync',
      payload
    )
    return response.data
  },

  /**
   * Fetch promotion governance state machine status.
   */
  async getPromotionGovernanceStatus(): Promise<import('@/types').PromotionStatusGovernance> {
    const response = await apiClient.get<import('@/types').PromotionStatusGovernance>(
      '/api/v1/institutions/catalog/promotion/status'
    )
    return response.data
  },

  /**
   * Execute promotion preflight audit (Gates A-T evaluation).
   */
  async evaluatePromotionPreflight(): Promise<import('@/types').PromotionPreflightResponse> {
    const response = await apiClient.post<import('@/types').PromotionPreflightResponse>(
      '/api/v1/institutions/catalog/promotion/preflight'
    )
    return response.data
  },

  /**
   * Explicitly authorize national catalog promotion.
   */
  async authorizePromotion(
    payload: import('@/types').PromotionAuthorizationRequest
  ): Promise<import('@/types').PromotionAuthorizationResponse> {
    const response = await apiClient.post<import('@/types').PromotionAuthorizationResponse>(
      '/api/v1/institutions/catalog/promotion/authorize',
      payload
    )
    return response.data
  },

  /**
   * Execute dry-run simulation of catalog promotion without mutating data.
   */
  async executePromotionDryRun(): Promise<import('@/types').PromotionDryRunResponse> {
    const response = await apiClient.post<import('@/types').PromotionDryRunResponse>(
      '/api/v1/institutions/catalog/promotion/dry-run'
    )
    return response.data
  },

  /**
   * Execute controlled promotion to NATIONAL_CATALOG_SYNCED.
   */
  async executeControlledPromotion(
    payload: import('@/types').PromotionExecuteRequest
  ): Promise<import('@/types').PromotionExecuteResponse> {
    const response = await apiClient.post<import('@/types').PromotionExecuteResponse>(
      '/api/v1/institutions/catalog/promotion/execute',
      payload
    )
    return response.data
  },

  /**
   * Rollback promotion to previous snapshot.
   */
  async executePromotionRollback(
    payload: import('@/types').PromotionRollbackRequest
  ): Promise<import('@/types').PromotionRollbackResponse> {
    const response = await apiClient.post<import('@/types').PromotionRollbackResponse>(
      '/api/v1/institutions/catalog/promotion/rollback',
      payload
    )
    return response.data
  },

  /**
   * Query immutable promotion audit log.
   */
  async getPromotionAuditEvents(limit = 50): Promise<import('@/types').PromotionAuditEvent[]> {
    const response = await apiClient.get<import('@/types').PromotionAuditEvent[]>(
      `/api/v1/institutions/catalog/promotion/audit?limit=${limit}`
    )
    return response.data
  },

  /**
   * Execute final pre-authorization forensic certification audit (Gates U-AN).
   */
  async getFinalPreauthorizationCertification(): Promise<import('@/types').NationalCatalogFinalCertificationResponse> {
    const response = await apiClient.get<import('@/types').NationalCatalogFinalCertificationResponse>(
      '/api/v1/institutions/catalog/promotion/final-certification'
    )
    return response.data
  },
}

export default institutionApi
