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
