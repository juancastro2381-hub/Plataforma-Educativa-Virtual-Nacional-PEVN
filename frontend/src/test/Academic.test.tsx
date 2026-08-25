/**
 * PEVN Frontend — Academic Management Unit / Component Tests
 *
 * Tests for Academic Hub, Academic Years, Groups, Capacity Inspector,
 * Students, Teachers, Guardians, Enrollments, Transfers, and Assignments.
 */

import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { AuthProvider } from '@/context/AuthContext'
import { AcademicHub } from '@/pages/academic/AcademicHub'
import { AcademicYearsView } from '@/pages/academic/AcademicYearsView'
import { GroupsView } from '@/pages/academic/GroupsView'
import { StudentsView } from '@/pages/academic/StudentsView'
import { TeachersView } from '@/pages/academic/TeachersView'
import { GuardiansView } from '@/pages/academic/GuardiansView'
import { EnrollmentsView } from '@/pages/academic/EnrollmentsView'
import { TransfersView } from '@/pages/academic/TransfersView'
import { AcademicAssignmentsView } from '@/pages/academic/AcademicAssignmentsView'
import type {
  AcademicAssignmentListResponse,
  AcademicYearListResponse,
  EnrollmentListResponse,
  GroupCapacityResponse,
  GroupListResponse,
  GuardianListResponse,
  RefreshTokenResponse,
  StudentListResponse,
  TeacherListResponse,
  User,
} from '@/types'

const mockAdminUser: User = {
  id: 'u-admin-01',
  email: 'rector@pevn.edu.co',
  username: 'rector1',
  first_name: 'Ana',
  last_name: 'Martínez',
  full_name: 'Ana Martínez',
  document_type: 'CC',
  document_number: '98765432',
  institution_id: 'inst-001',
  is_active: true,
  is_verified: true,
  must_change_password: false,
  roles: ['rector'],
  permissions: ['*'],
  scope: {
    country_code: 'CO',
    department_id: 'DEP-11',
    municipality_id: 'MUN-11001',
    institution_id: 'inst-001',
    campus_id: null,
    is_national: false,
    is_institution: true,
  },
}

// Mock auth service
vi.mock('@/services/auth', () => ({
  authApi: {
    refresh: (): Promise<RefreshTokenResponse> =>
      Promise.resolve({
        access_token: 'mock-token',
        token_type: 'bearer',
        expires_in: 900,
        user: mockAdminUser,
      }),
  },
  default: {
    refresh: (): Promise<RefreshTokenResponse> =>
      Promise.resolve({
        access_token: 'mock-token',
        token_type: 'bearer',
        expires_in: 900,
        user: mockAdminUser,
      }),
  },
}))

// Mock academic service
const mockListYears = vi.fn<() => Promise<AcademicYearListResponse>>()
const mockListGroups = vi.fn<() => Promise<GroupListResponse>>()
const mockGetCapacity = vi.fn<() => Promise<GroupCapacityResponse>>()
const mockListStudents = vi.fn<() => Promise<StudentListResponse>>()
const mockListTeachers = vi.fn<() => Promise<TeacherListResponse>>()
const mockListGuardians = vi.fn<() => Promise<GuardianListResponse>>()
const mockListEnrollments = vi.fn<() => Promise<EnrollmentListResponse>>()
const mockListAssignments = vi.fn<() => Promise<AcademicAssignmentListResponse>>()

vi.mock('@/services/academic', () => ({
  academicApi: {
    listAcademicYears: () => mockListYears(),
    listGroups: () => mockListGroups(),
    getGroupCapacity: () => mockGetCapacity(),
    listStudents: () => mockListStudents(),
    listTeachers: () => mockListTeachers(),
    listGuardians: () => mockListGuardians(),
    listEnrollments: () => mockListEnrollments(),
    listAssignments: () => mockListAssignments(),
    getTransferHistory: () => Promise.resolve({ items: [], total: 0 }),
  },
  default: {
    listAcademicYears: () => mockListYears(),
    listGroups: () => mockListGroups(),
    getGroupCapacity: () => mockGetCapacity(),
    listStudents: () => mockListStudents(),
    listTeachers: () => mockListTeachers(),
    listGuardians: () => mockListGuardians(),
    listEnrollments: () => mockListEnrollments(),
    listAssignments: () => mockListAssignments(),
    getTransferHistory: () => Promise.resolve({ items: [], total: 0 }),
  },
}))

describe('Academic Management Views', () => {
  beforeEach(() => {
    vi.clearAllMocks()

    mockListYears.mockResolvedValue({
      items: [
        {
          id: 'year-2026',
          institution_id: 'inst-001',
          year: 2026,
          name: 'Año Lectivo 2026',
          start_date: '2026-02-01',
          end_date: '2026-11-30',
          calendar_type: 'CALENDAR_A',
          status: 'ACTIVE',
          created_at: '2026-01-01T00:00:00Z',
          updated_at: '2026-01-01T00:00:00Z',
        },
      ],
      total: 1,
    })

    mockListGroups.mockResolvedValue({
      items: [
        {
          id: 'grp-1001',
          campus_id: 'camp-01',
          academic_year_id: 'year-2026',
          grade_id: 'grd-10',
          name: '10-01',
          shift: 'MANANA',
          capacity_limit: 35,
          group_director_teacher_id: 't-01',
          created_at: '2026-01-01T00:00:00Z',
          updated_at: '2026-01-01T00:00:00Z',
        },
      ],
      total: 1,
    })

    mockGetCapacity.mockResolvedValue({
      group_id: 'grp-1001',
      capacity_limit: 35,
      active_enrolled_count: 28,
      available_slots: 7,
    })

    mockListStudents.mockResolvedValue({
      items: [
        {
          id: 'std-001',
          user_id: 'u-std-01',
          institution_id: 'inst-001',
          code_simat: 'SIMAT-998877',
          birth_date: '2010-05-12',
          gender: 'M',
          blood_type: 'O+',
          stratum: 2,
          eps_health_provider: 'Sura',
          has_disability: false,
          disability_type: null,
          user: {
            id: 'u-std-01',
            email: 'std@pevn.edu.co',
            username: 'std01',
            first_name: 'Carlos',
            last_name: 'Pérez',
            full_name: 'Carlos Pérez',
            document_type: 'TI',
            document_number: '10203040',
            institution_id: 'inst-001',
            is_active: true,
            is_verified: true,
            must_change_password: false,
            roles: ['student'],
            permissions: [],
            scope: {
              country_code: 'CO',
              department_id: 'DEP-11',
              municipality_id: 'MUN-11001',
              institution_id: 'inst-001',
              campus_id: null,
              is_national: false,
              is_institution: true,
            },
          },
          created_at: '2026-01-01T00:00:00Z',
          updated_at: '2026-01-01T00:00:00Z',
        },
      ],
      total: 1,
    })

    mockListTeachers.mockResolvedValue({
      items: [
        {
          id: 'tea-001',
          user_id: 'u-tea-01',
          institution_id: 'inst-001',
          specialty_area: 'Matemáticas',
          contract_type: 'PROPIEDAD',
          escalafon_grade: '14',
          created_at: '2026-01-01T00:00:00Z',
          updated_at: '2026-01-01T00:00:00Z',
        },
      ],
      total: 1,
    })

    mockListGuardians.mockResolvedValue({
      items: [
        {
          id: 'grd-001',
          first_name: 'Marta',
          last_name: 'Gómez',
          document_type: 'CC',
          document_number: '52999888',
          phone: '3109876543',
          email: 'marta@example.com',
          address: 'Calle 10 # 5-20',
          relationship_type: 'MADRE',
          user_id: null,
          created_at: '2026-01-01T00:00:00Z',
          updated_at: '2026-01-01T00:00:00Z',
        },
      ],
      total: 1,
    })

    mockListEnrollments.mockResolvedValue({
      items: [
        {
          id: 'enr-001',
          student_id: 'std-001',
          group_id: 'grp-1001',
          academic_year_id: 'year-2026',
          enrollment_date: '2026-02-01',
          status: 'ACTIVE',
          status_reason: null,
          created_at: '2026-01-01T00:00:00Z',
          updated_at: '2026-01-01T00:00:00Z',
        },
      ],
      total: 1,
    })

    mockListAssignments.mockResolvedValue({
      items: [
        {
          id: 'asg-001',
          teacher_id: 'tea-001',
          subject_id: 'sub-mat-10',
          group_id: 'grp-1001',
          academic_year_id: 'year-2026',
          weekly_hours: 4,
          is_active: true,
          created_at: '2026-01-01T00:00:00Z',
          updated_at: '2026-01-01T00:00:00Z',
        },
      ],
      total: 1,
    })
  })

  it('renders AcademicHub and shows module tabs', async () => {
    render(
      <MemoryRouter initialEntries={['/academic']}>
        <AuthProvider>
          <AcademicHub />
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/Gestión Académica e Institucional/i)).toBeInTheDocument()
    })

    expect(screen.getByRole('tab', { name: /Años Lectivos/i })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: /Grupos y Cupos/i })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: /Estudiantes/i })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: /Planta Docente/i })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: /Libro de Matrículas/i })).toBeInTheDocument()
  })

  it('renders AcademicYearsView with active year badge', async () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <AcademicYearsView />
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Año Lectivo 2026')).toBeInTheDocument()
      expect(screen.getByText('ACTIVO')).toBeInTheDocument()
    })
  })

  it('renders GroupsView and opens real-time capacity inspector modal', async () => {
    const user = userEvent.setup()

    render(
      <MemoryRouter>
        <AuthProvider>
          <GroupsView />
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('10-01')).toBeInTheDocument()
    })

    const viewCapacityBtn = screen.getByRole('button', { name: /Ver Cupos/i })
    await user.click(viewCapacityBtn)

    await waitFor(() => {
      expect(screen.getByText(/Disponibilidad y Cupos — Grupo 10-01/i)).toBeInTheDocument()
      expect(screen.getByText('28')).toBeInTheDocument()
      expect(screen.getByText('7')).toBeInTheDocument()
    })
  })

  it('renders StudentsView with SIMAT search and student record', async () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <StudentsView />
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('SIMAT-998877')).toBeInTheDocument()
      expect(screen.getByText('Carlos Pérez')).toBeInTheDocument()
    })
  })

  it('renders TeachersView with contract badge', async () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <TeachersView />
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Matemáticas')).toBeInTheDocument()
      expect(screen.getByText('PROPIEDAD')).toBeInTheDocument()
    })
  })

  it('renders GuardiansView with civil registry details', async () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <GuardiansView />
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Marta Gómez')).toBeInTheDocument()
      expect(screen.getByText('3109876543')).toBeInTheDocument()
    })
  })

  it('renders EnrollmentsView with active status badge', async () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <EnrollmentsView />
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('ACTIVA')).toBeInTheDocument()
    })
  })

  it('renders TransfersView form and history inspector', () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <TransfersView />
        </AuthProvider>
      </MemoryRouter>
    )

    expect(screen.getByText(/Trasladar Estudiante de Salón/i)).toBeInTheDocument()
    expect(screen.getByText(/Historial de Traslados por Matrícula/i)).toBeInTheDocument()
  })

  it('renders AcademicAssignmentsView with workload allocation table', async () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <AcademicAssignmentsView />
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('4 h/sem')).toBeInTheDocument()
      expect(screen.getByText('ACTIVA')).toBeInTheDocument()
    })
  })
})
