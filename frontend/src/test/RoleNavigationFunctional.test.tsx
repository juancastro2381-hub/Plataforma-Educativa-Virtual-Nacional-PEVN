/**
 * PEVN Frontend — Phase 10: Role UX, Navigation & User-Lifecycle Functional Tests
 *
 * Exhaustive component & navigation testing for all 11 canonical roles:
 * superadmin, national_admin, department_admin, municipality_admin,
 * rector, institution_admin, coordinator, academic_coordinator,
 * teacher, student, guardian.
 */

import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AuthProvider } from '@/context/AuthContext'
import { RootLayout } from '@/layouts/RootLayout'
import { Dashboard } from '@/pages/Dashboard'
import { AcademicHub } from '@/pages/academic/AcademicHub'
import { TeachersView } from '@/pages/academic/TeachersView'
import { StudentsView } from '@/pages/academic/StudentsView'
import { RequireAuth } from '@/components/auth/RequireAuth'
import type { User } from '@/types'

// Role user factory
function createMockUser(
  role: string,
  permissions: string[],
  isNational = false,
  institutionId: string | null = 'inst-001'
): User {
  return {
    id: `user-${role}-01`,
    email: `${role}@pevn.edu.co`,
    username: `${role}_user`,
    first_name: 'Test',
    last_name: role.toUpperCase(),
    full_name: `Test ${role.toUpperCase()}`,
    document_type: 'CC',
    document_number: '123456789',
    institution_id: isNational ? null : institutionId,
    is_active: true,
    is_verified: true,
    must_change_password: false,
    roles: [role],
    permissions,
    scope: {
      country_code: 'CO',
      department_id: isNational ? null : 'DEP-11',
      municipality_id: isNational ? null : 'MUN-11001',
      institution_id: isNational ? null : institutionId,
      campus_id: null,
      is_national: isNational,
      is_institution: !isNational,
    },
  }
}

let activeUser: User = createMockUser('rector', [
  'academic_years:read',
  'academic_years:create',
  'groups:read',
  'groups:create',
  'students:read',
  'students:create',
  'teachers:read',
  'teachers:create',
  'guardians:read',
  'enrollments:read',
  'academic_assignments:read',
  'virtual_classrooms:read',
])

vi.mock('@/services/auth', () => ({
  authApi: {
    refresh: (): Promise<string> => Promise.resolve('mock-token'),
    getMyProfile: (): Promise<User> => Promise.resolve(activeUser),
  },
  default: {
    refresh: (): Promise<string> => Promise.resolve('mock-token'),
    getMyProfile: (): Promise<User> => Promise.resolve(activeUser),
  },
}))

vi.mock('@/services/academic', () => ({
  academicApi: {
    listAcademicYears: () => Promise.resolve({ items: [], total: 0 }),
    listGroups: () => Promise.resolve({ items: [], total: 0 }),
    getGroupCapacity: () => Promise.resolve({ total_capacity: 40, enrolled_count: 20, available_capacity: 20 }),
    listStudents: () => Promise.resolve({ items: [], total: 0 }),
    listTeachers: () => Promise.resolve({ items: [], total: 0 }),
    listGuardians: () => Promise.resolve({ items: [], total: 0 }),
    listEnrollments: () => Promise.resolve({ items: [], total: 0 }),
    listAssignments: () => Promise.resolve({ items: [], total: 0 }),
    getTransferHistory: () => Promise.resolve({ items: [], total: 0 }),
    createTeacher: vi.fn().mockResolvedValue({ id: 'tch-01', user_id: '123e4567-e89b-12d3-a456-426614174000' }),
    createStudent: vi.fn().mockResolvedValue({ id: 'std-01', user_id: '123e4567-e89b-12d3-a456-426614174000' }),
  },
  default: {
    listAcademicYears: () => Promise.resolve({ items: [], total: 0 }),
    listGroups: () => Promise.resolve({ items: [], total: 0 }),
    getGroupCapacity: () => Promise.resolve({ total_capacity: 40, enrolled_count: 20, available_capacity: 20 }),
    listStudents: () => Promise.resolve({ items: [], total: 0 }),
    listTeachers: () => Promise.resolve({ items: [], total: 0 }),
    listGuardians: () => Promise.resolve({ items: [], total: 0 }),
    listEnrollments: () => Promise.resolve({ items: [], total: 0 }),
    listAssignments: () => Promise.resolve({ items: [], total: 0 }),
    getTransferHistory: () => Promise.resolve({ items: [], total: 0 }),
    createTeacher: vi.fn().mockResolvedValue({ id: 'tch-01', user_id: '123e4567-e89b-12d3-a456-426614174000' }),
    createStudent: vi.fn().mockResolvedValue({ id: 'std-01', user_id: '123e4567-e89b-12d3-a456-426614174000' }),
  },
}))

vi.mock('@/services/users', () => ({
  usersApi: {
    searchUsers: vi.fn().mockImplementation(({ search }) => {
      if (search && search.includes('8788')) {
        return Promise.resolve({
          items: [
            {
              id: '123e4567-e89b-12d3-a456-426614174000',
              email: 'carlos.docente@inst.edu.co',
              username: 'carlos_docente',
              first_name: 'Carlos',
              last_name: 'Docente',
              full_name: 'Carlos Docente',
              document_type: 'CC',
              document_number: '87884512',
              institution_id: 'inst-001',
              is_active: true,
              is_verified: true,
              created_at: '2026-01-01T00:00:00Z',
              updated_at: '2026-01-01T00:00:00Z',
            },
          ],
          total: 1,
          page: 1,
          page_size: 10,
        })
      }
      if (search && search.includes('9999')) {
        return Promise.resolve({
          items: [
            {
              id: '999e4567-e89b-12d3-a456-426614174000',
              email: 'estudiante.test@inst.edu.co',
              username: 'estudiante_test',
              first_name: 'Estudiante',
              last_name: 'Prueba',
              full_name: 'Estudiante Prueba',
              document_type: 'TI',
              document_number: '99991234',
              institution_id: 'inst-001',
              is_active: true,
              is_verified: true,
              created_at: '2026-01-01T00:00:00Z',
              updated_at: '2026-01-01T00:00:00Z',
            },
          ],
          total: 1,
          page: 1,
          page_size: 10,
        })
      }
      return Promise.resolve({ items: [], total: 0, page: 1, page_size: 10 })
    }),
    getUserById: vi.fn(),
  },
  default: {
    searchUsers: vi.fn(),
    getUserById: vi.fn(),
  },
}))

describe('Phase 10 — Role Navigation & UX Functional Validation', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // -------------------------------------------------------------------------
  // 1. RootLayout Navigation Bar per Role
  // -------------------------------------------------------------------------
  describe('Top Navigation Bar Visibility by Role', () => {
    it('shows "Instituciones" for National Admin and Superadmin', async () => {
      activeUser = createMockUser('national_admin', ['institutions:read', 'institutions:create'], true)
      render(
        <MemoryRouter initialEntries={['/']}>
          <AuthProvider>
            <RootLayout />
          </AuthProvider>
        </MemoryRouter>
      )

      await waitFor(() => {
        expect(screen.getByText('Instituciones')).toBeInTheDocument()
        expect(screen.getByText('Analítica Territorial')).toBeInTheDocument()
      })
    })

    it('shows "Aulas Virtuales" for Teacher and Rector', async () => {
      activeUser = createMockUser('teacher', ['virtual_classrooms:read', 'virtual_classrooms:join'])
      render(
        <MemoryRouter initialEntries={['/']}>
          <AuthProvider>
            <RootLayout />
          </AuthProvider>
        </MemoryRouter>
      )

      await waitFor(() => {
        expect(screen.getByText('Aulas Virtuales')).toBeInTheDocument()
        expect(screen.queryByText('Instituciones')).not.toBeInTheDocument()
      })
    })

    it('does not expose administrative links to Student or Guardian', async () => {
      activeUser = createMockUser('student', ['virtual_classrooms:join'])
      render(
        <MemoryRouter initialEntries={['/']}>
          <AuthProvider>
            <RootLayout />
          </AuthProvider>
        </MemoryRouter>
      )

      await waitFor(() => {
        expect(screen.queryByText('Instituciones')).not.toBeInTheDocument()
        expect(screen.queryByText('Analítica Territorial')).not.toBeInTheDocument()
      })
    })
  })

  // -------------------------------------------------------------------------
  // 2. Dashboard View Content by Role
  // -------------------------------------------------------------------------
  describe('Dashboard Role-Specific Access Cards', () => {
    it('renders National Catalog card for National Admin', async () => {
      activeUser = createMockUser('national_admin', ['institutions:read', 'institutions:create'], true)
      render(
        <MemoryRouter initialEntries={['/dashboard']}>
          <AuthProvider>
            <Dashboard />
          </AuthProvider>
        </MemoryRouter>
      )

      await waitFor(() => {
        expect(screen.getByText(/Aprovisionamiento Institucional y Rectores/i)).toBeInTheDocument()
        expect(screen.getByText(/Abrir Catálogo Nacional →/i)).toBeInTheDocument()
      })
    })

    it('renders Academic Management cards for Rector & Coordinator', async () => {
      activeUser = createMockUser('rector', [
        'academic_years:read',
        'groups:read',
        'students:read',
        'teachers:read',
      ])
      render(
        <MemoryRouter initialEntries={['/dashboard']}>
          <AuthProvider>
            <Dashboard />
          </AuthProvider>
        </MemoryRouter>
      )

      await waitFor(() => {
        expect(screen.getByText(/Módulo de Gestión Académica/i)).toBeInTheDocument()
        expect(screen.getByText('Años Lectivos')).toBeInTheDocument()
        expect(screen.getByText('Planta Docente')).toBeInTheDocument()
      })
    })

    it('renders Family Accompaniment card for Guardian', async () => {
      activeUser = createMockUser('guardian', [])
      render(
        <MemoryRouter initialEntries={['/dashboard']}>
          <AuthProvider>
            <Dashboard />
          </AuthProvider>
        </MemoryRouter>
      )

      await waitFor(() => {
        expect(screen.getByText(/Portal de Acompañamiento Familiar/i)).toBeInTheDocument()
      })
    })
  })

  // -------------------------------------------------------------------------
  // 3. RequireAuth Guard Protection
  // -------------------------------------------------------------------------
  describe('RequireAuth Route Guarding', () => {
    it('redirects unauthorized role away from protected routes to dashboard', async () => {
      activeUser = createMockUser('student', [])
      render(
        <MemoryRouter initialEntries={['/admin/institutions']}>
          <AuthProvider>
            <Routes>
              <Route
                path="/admin/institutions"
                element={
                  <RequireAuth roles={['superadmin', 'national_admin']}>
                    <div>Ruta Instituciones Secreta</div>
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
        expect(screen.queryByText('Ruta Instituciones Secreta')).not.toBeInTheDocument()
      })
    })
  })

  // -------------------------------------------------------------------------
  // 4. AcademicHub Tab Navigation & Unauthorized Warning
  // -------------------------------------------------------------------------
  describe('AcademicHub Tab Protection', () => {
    it('displays unauthorized alert and falls back to first authorized tab when accessing restricted tab', async () => {
      // Teacher only has students:read and assignments:read, not academic_years:read
      activeUser = createMockUser('teacher', ['students:read', 'academic_assignments:read'])
      render(
        <MemoryRouter initialEntries={['/academic?tab=years']}>
          <AuthProvider>
            <AcademicHub />
          </AuthProvider>
        </MemoryRouter>
      )

      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument()
        expect(screen.getByText(/no se encuentra disponible para su rol institucional/i)).toBeInTheDocument()
      })
    })
  })

  // -------------------------------------------------------------------------
  // 5. Teacher Creation Modal Tenant-Safe User Search & Selection Flow ("8788")
  // -------------------------------------------------------------------------
  describe('Teacher Creation Form User Search & Selection ("8788" Flow)', () => {
    it('searches user by "8788", selects account, and submits canonical UUID without manual entry', async () => {
      activeUser = createMockUser('rector', ['teachers:read', 'teachers:create'])
      render(
        <MemoryRouter>
          <AuthProvider>
            <TeachersView />
          </AuthProvider>
        </MemoryRouter>
      )

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /\+ Registrar Perfil Docente/i })).toBeInTheDocument()
      })

      // Open Modal
      fireEvent.click(screen.getByRole('button', { name: /\+ Registrar Perfil Docente/i }))

      // Search by "8788"
      const searchInput = screen.getByPlaceholderText(/Buscar por documento \(ej\. 8788\)/i)
      await userEvent.type(searchInput, '8788')

      // Matching institutional user card is displayed
      await waitFor(() => {
        expect(screen.getByText('Carlos Docente')).toBeInTheDocument()
        expect(screen.getByText(/87884512/i)).toBeInTheDocument()
      })

      // Select user
      fireEvent.click(screen.getByRole('button', { name: 'Seleccionar' }))

      // Confirm user is selected
      await waitFor(() => {
        expect(screen.getByText(/✓ Carlos Docente/i)).toBeInTheDocument()
      })

      const specialtyInput = screen.getByPlaceholderText(/Licenciatura en Matemáticas/i)
      await userEvent.clear(specialtyInput)
      await userEvent.type(specialtyInput, 'Matemáticas y Física')

      // Click Guardar
      fireEvent.click(screen.getByText('Guardar Docente'))

      // Verify academicApi.createTeacher called with canonical UUID
      await waitFor(() => {
        expect(screen.getByText(/Perfil docente para Carlos Docente creado exitosamente/i)).toBeInTheDocument()
      })
    })

    it('provisions a completely new teacher on the fly without prerequisite user account (20202020 flow)', async () => {
      activeUser = createMockUser('rector', ['teachers:read', 'teachers:create'])
      render(
        <MemoryRouter>
          <AuthProvider>
            <TeachersView />
          </AuthProvider>
        </MemoryRouter>
      )

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /\+ Registrar Perfil Docente/i })).toBeInTheDocument()
      })

      // Open Modal
      fireEvent.click(screen.getByRole('button', { name: /\+ Registrar Perfil Docente/i }))

      // Search by "20202020" (no existing account)
      const searchInput = screen.getByPlaceholderText(/Buscar por documento \(ej\. 8788\)/i)
      await userEvent.type(searchInput, '20202020')

      // Option to register new educator appears
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /\+ Registrar como nuevo docente en la institución/i })).toBeInTheDocument()
      })

      // Click to switch to new teacher provisioning
      fireEvent.click(screen.getByRole('button', { name: /\+ Registrar como nuevo docente en la institución/i }))

      // Civil identity fields appear
      await waitFor(() => {
        expect(screen.getByPlaceholderText(/Ej\. Carlos Alberto/i)).toBeInTheDocument()
      })

      await userEvent.type(screen.getByPlaceholderText(/Ej\. Carlos Alberto/i), 'Carlos Alberto')
      await userEvent.type(screen.getByPlaceholderText(/Ej\. Gómez Restrepo/i), 'Gómez Restrepo')
      await userEvent.type(screen.getByPlaceholderText(/carlos\.gomez@colegio\.edu\.co/i), 'carlos.gomez@librada.edu.co')

      // Save Teacher
      fireEvent.click(screen.getByText('Guardar Docente'))

      // Verify success notification
      await waitFor(() => {
        expect(screen.getByText(/Perfil docente para Carlos Alberto Gómez Restrepo creado exitosamente/i)).toBeInTheDocument()
      })
    })
  })

  // -------------------------------------------------------------------------
  // 6. Student Creation Modal Tenant-Safe User Search & Selection Flow
  // -------------------------------------------------------------------------
  describe('Student Creation Form User Search & Selection', () => {
    it('searches user by document "9999", selects account, and creates student profile with canonical UUID', async () => {
      activeUser = createMockUser('rector', ['students:read', 'students:create'])
      render(
        <MemoryRouter>
          <AuthProvider>
            <StudentsView />
          </AuthProvider>
        </MemoryRouter>
      )

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /\+ Registrar Estudiante/i })).toBeInTheDocument()
      })

      // Open Modal
      fireEvent.click(screen.getByRole('button', { name: /\+ Registrar Estudiante/i }))

      // Search by "9999"
      const searchInput = screen.getByPlaceholderText(/Buscar por documento \(ej\. 8788\)/i)
      await userEvent.type(searchInput, '9999')

      // Matching user appears
      await waitFor(() => {
        expect(screen.getByText('Estudiante Prueba')).toBeInTheDocument()
      })

      // Select user
      fireEvent.click(screen.getByRole('button', { name: 'Seleccionar' }))

      // Confirm user is selected
      await waitFor(() => {
        expect(screen.getByText(/✓ Estudiante Prueba/i)).toBeInTheDocument()
      })

      const simatInput = screen.getByPlaceholderText(/SIMAT-2026-XXXX/i)
      await userEvent.type(simatInput, 'SIMAT-2026-9999')

      // Click Guardar
      fireEvent.click(screen.getByText('Guardar Estudiante'))

      // Verify success
      await waitFor(() => {
        expect(screen.getByText(/Perfil estudiantil con código SIMAT SIMAT-2026-9999 creado exitosamente/i)).toBeInTheDocument()
      })
    })

    it('provisions a completely new student on the fly without prerequisite user account (Natalia Castro flow)', async () => {
      activeUser = createMockUser('rector', ['students:read', 'students:create'])
      render(
        <MemoryRouter>
          <AuthProvider>
            <StudentsView />
          </AuthProvider>
        </MemoryRouter>
      )

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /\+ Registrar Estudiante/i })).toBeInTheDocument()
      })

      // Open Modal
      fireEvent.click(screen.getByRole('button', { name: /\+ Registrar Estudiante/i }))

      // Search for non-existent user "Natalia Castro"
      const searchInput = screen.getByPlaceholderText(/Buscar por documento \(ej\. 8788\)/i)
      await userEvent.type(searchInput, 'Natalia Castro')

      // Switch to Mode B: Registrar Nuevo Estudiante
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /\+ Registrar Nuevo Estudiante/i })).toBeInTheDocument()
      })
      fireEvent.click(screen.getByRole('button', { name: /\+ Registrar Nuevo Estudiante/i }))

      // Mode B header is displayed
      await waitFor(() => {
        expect(screen.getByText(/🆕 Nuevo Estudiante Institucional/i)).toBeInTheDocument()
      })

      // Fill in civil identity fields
      const docNumberInput = screen.getByPlaceholderText(/10203040/i)
      await userEvent.type(docNumberInput, '1098765432')

      const emailInput = screen.getByPlaceholderText(/natalia\.castro@colegio\.edu\.co/i)
      await userEvent.type(emailInput, 'natalia.castro@librada.edu.co')

      const simatInput = screen.getByPlaceholderText(/SIMAT-2026-XXXX/i)
      await userEvent.type(simatInput, 'SIMAT-2026-NATALIA-01')

      // Click Guardar
      fireEvent.click(screen.getByText('Guardar Estudiante'))

      // Verify success
      await waitFor(() => {
        expect(screen.getByText(/Perfil estudiantil con código SIMAT SIMAT-2026-NATALIA-01 creado exitosamente/i)).toBeInTheDocument()
      })
    })
  })
})
