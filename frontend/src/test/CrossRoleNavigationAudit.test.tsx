/**
 * PEVN Frontend — RBAC-AUDIT-02: Cross-Role Navigation & Context Guard Tests
 *
 * Automated regression verification for:
 * - DEPARTMENT_ADMIN & MUNICIPALITY_ADMIN territorial context requirements
 * - returnTo preservation and seamless navigation upon context activation
 * - Role-to-route protection for /academic and /virtual-classrooms
 * - Anti-Open-Redirect sanitization
 * - Role isolation and unauthorized access blocking
 */

import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AuthProvider } from '@/context/AuthContext'
import { RequireAuth } from '@/components/auth/RequireAuth'
import { AcademicHub } from '@/pages/academic/AcademicHub'
import { InstitutionsView } from '@/pages/admin/InstitutionsView'
import type { User } from '@/types'

// Mock User Factory
function createTerritorialUser(
  role: 'department_admin' | 'municipality_admin' | 'student' | 'superadmin' | 'rector',
  deptId: string | null = 'DEP-99',
  muniId: string | null = 'MUN-99001'
): User {
  return {
    id: `user-${role}-test`,
    email: `${role}@territorio.gov.co`,
    username: `${role}_test`,
    first_name: 'Luis',
    last_name: role === 'municipality_admin' ? 'Soto' : 'Gomez',
    full_name: `${role} test`,
    document_type: 'CC',
    document_number: '987654321',
    institution_id: role === 'rector' ? 'inst-ptocarreno-01' : null,
    is_active: true,
    is_verified: true,
    must_change_password: false,
    roles: [role],
    permissions:
      role === 'student'
        ? ['students:read']
        : role === 'superadmin'
        ? ['*:*']
        : [
            'institutions:read',
            'academic_years:read',
            'academic_periods:read',
            'grades:read',
            'subjects:read',
            'groups:read',
            'teachers:read',
            'students:read',
            'guardians:read',
            'enrollments:read',
            'academic_assignments:read',
            'virtual_classrooms:read',
            'communications:read',
            'news:read',
            'incidents:read',
          ],
    scope: {
      country_code: 'CO',
      department_id: deptId,
      municipality_id: muniId,
      institution_id: role === 'rector' ? 'inst-ptocarreno-01' : null,
      campus_id: null,
      is_national: false,
      is_department: Boolean(deptId && !muniId),
      is_municipality: Boolean(muniId),
      is_institution: role === 'rector',
    },
  }
}

const { getActiveMockUser, setActiveMockUser, mockInstitutions } = vi.hoisted(() => {
  const institutions = [
    {
      id: 'inst-ptocarreno-01',
      dane_code: '199001000111',
      name: 'Colegio Eduardo Carranza',
      email: 'contacto@carranza.edu.co',
      phone: '3100000000',
      address: 'Calle 10 # 5-20',
      municipality_id: 'MUN-99001',
      is_active: true,
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
      main_campus_name: 'Sede Principal',
      campuses: [],
    },
  ]
  let currentUser: any = null
  return {
    getActiveMockUser: () => currentUser,
    setActiveMockUser: (u: any) => { currentUser = u },
    mockInstitutions: institutions,
  }
})

vi.mock('@/services/auth', () => ({
  authApi: {
    refresh: () => Promise.resolve('mock-token'),
    getMyProfile: () => Promise.resolve(getActiveMockUser()),
  },
  default: {
    refresh: () => Promise.resolve('mock-token'),
    getMyProfile: () => Promise.resolve(getActiveMockUser()),
  },
}))

vi.mock('@/services/institution', () => ({
  institutionApi: {
    listInstitutions: vi.fn().mockImplementation(() => Promise.resolve({ items: mockInstitutions, total: 1 })),
    listOfficialCatalog: vi.fn().mockImplementation(() => Promise.resolve({
      items: [
        {
          id: 'cat-01',
          dane_code: '199001000111',
          name: 'Colegio Eduardo Carranza',
          department: 'VICHADA',
          municipality: 'PUERTO CARREÑO',
          is_provisioned: true,
          institution_id: 'inst-ptocarreno-01',
          campuses_count: 1,
        },
      ],
      total: 1,
      summary: { total_catalog: 1, provisioned_count: 1, unprovisioned_count: 0 },
    })),
    getCatalogSyncStatus: vi.fn().mockImplementation(() => Promise.resolve({ is_stale: false })),
    getMyInstitution: vi.fn().mockImplementation(() => Promise.resolve(mockInstitutions[0])),
  },
  default: {
    listInstitutions: vi.fn().mockImplementation(() => Promise.resolve({ items: mockInstitutions, total: 1 })),
    listOfficialCatalog: vi.fn().mockImplementation(() => Promise.resolve({ items: [], total: 0 })),
    getCatalogSyncStatus: vi.fn().mockImplementation(() => Promise.resolve({ is_stale: false })),
  },
}))

vi.mock('@/services/academic', () => ({
  academicApi: {
    listAcademicYears: vi.fn().mockResolvedValue({ items: [], total: 0 }),
    listAcademicPeriods: vi.fn().mockResolvedValue({ items: [], total: 0 }),
    listGrades: vi.fn().mockResolvedValue({ items: [], total: 0 }),
    listSubjects: vi.fn().mockResolvedValue({ items: [], total: 0 }),
    listGroups: vi.fn().mockResolvedValue({ items: [], total: 0 }),
    listStudents: vi.fn().mockResolvedValue({ items: [], total: 0 }),
    listTeachers: vi.fn().mockResolvedValue({ items: [], total: 0 }),
    listGuardians: vi.fn().mockResolvedValue({ items: [], total: 0 }),
    listEnrollments: vi.fn().mockResolvedValue({ items: [], total: 0 }),
    listAssignments: vi.fn().mockResolvedValue({ items: [], total: 0 }),
  },
  default: {
    listAcademicYears: vi.fn().mockResolvedValue({ items: [], total: 0 }),
  },
}))

describe('RBAC-AUDIT-02: Cross-Role Navigation & Context Protection Suites', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.clearAllMocks()
  })

  it('1. MUNICIPALITY_ADMIN navigating to /academic is denied and redirected to /dashboard', async () => {
    setActiveMockUser(createTerritorialUser('municipality_admin'))

    render(
      <MemoryRouter initialEntries={['/academic']}>
        <AuthProvider>
          <Routes>
            <Route
              path="/academic"
              element={
                <RequireAuth
                  roles={['rector', 'institution_admin', 'coordinator', 'academic_coordinator']}
                  requireInstitutionContext
                >
                  <div>Vista Académica Protegida</div>
                </RequireAuth>
              }
            />
            <Route path="/dashboard" element={<div>Dashboard Redirección Exitosa</div>} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Dashboard Redirección Exitosa')).toBeInTheDocument()
      expect(screen.queryByText('Vista Académica Protegida')).not.toBeInTheDocument()
    })
  })

  it('2. DEPARTMENT_ADMIN navigating to /virtual-classrooms without context is redirected preserving returnTo', async () => {
    setActiveMockUser(createTerritorialUser('department_admin'))

    render(
      <MemoryRouter initialEntries={['/virtual-classrooms']}>
        <AuthProvider>
          <Routes>
            <Route
              path="/virtual-classrooms"
              element={
                <RequireAuth permissions={['virtual_classrooms:read']} requireInstitutionContext>
                  <div>Aulas Virtuales</div>
                </RequireAuth>
              }
            />
            <Route
              path="/admin/institutions"
              element={<InstitutionsView />}
            />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/Selección de Contexto Requerida/i)).toBeInTheDocument()
      expect(screen.getByText(/\/virtual-classrooms/i)).toBeInTheDocument()
    })
  })

  it('3. DEPARTMENT_ADMIN navigating to /academic is denied and redirected to /dashboard even with active context', async () => {
    setActiveMockUser(createTerritorialUser('department_admin'))
    localStorage.setItem('pevn_active_institution_id', 'inst-ptocarreno-01')
    localStorage.setItem('pevn_active_institution_name', 'Colegio Eduardo Carranza')

    render(
      <MemoryRouter initialEntries={['/academic']}>
        <AuthProvider>
          <Routes>
            <Route
              path="/academic"
              element={
                <RequireAuth
                  roles={['rector', 'institution_admin', 'coordinator', 'academic_coordinator']}
                  requireInstitutionContext
                >
                  <AcademicHub />
                </RequireAuth>
              }
            />
            <Route path="/dashboard" element={<div>Dashboard Redirección Exitosa</div>} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Dashboard Redirección Exitosa')).toBeInTheDocument()
      expect(screen.queryByText(/Gestión Académica e Institucional/i)).not.toBeInTheDocument()
    })
  })

  it('4. RECTOR with active context in localStorage successfully renders AcademicHub', async () => {
    setActiveMockUser(createTerritorialUser('rector', null, null))
    localStorage.setItem('pevn_active_institution_id', 'inst-ptocarreno-01')

    render(
      <MemoryRouter initialEntries={['/academic']}>
        <AuthProvider>
          <Routes>
            <Route
              path="/academic"
              element={
                <RequireAuth
                  roles={['rector', 'institution_admin', 'coordinator', 'academic_coordinator']}
                  requireInstitutionContext
                >
                  <AcademicHub />
                </RequireAuth>
              }
            />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/Gestión Académica e Institucional/i)).toBeInTheDocument()
    })
  })

  it('5. InstitutionsView on contextRequired defaults activeTab to tenants and renders Context button', async () => {
    setActiveMockUser(createTerritorialUser('municipality_admin'))

    render(
      <MemoryRouter initialEntries={['/admin/institutions?contextRequired=true&returnTo=%2Facademic']}>
        <AuthProvider>
          <InstitutionsView />
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/Colegios Aprovisionados \(Tenants\)/i)).toBeInTheDocument()
      expect(screen.getByText('Colegio Eduardo Carranza')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /contexto/i })).toBeInTheDocument()
    })
  })

  it('6. Clicking 🏛️ Contexto in InstitutionsView sets context and navigates to returnTo', async () => {
    setActiveMockUser(createTerritorialUser('municipality_admin'))

    render(
      <MemoryRouter initialEntries={['/admin/institutions?contextRequired=true&returnTo=%2Facademic']}>
        <AuthProvider>
          <Routes>
            <Route path="/admin/institutions" element={<InstitutionsView />} />
            <Route path="/academic" element={<div>Destino Académico Alcanzado Exitosamente</div>} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    )

    // Wait for the button to be stably present, click it, and verify navigation to returnTo
    await waitFor(
      () => {
        const btn = screen.getByRole('button', { name: /contexto/i })
        fireEvent.click(btn)
        expect(screen.getByText('Destino Académico Alcanzado Exitosamente')).toBeInTheDocument()
      },
      { timeout: 5000 }
    )
  })

  it('7. Malicious returnTo parameter (//evil.com or http:) is ignored by InstitutionsView', async () => {
    setActiveMockUser(createTerritorialUser('municipality_admin'))

    render(
      <MemoryRouter initialEntries={['/admin/institutions?contextRequired=true&returnTo=%2F%2Fevil.com']}>
        <AuthProvider>
          <InstitutionsView />
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      // Must not display or bind the malicious protocol-relative URL
      expect(screen.queryByText('//evil.com')).not.toBeInTheDocument()
      expect(screen.getByText(/los módulos de Gestión Académica y Aulas Virtuales/i)).toBeInTheDocument()
    })
  })

  it('8. Unauthorized role (student) attempting direct URL to /admin/institutions is redirected to /dashboard', async () => {
    setActiveMockUser(createTerritorialUser('student'))

    render(
      <MemoryRouter initialEntries={['/admin/institutions']}>
        <AuthProvider>
          <Routes>
            <Route
              path="/admin/institutions"
              element={
                <RequireAuth permissions={['institutions:read']}>
                  <div>Catálogo Institucional Secreto</div>
                </RequireAuth>
              }
            />
            <Route path="/dashboard" element={<div>Dashboard Estudiante Seguro</div>} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Dashboard Estudiante Seguro')).toBeInTheDocument()
      expect(screen.queryByText('Catálogo Institucional Secreto')).not.toBeInTheDocument()
    })
  })

  it('9. Unauthorized role (municipality_admin) attempting direct URL to SuperAdmin /operations/health is denied', async () => {
    setActiveMockUser(createTerritorialUser('municipality_admin'))

    render(
      <MemoryRouter initialEntries={['/operations/health']}>
        <AuthProvider>
          <Routes>
            <Route
              path="/operations/health"
              element={
                <RequireAuth roles={['superadmin', 'super_admin']}>
                  <div>Consola Salud Plataforma</div>
                </RequireAuth>
              }
            />
            <Route path="/dashboard" element={<div>Dashboard Redirección</div>} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Dashboard Redirección')).toBeInTheDocument()
      expect(screen.queryByText('Consola Salud Plataforma')).not.toBeInTheDocument()
    })
  })
})
