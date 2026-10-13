/**
 * PEVN Frontend — Canonical Scope Label Resolution Utilities
 * AI Software Factory Standard v1.2 — Workstream C Remediation
 *
 * Distinguishes role, numeric hierarchy, and canonical jurisdictional scope:
 *   - SUPERADMIN: Global (Operador Técnico del Estado / Plataforma)
 *   - NATIONAL_ADMIN: Nacional (Todo el Territorio)
 *   - DEPARTMENT_ADMIN: Departamental
 *   - MUNICIPALITY_ADMIN: Territorial
 *   - COORDINATOR / RECTOR / TEACHER / STUDENT / GUARDIAN: Institucional
 */

export interface CanonicalScopeUser {
  roles?: string[]
  scope?: {
    is_national?: boolean
    is_department?: boolean
    is_municipality?: boolean
    is_institution?: boolean
    department_id?: string | null
    municipality_id?: string | null
    institution_id?: string | null
    campus_id?: string | null
    jurisdiction_name?: string | null
    municipality_code?: string | null
    country_code?: string | null
  } | null
}

/**
 * Resolves the canonical human-readable scope label for a given user.
 *
 * Rules:
 * 1. SUPERADMIN -> Global
 * 2. NATIONAL_ADMIN / is_national -> Nacional
 * 3. DEPARTMENT_ADMIN -> Departamental
 * 4. MUNICIPALITY_ADMIN -> Territorial (Municipality within department)
 * 5. Institutional roles (coordinator, rector, teacher, student, guardian, auditor) -> Institucional
 * 6. Explicit boolean scope fallback if no recognized role matched
 * 7. Missing or unassigned -> 'No asignado'
 */
export function resolveCanonicalScopeLabel(
  user: CanonicalScopeUser | null | undefined
): string {
  if (!user) return 'No asignado'

  const userRoles = (user.roles || []).map((r) => r.toLowerCase())

  // 1. Global Platform Governance (Tier 100)
  if (userRoles.includes('superadmin') || userRoles.includes('super_admin')) {
    return '🌐 Global (Operador Técnico del Estado / Plataforma)'
  }

  // 2. National Territorial Governance (Tier 90)
  if (userRoles.includes('national_admin') || user.scope?.is_national) {
    return '🇨🇴 Nacional (Todo el Territorio)'
  }

  // 3. Departmental Territorial Governance (Tier 80)
  if (userRoles.includes('department_admin')) {
    return 'Departamental'
  }

  // 4. Municipal Territorial Governance (Tier 70)
  // Canonical requirement: MUNICIPALITY_ADMIN displayed scope is 'Territorial'
  if (userRoles.includes('municipality_admin')) {
    return 'Territorial'
  }

  // 5. Institutional Roles (Tiers 60, 50, 30, 25, 10)
  // Coordinator, Rector, Teacher, Auditor, Student, Guardian
  const institutionalRoles = [
    'coordinator',
    'academic_coordinator',
    'rector',
    'institution_admin',
    'teacher',
    'auditor',
    'student',
    'guardian',
  ]
  if (userRoles.some((r) => institutionalRoles.includes(r))) {
    return 'Institucional'
  }

  // 6. Explicit Scope Flag Fallbacks (when user roles are empty or non-canonical)
  if (user.scope?.is_department) {
    return 'Departamental'
  }
  if (user.scope?.is_municipality) {
    return 'Territorial'
  }
  if (user.scope?.is_institution || user.scope?.institution_id) {
    return 'Institucional'
  }

  return 'No asignado'
}
