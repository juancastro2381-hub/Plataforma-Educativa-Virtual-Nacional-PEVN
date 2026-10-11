/**
 * PEVN Frontend — Territorial Analytics Types
 *
 * Defines TypeScript interfaces matching the backend Territorial Analytics schemas.
 */

export interface TerritorialSectorBreakdown {
  official: number
  non_official: number
}

export interface TerritorialZoneBreakdown {
  urban: number
  rural: number
}

export interface TerritorialSummaryResponse {
  scope_level: string
  jurisdiction_name: string
  total_departments: number
  total_municipalities: number
  total_institutions: number
  provisioned_institutions: number
  provisioning_rate_percent: number
  total_campuses: number
  active_students: number
  active_teachers: number
  active_groups: number
  sector_breakdown: TerritorialSectorBreakdown
  zone_breakdown: TerritorialZoneBreakdown
  computed_at: string
}

export interface DepartmentAnalyticsItem {
  department_code: string
  department_name: string
  total_municipalities: number
  total_institutions: number
  official_institutions: number
  non_official_institutions: number
  total_campuses: number
  provisioned_institutions: number
}

export interface DepartmentAnalyticsResponse {
  items: DepartmentAnalyticsItem[]
  total_count: number
  computed_at: string
}

export interface MunicipalityAnalyticsItem {
  municipality_code: string
  municipality_name: string
  department_code: string
  department_name: string
  total_institutions: number
  official_institutions: number
  non_official_institutions: number
  total_campuses: number
  provisioned_institutions: number
}

export interface MunicipalityAnalyticsResponse {
  department_code: string | null
  items: MunicipalityAnalyticsItem[]
  total_count: number
  computed_at: string
}

export interface InstitutionalKPIResponse {
  institution_id: string
  dane_code: string
  name: string
  department_name: string
  municipality_name: string
  total_campuses: number
  total_groups: number
  total_students: number
  total_teachers: number
  total_enrollments: number
  computed_at: string
}

// ---------------------------------------------------------------------------
// NTA-05 Territorial Control Center Types
// ---------------------------------------------------------------------------

export interface Tier1CatalogMetrics {
  total_departments: number
  total_municipalities: number
  total_establishments: number
  total_campuses: number
  official_sector_count: number
  non_official_sector_count: number
  urban_zone_count: number
  rural_zone_count: number
}

export interface Tier2PipelineMetrics {
  total_requests: number
  submitted: number
  under_review: number
  approved: number
  provisioned: number
  rejected: number
  cancelled: number
}

export interface Tier3TenancyMetrics {
  total_institutions: number
  active_institutions: number
  inactive_institutions: number
  catalog_linked_institutions: number
  synthetic_fixture_institutions: number
  provisioned_campuses: number
  active_operational_campuses: number
  total_users: number
  active_students: number
  active_teachers: number
}

export interface Tier4GovernanceMetrics {
  total_departments: number
  department_admin_users_count: number
  covered_departments: number
  vacant_departments: number
  pending_invitations: number
  coverage_percentage: number
}

export type DepartmentAdminStatus = 'COVERED' | 'INVITED' | 'VACANT'

export interface DepartmentMatrixRow {
  department_id: string
  department_code: string
  department_name: string
  governance_status: DepartmentAdminStatus | string
  admin_name: string | null
  admin_email: string | null
  total_establishments: number
  total_campuses: number
  pipeline_in_progress: number
  active_institutions: number
  inactive_institutions: number
  provisioning_rate_percent: number
}

export interface TerritorialControlCenterResponse {
  scope_level: 'NATIONAL' | 'DEPARTMENT'
  jurisdiction_name: string
  tier1_catalog: Tier1CatalogMetrics
  tier2_pipeline: Tier2PipelineMetrics
  tier3_tenancy: Tier3TenancyMetrics
  tier4_governance: Tier4GovernanceMetrics
  department_matrix: DepartmentMatrixRow[]
  computed_at: string
}

export interface DepartmentMunicipalityRow {
  municipality_id: string
  municipality_code: string
  municipality_name: string
  total_establishments: number
  total_campuses: number
  active_institutions: number
  inactive_institutions: number
  pipeline_in_progress: number
}

export interface DepartmentDetailControlCenterResponse {
  department_id: string
  department_code: string
  department_name: string
  governance_status: DepartmentAdminStatus | string
  admin_name: string | null
  admin_email: string | null
  total_municipalities: number
  total_establishments: number
  total_campuses: number
  active_institutions: number
  inactive_institutions: number
  pipeline_in_progress: number
  municipalities: DepartmentMunicipalityRow[]
  computed_at: string
}
