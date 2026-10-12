/**
 * PEVN Frontend — System Operations & Platform Observability API Service
 *
 * Dedicated service for SUPER_ADMIN (Level 100) technical operations:
 *   - Live platform overview & latency telemetry
 *   - Comprehensive multi-tier health probe
 *   - Real-time security audit log stream
 *   - Technical incident & support ticket lifecycle
 *   - Institutional tenant diagnostics with audited access
 *   - Integration connectivity catalog
 */

import apiClient from '@/services/api/client'

export interface PlatformOverviewResponse {
  overall_status: 'OPERATIONAL' | 'DEGRADED' | 'OUTAGE'
  measured_at: string
  environment: string
  version: string
  database: {
    status: string
    latency_ms: number
    pool_size: number
    safe_url: string
  }
  redis: {
    status: string
    mode: string
  }
  background_jobs: {
    status: string
    active_queues: string[]
  }
  metrics: {
    active_incidents: number
    security_events_24h: number
  }
}

export interface PlatformHealthServiceItem {
  name: string
  status: string
  type: string
  details: string
}

export interface PlatformHealthResponse {
  status: string
  timestamp: string
  services: PlatformHealthServiceItem[]
}

export interface AuditFeedItem {
  id: string
  event_type: string
  actor_id: string | null
  actor_ip: string
  target_type: string | null
  target_id: string | null
  institution_id: string | null
  success: boolean
  metadata: Record<string, unknown>
  occurred_at: string | null
}

export interface AuditFeedResponse {
  items: AuditFeedItem[]
  total: number
  summary: {
    total_queried: number
    failed_logins: number
    permission_denied: number
    suspicious_events: number
  }
}

export interface TechnicalIncident {
  id: string
  ticket_number: string
  title: string
  category: string
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'
  status: 'OPEN' | 'INVESTIGATING' | 'MITIGATED' | 'RESOLVED' | 'CLOSED'
  affected_service: string
  institution_id: string | null
  institution_name?: string | null
  reporter_id: string | null
  assigned_operator: string | null
  description: string
  technical_context: Record<string, unknown> | null
  resolution_notes: string | null
  created_at: string
  updated_at: string
  resolved_at: string | null
}

export interface TechnicalIncidentListResponse {
  items: TechnicalIncident[]
  total: number
  open_count: number
  critical_count: number
}

export interface TechnicalIncidentCreatePayload {
  title: string
  category: string
  severity: string
  affected_service: string
  institution_id?: string | null
  description: string
  technical_context?: Record<string, unknown> | null
  assigned_operator?: string | null
}

export interface TechnicalIncidentUpdatePayload {
  status?: string | null
  severity?: string | null
  assigned_operator?: string | null
  resolution_notes?: string | null
}

export interface TenantDiagnosticsResponse {
  institution_id: string
  name: string
  dane_code: string
  is_active: boolean
  created_at: string | null
  telemetry: {
    campuses_count: number
    campuses: Array<{ id: string; name: string; dane_code: string }>
    total_users: number
    active_users: number
    locked_users: number
    configuration_status: string
  }
  audited_at: string
}

export interface PlatformIntegrationsResponse {
  integrations: Array<{
    name: string
    type: string
    endpoint?: string
    safe_host?: string
    status: string
    auth_type?: string
    pool_size?: number
  }>
}

export const operationsApi = {
  /**
   * Fetch high-level platform telemetry and operational health overview.
   */
  async getOverview(): Promise<PlatformOverviewResponse> {
    const res = await apiClient.get<PlatformOverviewResponse>('/api/v1/system/operations/overview')
    return res.data
  },

  /**
   * Run detailed multi-tier infrastructure health probe.
   */
  async getHealth(): Promise<PlatformHealthResponse> {
    const res = await apiClient.get<PlatformHealthResponse>('/api/v1/system/operations/health')
    return res.data
  },

  /**
   * Fetch real security audit log stream.
   */
  async getAuditFeed(params: { limit?: number; offset?: number; only_security?: boolean } = {}): Promise<AuditFeedResponse> {
    const res = await apiClient.get<AuditFeedResponse>('/api/v1/system/operations/audit-feed', {
      params: {
        limit: params.limit ?? 50,
        offset: params.offset ?? 0,
        only_security: params.only_security ?? true,
      },
    })
    return res.data
  },

  /**
   * List technical support cases and operational incidents.
   */
  async listSupportCases(params: { status?: string; severity?: string; limit?: number; offset?: number } = {}): Promise<TechnicalIncidentListResponse> {
    const res = await apiClient.get<TechnicalIncidentListResponse>('/api/v1/system/operations/support-cases', {
      params,
    })
    return res.data
  },

  /**
   * Create a new technical incident ticket.
   */
  async createSupportCase(payload: TechnicalIncidentCreatePayload): Promise<TechnicalIncident> {
    const res = await apiClient.post<TechnicalIncident>('/api/v1/system/operations/support-cases', payload)
    return res.data
  },

  /**
   * Update lifecycle status or resolution notes of an incident.
   */
  async updateSupportCase(caseId: string, payload: TechnicalIncidentUpdatePayload): Promise<TechnicalIncident> {
    const res = await apiClient.patch<TechnicalIncident>(`/api/v1/system/operations/support-cases/${caseId}`, payload)
    return res.data
  },

  /**
   * Run audited diagnostic probe on a specific educational tenant.
   */
  async getTenantDiagnostics(institutionId: string): Promise<TenantDiagnosticsResponse> {
    const res = await apiClient.get<TenantDiagnosticsResponse>(`/api/v1/system/operations/tenant-diagnostics/${institutionId}`)
    return res.data
  },

  /**
   * List configured platform integrations.
   */
  async getIntegrations(): Promise<PlatformIntegrationsResponse> {
    const res = await apiClient.get<PlatformIntegrationsResponse>('/api/v1/system/operations/integrations')
    return res.data
  },
}
