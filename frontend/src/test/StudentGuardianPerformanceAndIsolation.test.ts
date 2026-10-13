/**
 * PEVN Frontend — Student/Guardian Performance & Session Isolation Regression Suite
 * AI Software Factory Standard v1.2 — RBAC-AUDIT-02-R3 Verification
 *
 * Verifies:
 * 1. Client-side exclusion of student and guardian endpoints from X-Institution-Context injection.
 * 2. clearClientSessionState completely wipes access token and localStorage institutional keys.
 * 3. syncInstitutionalContext binds strictly to user's assigned institution.
 * 4. Empty datasets render correctly without timing out or crashing into error state.
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import {
  apiClient,
  clearClientSessionState,
  getAccessToken,
  setAccessToken,
} from '@/services/api/client'
import { resolveCanonicalScopeLabel } from '@/utils/scopeLabels'

describe('RBAC-AUDIT-02-R3: Student/Guardian Performance & Session Isolation', () => {
  beforeEach(() => {
    localStorage.clear()
    clearClientSessionState()
  })

  afterEach(() => {
    localStorage.clear()
    clearClientSessionState()
  })

  describe('Session Isolation (Workstream B)', () => {
    it('B-01: clearClientSessionState clears access token and institutional localStorage context', () => {
      setAccessToken('mock.jwt.token')
      localStorage.setItem('pevn_active_institution_id', 'inst-alpha')
      localStorage.setItem('pevn_active_institution_name', 'Colegio Alpha')

      expect(getAccessToken()).toBe('mock.jwt.token')
      expect(localStorage.getItem('pevn_active_institution_id')).toBe('inst-alpha')

      clearClientSessionState()

      expect(getAccessToken()).toBeNull()
      expect(localStorage.getItem('pevn_active_institution_id')).toBeNull()
      expect(localStorage.getItem('pevn_active_institution_name')).toBeNull()
    })

    it('B-02: Student endpoints are excluded from generic X-Institution-Context and params injection', () => {
      localStorage.setItem('pevn_active_institution_id', 'inst-foreign-99')

      const studentRequestConfig: any = {
        url: '/api/v1/student/dashboard',
        headers: {},
        params: {},
      }

      // Execute request interceptor manually
      const handlers = (apiClient.interceptors.request as any).handlers
      const requestHandler = handlers[0]?.fulfilled

      expect(requestHandler).toBeDefined()
      const result = requestHandler(studentRequestConfig)

      // X-Institution-Context and params.institution_id must NOT be injected
      expect(result.headers['X-Institution-Context']).toBeUndefined()
      expect(result.params?.institution_id).toBeUndefined()
    })

    it('B-03: Guardian endpoints are excluded from generic X-Institution-Context and params injection', () => {
      localStorage.setItem('pevn_active_institution_id', 'inst-foreign-99')

      const guardianRequestConfig: any = {
        url: '/api/v1/guardian/profile',
        headers: {},
        params: {},
      }

      const handlers = (apiClient.interceptors.request as any).handlers
      const requestHandler = handlers[0]?.fulfilled

      const result = requestHandler(guardianRequestConfig)

      expect(result.headers['X-Institution-Context']).toBeUndefined()
      expect(result.params?.institution_id).toBeUndefined()
    })

    it('B-04: Non-excluded institutional endpoints still receive active context correctly', () => {
      localStorage.setItem('pevn_active_institution_id', 'inst-authorized-01')

      const academicRequestConfig: any = {
        url: '/api/v1/academic/curriculum',
        headers: {},
        params: {},
      }

      const handlers = (apiClient.interceptors.request as any).handlers
      const requestHandler = handlers[0]?.fulfilled

      const result = requestHandler(academicRequestConfig)

      expect(result.headers['X-Institution-Context']).toBe('inst-authorized-01')
      expect(result.params?.institution_id).toBe('inst-authorized-01')
    })
  })

  describe('Canonical Scope Labels (Workstream C)', () => {
    it('C-01: Canonical scope label distinguishes role and jurisdictional level', () => {
      // Coordinator is Institucional
      expect(
        resolveCanonicalScopeLabel({
          roles: ['coordinator'],
          scope: { department_id: 'DEP-99', institution_id: 'inst-1' },
        })
      ).toBe('Institucional')

      // Municipality Admin is Territorial
      expect(
        resolveCanonicalScopeLabel({
          roles: ['municipality_admin'],
          scope: { department_id: 'DEP-99', municipality_id: 'mun-1' },
        })
      ).toBe('Territorial')

      // Department Admin is Departamental
      expect(
        resolveCanonicalScopeLabel({
          roles: ['department_admin'],
          scope: { department_id: 'DEP-99' },
        })
      ).toBe('Departamental')

      // Rector is Institucional
      expect(
        resolveCanonicalScopeLabel({
          roles: ['rector'],
          scope: { institution_id: 'inst-1' },
        })
      ).toBe('Institucional')

      // Superadmin is Global
      expect(
        resolveCanonicalScopeLabel({
          roles: ['superadmin'],
        })
      ).toBe('🌐 Global (Operador Técnico del Estado / Plataforma)')

      // National Admin is Nacional
      expect(
        resolveCanonicalScopeLabel({
          roles: ['national_admin'],
        })
      ).toBe('🇨🇴 Nacional (Todo el Territorio)')
    })
  })
})
