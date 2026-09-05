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

let activeUser: User = mockAdminUser

// Mock auth service
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

// Mock institution service
const mockGetMyInstitution = vi.fn()
vi.mock('@/services/institution', () => ({
  institutionApi: {
    getMyInstitution: () => mockGetMyInstitution(),
  },
  default: {
    getMyInstitution: () => mockGetMyInstitution(),
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
const mockListGrades = vi.fn()
const mockListSubjects = vi.fn()
const mockCreateGroup = vi.fn()
const mockCreateEnrollment = vi.fn()
const mockCreateAssignment = vi.fn()
const mockTransferStudentGroup = vi.fn()
const mockAssociateGuardianToStudent = vi.fn()

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
    listGrades: () => mockListGrades(),
    listSubjects: () => mockListSubjects(),
    createGroup: (payload: any) => mockCreateGroup(payload),
    createEnrollment: (payload: any) => mockCreateEnrollment(payload),
    createAssignment: (payload: any) => mockCreateAssignment(payload),
    transferStudentGroup: (payload: any) => mockTransferStudentGroup(payload),
    associateGuardianToStudent: (gId: string, sId: string, payload: any) =>
      mockAssociateGuardianToStudent(gId, sId, payload),
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
    listGrades: () => mockListGrades(),
    listSubjects: () => mockListSubjects(),
    createGroup: (payload: any) => mockCreateGroup(payload),
    createEnrollment: (payload: any) => mockCreateEnrollment(payload),
    createAssignment: (payload: any) => mockCreateAssignment(payload),
    transferStudentGroup: (payload: any) => mockTransferStudentGroup(payload),
    associateGuardianToStudent: (gId: string, sId: string, payload: any) =>
      mockAssociateGuardianToStudent(gId, sId, payload),
    getTransferHistory: () => Promise.resolve({ items: [], total: 0 }),
  },
}))

describe('Academic Management Views', () => {
  beforeEach(() => {
    activeUser = mockAdminUser
    vi.clearAllMocks()

    mockGetMyInstitution.mockResolvedValue({
      id: 'inst-001',
      name: 'Institución Educativa Santa Librada',
      dane_code: '111001044806',
      campuses: [
        {
          id: 'camp-01',
          institution_id: 'inst-001',
          name: 'Sede Principal',
          dane_sede_code: '111001044806',
          is_active: true,
        },
      ],
    })

    mockListGrades.mockResolvedValue({
      items: [
        {
          id: 'grd-10',
          code: 'G10',
          name: 'Décimo',
          level: 'MEDIA',
          ordinal_order: 10,
        },
      ],
      total: 1,
    })

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
          institution_id: 'inst-001',
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

    mockListSubjects.mockResolvedValue({
      items: [
        {
          id: 'sub-mat-10',
          institution_id: 'inst-001',
          knowledge_area_id: 'ka-001',
          grade_id: 'grade-10',
          name: 'Matemáticas - Grado 10',
          weekly_hours: 4,
          created_at: '2026-01-01T00:00:00Z',
          updated_at: '2026-01-01T00:00:00Z',
        },
      ],
      total: 1,
    })

    mockCreateAssignment.mockResolvedValue({
      id: 'asg-002',
      teacher_id: 'tea-001',
      subject_id: 'sub-mat-10',
      group_id: 'grp-1001',
      academic_year_id: 'year-2026',
      weekly_hours: 4,
      is_active: true,
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
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

  it('renders GroupsView create modal with Sede, Año Lectivo, and Grado dropdowns and submits canonical UUIDs', async () => {
    const user = userEvent.setup()
    mockCreateGroup.mockResolvedValue({
      id: 'grp-new-1002',
      campus_id: 'camp-01',
      academic_year_id: 'year-2026',
      grade_id: 'grd-10',
      name: '10-B',
      shift: 'MANANA',
      capacity_limit: 35,
      group_director_teacher_id: null,
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
    })

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

    const newGroupBtn = screen.getByRole('button', { name: /\+ Nuevo Grupo/i })
    await user.click(newGroupBtn)

    await waitFor(() => {
      expect(screen.getByText(/Crear Nuevo Grupo \/ Salón/i)).toBeInTheDocument()
      expect(screen.getByText(/Sede Educativa \*/i)).toBeInTheDocument()
      expect(screen.getByText(/Año Lectivo \*/i)).toBeInTheDocument()
      expect(screen.getByText(/Grado \*/i)).toBeInTheDocument()
    })

    // Sede should show the preselected/available campus
    expect(screen.getByDisplayValue(/Sede Principal — DANE 111001044806/i)).toBeInTheDocument()

    // Academic year should show active year
    expect(screen.getByDisplayValue(/Año Lectivo 2026 \(ACTIVE\)/i)).toBeInTheDocument()

    // Select grade
    const selects = screen.getAllByRole('combobox')
    const gradeSelect = selects.find((s) => (s as HTMLSelectElement).innerHTML.includes('Décimo'))
    if (gradeSelect) {
      await user.selectOptions(gradeSelect, 'grd-10')
    }

    // Fill Name
    const nameInput = screen.getByPlaceholderText('10-01')
    await user.type(nameInput, '10-B')

    // Submit
    const submitBtn = screen.getByRole('button', { name: /Guardar Grupo/i })
    await user.click(submitBtn)

    await waitFor(() => {
      expect(mockCreateGroup).toHaveBeenCalledWith(
        expect.objectContaining({
          campus_id: 'camp-01',
          academic_year_id: 'year-2026',
          grade_id: 'grd-10',
          name: '10-B',
          shift: 'MANANA',
          capacity_limit: 35,
        })
      )
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

  it('renders EnrollmentsView with active status badge and contextual create selectors', async () => {
    mockCreateEnrollment.mockResolvedValue({
      id: 'enr-new-01',
      student_id: 'std-001',
      group_id: 'grp-1001',
      academic_year_id: 'year-2026',
      enrollment_date: '2026-02-15',
      status: 'ACTIVE',
      status_reason: null,
      created_at: '2026-02-15T00:00:00Z',
      updated_at: '2026-02-15T00:00:00Z',
    })

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

    // Open Create Modal
    const createBtn = screen.getByRole('button', { name: /\+ Formalizar Matrícula/i })
    await userEvent.click(createBtn)

    expect(screen.getByText('Formalizar Nueva Matrícula')).toBeInTheDocument()

    // Verify selectors are populated and select options
    await waitFor(() => {
      expect(screen.getByRole('option', { name: /Carlos Pérez/i })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: /Año Lectivo 2026/i })).toBeInTheDocument()
      expect(screen.getByRole('option', { name: /10-01/i })).toBeInTheDocument()
    })

    const studentSelect = screen.getByLabelText(/Estudiante \*/i)
    await userEvent.selectOptions(studentSelect, 'std-001')

    const groupSelect = screen.getByLabelText(/Salón \/ Grupo Destino \*/i)
    await userEvent.selectOptions(groupSelect, 'grp-1001')

    const submitBtn = screen.getByRole('button', { name: /Registrar Matrícula/i })
    await userEvent.click(submitBtn)

    await waitFor(() => {
      expect(mockCreateEnrollment).toHaveBeenCalledWith(
        expect.objectContaining({
          student_id: 'std-001',
          academic_year_id: 'year-2026',
          group_id: 'grp-1001',
          status: 'ACTIVE',
        })
      )
    })
  })

  it('renders TransfersView form with active enrollment and target group selectors', async () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <TransfersView />
        </AuthProvider>
      </MemoryRouter>
    )

    expect(screen.getByText(/Trasladar Estudiante de Salón/i)).toBeInTheDocument()
    expect(screen.getByText(/Historial de Traslados por Matrícula/i)).toBeInTheDocument()

    // Verify Active Enrollment selector populated
    await waitFor(() => {
      expect(screen.getAllByText(/Carlos Pérez/i).length).toBeGreaterThan(0)
    })
  })

  it('renders GuardiansView with civil registry details and link student modal selector', async () => {
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

    // Open Link Student Modal
    const linkBtn = screen.getByRole('button', { name: /Vincular a Estudiante/i })
    await userEvent.click(linkBtn)

    expect(screen.getByText(/Vincular Acudiente — Marta Gómez/i)).toBeInTheDocument()

    // Verify student selector in link modal
    await waitFor(() => {
      expect(screen.getByRole('option', { name: /Carlos Pérez/i })).toBeInTheDocument()
    })
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

  it('allows opening create modal and renders resolved selectors for Teacher, Year, Group, Subject', async () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <AcademicAssignmentsView />
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /\+ Asignar Carga Académica/i })).toBeInTheDocument()
    })

    await userEvent.click(screen.getByRole('button', { name: /\+ Asignar Carga Académica/i }))

    await waitFor(() => {
      expect(screen.getByText('Asignar Carga Académica Docente')).toBeInTheDocument()
    })

    // Verify resolved dropdown options are populated
    expect(screen.getByRole('option', { name: /Matemáticas - Grado 10/i })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: /10-01/i })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: /Año Lectivo 2026/i })).toBeInTheDocument()
  })

  it('renders unauthorized notice banner when navigating directly to a restricted tab', async () => {
    // User with only academic_assignments:read (Teacher profile)
    activeUser = {
      ...mockAdminUser,
      roles: ['teacher'],
      permissions: ['academic_assignments:read'],
    }

    render(
      <MemoryRouter initialEntries={['/academic?tab=years']}>
        <AuthProvider>
          <AcademicHub />
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument()
      expect(
        screen.getByText(/La sección "Años Lectivos" no se encuentra disponible para su rol/i)
      ).toBeInTheDocument()
    })

    // Dismiss notice banner
    const closeBtn = screen.getByRole('button', { name: /Cerrar notificación/i })
    await userEvent.click(closeBtn)
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('renders zero-state restricted access message when user has no academic permissions', async () => {
    // User with no academic permissions (Guardian profile)
    activeUser = {
      ...mockAdminUser,
      roles: ['guardian'],
      permissions: [],
    }

    render(
      <MemoryRouter initialEntries={['/academic']}>
        <AuthProvider>
          <AcademicHub />
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(
        screen.getByText(/Portal de Gestión Académica — Acceso Restringido/i)
      ).toBeInTheDocument()
      expect(screen.getByText(/Volver al Panel Principal/i)).toBeInTheDocument()
    })
  })
})
