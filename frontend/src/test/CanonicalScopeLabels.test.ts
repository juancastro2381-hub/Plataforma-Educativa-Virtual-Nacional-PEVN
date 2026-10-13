/**
 * PEVN Frontend — Canonical Scope Labels Regression Suite
 * AI Software Factory Standard v1.2 — Workstream C Verification
 *
 * Verifies that the canonical presentation correctly distinguishes:
 * 1. COORDINATOR -> 'Institucional'
 * 2. MUNICIPALITY_ADMIN -> 'Territorial'
 * 3. DEPARTMENT_ADMIN -> 'Departamental'
 * 4. RECTOR / INSTITUTION_ADMIN -> 'Institucional'
 * 5. SUPERADMIN -> '🌐 Global (Operador Técnico del Estado / Plataforma)'
 * 6. NATIONAL_ADMIN -> '🇨🇴 Nacional (Todo el Territorio)'
 * 7. TEACHER, STUDENT, GUARDIAN -> 'Institucional'
 * 8. Missing / unassigned -> 'No asignado'
 */

import { describe, it, expect } from 'vitest'
import { resolveCanonicalScopeLabel } from '@/utils/scopeLabels'

describe('Canonical Scope Label Presentation (Workstream C)', () => {
  it('1. COORDINATOR displays "Institucional" even with enclosing department_id', () => {
    const coordinatorUser = {
      roles: ['coordinator'],
      scope: {
        is_national: false,
        is_department: false,
        is_municipality: false,
        is_institution: true,
        department_id: 'DEP-99', // Enclosing department must NOT mislabel as Departamental
        institution_id: 'inst-carranza-01',
        jurisdiction_name: 'Colegio Eduardo Carranza',
      },
    }
    expect(resolveCanonicalScopeLabel(coordinatorUser)).toBe('Institucional')

    const academicCoordinatorUser = {
      roles: ['academic_coordinator'],
      scope: {
        is_national: false,
        is_department: false,
        is_municipality: false,
        is_institution: true,
        department_id: 'DEP-99',
        institution_id: 'inst-carranza-01',
      },
    }
    expect(resolveCanonicalScopeLabel(academicCoordinatorUser)).toBe('Institucional')
  })

  it('2. MUNICIPALITY_ADMIN displays "Territorial"', () => {
    const municipalityAdminUser = {
      roles: ['municipality_admin'],
      scope: {
        is_national: false,
        is_department: false,
        is_municipality: true,
        is_institution: false,
        department_id: 'DEP-99', // Municipality is located within department DEP-99
        municipality_id: 'mun-puerto-carreno',
        municipality_code: '99001',
        jurisdiction_name: 'Puerto Carreño',
      },
    }
    expect(resolveCanonicalScopeLabel(municipalityAdminUser)).toBe('Territorial')
  })

  it('3. DEPARTMENT_ADMIN continues displaying "Departamental"', () => {
    const departmentAdminUser = {
      roles: ['department_admin'],
      scope: {
        is_national: false,
        is_department: true,
        is_municipality: false,
        is_institution: false,
        department_id: 'DEP-99',
        jurisdiction_name: 'Vichada',
      },
    }
    expect(resolveCanonicalScopeLabel(departmentAdminUser)).toBe('Departamental')
  })

  it('4. Rector remains institution-scoped ("Institucional")', () => {
    const rectorUser = {
      roles: ['rector'],
      scope: {
        is_national: false,
        is_department: false,
        is_municipality: false,
        is_institution: true,
        department_id: 'DEP-99',
        institution_id: 'inst-carranza-01',
        jurisdiction_name: 'Colegio Eduardo Carranza',
      },
    }
    expect(resolveCanonicalScopeLabel(rectorUser)).toBe('Institucional')

    const institutionAdminUser = {
      roles: ['institution_admin'],
      scope: {
        is_national: false,
        is_department: false,
        is_municipality: false,
        is_institution: true,
        institution_id: 'inst-carranza-01',
      },
    }
    expect(resolveCanonicalScopeLabel(institutionAdminUser)).toBe('Institucional')
  })

  it('5. SUPERADMIN and NATIONAL_ADMIN retain global / national presentation', () => {
    const superadminUser = {
      roles: ['superadmin'],
      scope: {
        is_national: true,
        country_code: 'CO',
      },
    }
    expect(resolveCanonicalScopeLabel(superadminUser)).toBe(
      '🌐 Global (Operador Técnico del Estado / Plataforma)'
    )

    const nationalAdminUser = {
      roles: ['national_admin'],
      scope: {
        is_national: true,
        country_code: 'CO',
      },
    }
    expect(resolveCanonicalScopeLabel(nationalAdminUser)).toBe(
      '🇨🇴 Nacional (Todo el Territorio)'
    )
  })

  it('6. Teacher, Student, Guardian display "Institucional"', () => {
    expect(resolveCanonicalScopeLabel({ roles: ['teacher'], scope: { institution_id: 'inst-1' } })).toBe('Institucional')
    expect(resolveCanonicalScopeLabel({ roles: ['student'], scope: { institution_id: 'inst-1' } })).toBe('Institucional')
    expect(resolveCanonicalScopeLabel({ roles: ['guardian'], scope: { institution_id: 'inst-1' } })).toBe('Institucional')
  })

  it('7. Handles missing, null, or unknown scope gracefully', () => {
    expect(resolveCanonicalScopeLabel(null)).toBe('No asignado')
    expect(resolveCanonicalScopeLabel(undefined)).toBe('No asignado')
    expect(resolveCanonicalScopeLabel({ roles: [] })).toBe('No asignado')
  })
})
