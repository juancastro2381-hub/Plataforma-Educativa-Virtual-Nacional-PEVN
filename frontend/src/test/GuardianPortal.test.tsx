/**
 * PEVN Frontend — Guardian Portal Unit and Integration Tests (Phase 14C)
 *
 * Tests the complete parental supervision experience:
 * - Profile and institutional header
 * - Multi-student context switching & Anti-IDOR validation
 * - Dashboard KPIs, urgent alerts, and recent evaluations
 * - Mis Hijos directory
 * - Academic performance and subject averages
 * - Homework monitoring & strictly read-only task detail modal (No submission actions)
 * - Official grades report on 0.0 – 5.0 scale
 * - Attendance stats and logs
 * - Virtual classroom agendas & modal
 * - Architectural placeholders for Phase 15 (Comunicados, Noticias, Convivencia)
 * - Mi Perfil view
 * - Safe empty and error fallbacks
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { GuardianPortal } from '@/pages/guardian/GuardianPortal'
import { guardianApi } from '@/services/guardian'
import { MemoryRouter } from 'react-router-dom'
import type {
  GuardianChildActivitiesListResponse,
  GuardianChildAttendanceListResponse,
  GuardianChildGradesListResponse,
  GuardianChildOverviewResponse,
  GuardianChildVirtualClassroomsListResponse,
  GuardianChildrenListResponse,
  GuardianProfileResponse,
} from '@/types/guardian'

// Mock guardianApi
vi.mock('@/services/guardian', () => ({
  guardianApi: {
    getProfile: vi.fn(),
    listStudents: vi.fn(),
    getChildOverview: vi.fn(),
    listChildActivities: vi.fn(),
    listChildGrades: vi.fn(),
    listChildAttendance: vi.fn(),
    listChildVirtualClassrooms: vi.fn(),
    getChildVirtualClassroom: vi.fn(),
  },
}))

// Mock communicationApi
vi.mock('@/services/communication', () => ({
  communicationApi: {
    getGuardianCommunications: vi.fn().mockResolvedValue({
      items: [
        {
          id: 'comm-1',
          institution_id: 'inst-1',
          title: 'Circular de Fin de Periodo',
          content: 'Estimados padres de familia, se les informa sobre la entrega de informes.',
          category: 'CIRCULAR_INFORMATIVA',
          priority: 'ALTA',
          status: 'PUBLICADO',
          published_at: '2026-09-01T08:00:00Z',
          expires_at: '2026-10-01T08:00:00Z',
          requires_acknowledgment: true,
          is_pinned: true,
          author_name: 'Rectoría Santa Librada',
          has_read: false,
          read_at: null,
          acknowledged_at: null,
          created_at: '2026-09-01T08:00:00Z',
        },
      ],
      total: 1,
      unread_count: 1,
    }),
    getGuardianNews: vi.fn().mockResolvedValue({
      items: [
        {
          id: 'news-1',
          institution_id: 'inst-1',
          title: 'Gran Feria de la Ciencia 2026',
          summary: 'Estudiantes de secundaria presentan sus proyectos científicos.',
          content: 'La feria científica se llevará a cabo en las instalaciones del colegio.',
          category: 'CIENCIA_TECNOLOGIA',
          cover_image_url: null,
          is_published: true,
          is_featured: true,
          published_at: '2026-09-01T08:00:00Z',
          author_name: 'Comité Científico',
          created_at: '2026-09-01T08:00:00Z',
        },
      ],
      total: 1,
    }),
    getChildIncidents: vi.fn().mockResolvedValue({
      items: [],
      total: 0,
    }),
  },
}))

const mockProfile: GuardianProfileResponse = {
  guardian_id: 'guard-1',
  user_id: 'user-guard-1',
  first_name: 'María Elena',
  last_name: 'Castro',
  full_name: 'María Elena Castro',
  email: 'maria.castro@familia.edu.co',
  document_type: 'CC',
  document_number: '52987654',
  phone: '3001234567',
  address: 'Calle 45 # 12-34, Bogotá',
  institution_id: 'inst-1',
  institution_name: 'Colegio Santa Librada',
  total_linked_students: 2,
}

const mockStudents: GuardianChildrenListResponse = {
  items: [
    {
      student_id: 'st-child-1',
      first_name: 'Mateo',
      last_name: 'Gómez Castro',
      full_name: 'Mateo Gómez Castro',
      code_simat: 'SIMAT-2026-MAT',
      document_type: 'TI',
      document_number: '1098765432',
      birth_date: '2012-04-10',
      relationship_type: 'Madre',
      is_primary_contact: true,
      is_authorized_pickup: true,
      institution_id: 'inst-1',
      institution_name: 'Colegio Santa Librada',
      campus_name: 'Sede Principal',
      grade_name: '8°',
      group_id: 'grp-8a',
      group_name: '8-A',
      academic_year_name: '2026',
      enrollment_status: 'MATRICULADO',
    },
    {
      student_id: 'st-child-2',
      first_name: 'Sofía',
      last_name: 'Gómez Castro',
      full_name: 'Sofía Gómez Castro',
      code_simat: 'SIMAT-2026-SOF',
      document_type: 'RC',
      document_number: '1098765433',
      birth_date: '2016-08-22',
      relationship_type: 'Madre',
      is_primary_contact: true,
      is_authorized_pickup: true,
      institution_id: 'inst-1',
      institution_name: 'Colegio Santa Librada',
      campus_name: 'Sede Principal',
      grade_name: '4°',
      group_id: 'grp-4b',
      group_name: '4-B',
      academic_year_name: '2026',
      enrollment_status: 'MATRICULADO',
    },
  ],
  total: 2,
}

const mockChild1Overview: GuardianChildOverviewResponse = {
  child: mockStudents.items[0],
  total_subjects: 5,
  pending_tasks_count: 2,
  overdue_tasks_count: 1,
  graded_tasks_count: 4,
  average_score: 4.4,
  attendance_summary: {
    total_sessions: 20,
    present_count: 18,
    absent_count: 1,
    late_count: 1,
    excused_count: 0,
    attendance_rate: 90,
  },
  upcoming_virtual_classrooms: [
    {
      id: 'vc-1',
      title: 'Clase de Ciencias Naturales en Vivo',
      description: 'Ecosistemas y biodiversidad colombiana.',
      scheduled_start_time: '2026-09-02T10:00:00Z',
      scheduled_end_time: '2026-09-02T11:30:00Z',
      status: 'SCHEDULED',
      room_name: 'ciencias-8a',
      subject_name: 'Ciencias Naturales',
      teacher_name: 'Prof. Carlos Mendoza',
      can_join: true,
      has_recordings: false,
    },
  ],
  pending_activities: [
    {
      id: 'act-1',
      title: 'Taller de Fotosíntesis',
      description: 'Resolver guía práctica del capítulo 3.',
      activity_type: 'WORKSHOP',
      status: 'PUBLISHED',
      submission_status: 'PENDING',
      publication_date: '2026-09-01T08:00:00Z',
      due_date: '2026-09-05T23:59:00Z',
      max_score: 5.0,
      score: null,
      feedback: null,
      graded_at: null,
      subject_id: 'subj-ciencias',
      subject_name: 'Ciencias Naturales',
      teacher_name: 'Prof. Carlos Mendoza',
      instructions: 'Realizar los esquemas gráficos con colores.',
      resource_url: 'https://cdn.pevn.gov.co/guias/fotosintesis.pdf',
    },
  ],
  recent_grades: [
    {
      grade_id: 'grd-1',
      activity_id: 'act-2',
      activity_title: 'Examen de Álgebra',
      activity_type: 'EXAM',
      subject_id: 'subj-mat',
      subject_name: 'Matemáticas',
      teacher_name: 'Prof. Diana Romero',
      max_score: 5.0,
      score: 4.8,
      status: 'GRADED',
      feedback: 'Excelente dominio de ecuaciones de primer grado.',
      graded_at: '2026-08-28T15:00:00Z',
    },
  ],
}

const mockChild1Activities: GuardianChildActivitiesListResponse = {
  student_id: 'st-child-1',
  student_name: 'Mateo Gómez Castro',
  items: [
    {
      id: 'act-1',
      title: 'Taller de Fotosíntesis',
      description: 'Resolver guía práctica del capítulo 3.',
      activity_type: 'WORKSHOP',
      status: 'PUBLISHED',
      submission_status: 'PENDING',
      publication_date: '2026-09-01T08:00:00Z',
      due_date: '2026-09-05T23:59:00Z',
      max_score: 5.0,
      score: null,
      feedback: null,
      graded_at: null,
      subject_id: 'subj-ciencias',
      subject_name: 'Ciencias Naturales',
      teacher_name: 'Prof. Carlos Mendoza',
      instructions: 'Realizar los esquemas gráficos con colores.',
      resource_url: 'https://cdn.pevn.gov.co/guias/fotosintesis.pdf',
    },
    {
      id: 'act-2',
      title: 'Examen de Álgebra',
      description: 'Evaluación periódica.',
      activity_type: 'EXAM',
      status: 'PUBLISHED',
      submission_status: 'GRADED',
      publication_date: '2026-08-25T08:00:00Z',
      due_date: '2026-08-27T10:00:00Z',
      max_score: 5.0,
      score: 4.8,
      feedback: 'Excelente dominio de ecuaciones de primer grado.',
      graded_at: '2026-08-28T15:00:00Z',
      subject_id: 'subj-mat',
      subject_name: 'Matemáticas',
      teacher_name: 'Prof. Diana Romero',
      instructions: 'Resolver paso a paso.',
      resource_url: null,
    },
  ],
  total: 2,
}

const mockChild1Grades: GuardianChildGradesListResponse = {
  student_id: 'st-child-1',
  student_name: 'Mateo Gómez Castro',
  items: [
    {
      grade_id: 'grd-1',
      activity_id: 'act-2',
      activity_title: 'Examen de Álgebra',
      activity_type: 'EXAM',
      subject_id: 'subj-mat',
      subject_name: 'Matemáticas',
      teacher_name: 'Prof. Diana Romero',
      max_score: 5.0,
      score: 4.8,
      status: 'GRADED',
      feedback: 'Excelente dominio de ecuaciones de primer grado.',
      graded_at: '2026-08-28T15:00:00Z',
    },
  ],
  total: 1,
  average_score: 4.8,
}

const mockChild1Attendance: GuardianChildAttendanceListResponse = {
  student_id: 'st-child-1',
  student_name: 'Mateo Gómez Castro',
  items: [
    {
      id: 'att-1',
      attendance_date: '2026-09-01',
      status: 'PRESENT',
      subject_name: 'Ciencias Naturales',
      teacher_name: 'Prof. Carlos Mendoza',
      remarks: 'Puntual y participativo',
    },
    {
      id: 'att-2',
      attendance_date: '2026-08-31',
      status: 'ABSENT',
      subject_name: 'Matemáticas',
      teacher_name: 'Prof. Diana Romero',
      remarks: 'Inasistencia sin justificar',
    },
  ],
  total: 2,
  summary: {
    total_sessions: 20,
    present_count: 18,
    absent_count: 1,
    late_count: 1,
    excused_count: 0,
    attendance_rate: 90,
  },
}

const mockChild1VirtualClasses: GuardianChildVirtualClassroomsListResponse = {
  student_id: 'st-child-1',
  student_name: 'Mateo Gómez Castro',
  items: [
    {
      id: 'vc-1',
      title: 'Clase de Ciencias Naturales en Vivo',
      description: 'Ecosistemas y biodiversidad colombiana.',
      scheduled_start_time: '2026-09-02T10:00:00Z',
      scheduled_end_time: '2026-09-02T11:30:00Z',
      status: 'SCHEDULED',
      room_name: 'ciencias-8a',
      subject_name: 'Ciencias Naturales',
      teacher_name: 'Prof. Carlos Mendoza',
      can_join: true,
      has_recordings: false,
    },
  ],
  total: 1,
}

describe('GuardianPortal (Phase 14C)', () => {
  beforeEach(() => {
    vi.clearAllMocks()

    vi.mocked(guardianApi.getProfile).mockResolvedValue(mockProfile)
    vi.mocked(guardianApi.listStudents).mockResolvedValue(mockStudents)
    vi.mocked(guardianApi.getChildOverview).mockResolvedValue(mockChild1Overview)
    vi.mocked(guardianApi.listChildActivities).mockResolvedValue(mockChild1Activities)
    vi.mocked(guardianApi.listChildGrades).mockResolvedValue(mockChild1Grades)
    vi.mocked(guardianApi.listChildAttendance).mockResolvedValue(mockChild1Attendance)
    vi.mocked(guardianApi.listChildVirtualClassrooms).mockResolvedValue(mockChild1VirtualClasses)
  })

  it('renders Guardian Header and Student Switcher with authorized children', async () => {
    render(
      <MemoryRouter initialEntries={['/guardian?tab=dashboard']}>
        <GuardianPortal />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/¡Bienvenido\(a\), María Elena Castro!/)).toBeInTheDocument()
      expect(screen.getByText(/Colegio Santa Librada/)).toBeInTheDocument()
    })

    // Verify multi-student context switcher renders both children
    expect(screen.getByText('Mateo Gómez Castro')).toBeInTheDocument()
    expect(screen.getByText('Sofía Gómez Castro')).toBeInTheDocument()
    expect(screen.getByText('✓ Activo')).toBeInTheDocument()
  })

  it('renders Dashboard KPIs, alert banners, and recent evaluations for the active child', async () => {
    render(
      <MemoryRouter initialEntries={['/guardian?tab=dashboard']}>
        <GuardianPortal />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Asignaturas Cursadas')).toBeInTheDocument()
      expect(screen.getByText('Tareas Pendientes')).toBeInTheDocument()
      expect(screen.getByText('Asistencia Escolar')).toBeInTheDocument()
      expect(screen.getByText('Promedio General')).toBeInTheDocument()
    })

    // Verify alert banner for overdue task
    expect(screen.getByText(/Atención requerida: 1 tarea vencida/i)).toBeInTheDocument()
    // Verify recent grade
    expect(screen.getByText('Examen de Álgebra')).toBeInTheDocument()
    expect(screen.getByText('4.8')).toBeInTheDocument()
  })

  it('switches student context and fetches child-specific data when clicking a different child', async () => {
    render(
      <MemoryRouter initialEntries={['/guardian?tab=dashboard']}>
        <GuardianPortal />
      </MemoryRouter>
    )

    // Wait for initial load to finish completely so switcher buttons are enabled
    await waitFor(() => {
      expect(screen.getByText('Asignaturas Cursadas')).toBeInTheDocument()
    })

    // Click on Sofia via data-testid
    const sofiaBtn = screen.getByTestId('student-switcher-st-child-2')
    expect(sofiaBtn).toBeInTheDocument()
    expect(sofiaBtn).not.toBeDisabled()
    fireEvent.click(sofiaBtn)

    await waitFor(() => {
      expect(guardianApi.getChildOverview).toHaveBeenCalledWith('st-child-2')
      expect(guardianApi.listChildActivities).toHaveBeenCalledWith('st-child-2')
      expect(guardianApi.listChildGrades).toHaveBeenCalledWith('st-child-2')
      expect(guardianApi.listChildAttendance).toHaveBeenCalledWith('st-child-2')
      expect(guardianApi.listChildVirtualClassrooms).toHaveBeenCalledWith('st-child-2')
    })
  })

  it('navigates to "Mis Hijos" view and displays full directory of children', async () => {
    render(
      <MemoryRouter initialEntries={['/guardian?tab=students']}>
        <GuardianPortal />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Mis Hijos y Tutorados Registrados')).toBeInTheDocument()
      expect(screen.getByText(/SIMAT-2026-MAT/)).toBeInTheDocument()
      expect(screen.getByText(/SIMAT-2026-SOF/)).toBeInTheDocument()
    })
  })

  it('navigates to "Rendimiento" view and displays subject breakdown', async () => {
    render(
      <MemoryRouter initialEntries={['/guardian?tab=academic']}>
        <GuardianPortal />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Rendimiento Académico y Desempeño')).toBeInTheDocument()
      expect(screen.getByText('Promedio General Acumulado')).toBeInTheDocument()
      expect(screen.getByText(/Matemáticas/)).toBeInTheDocument()
    })
  })

  it('navigates to "Tareas" view and opens strictly READ-ONLY task detail modal (No submission buttons)', async () => {
    render(
      <MemoryRouter initialEntries={['/guardian?tab=tasks']}>
        <GuardianPortal />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/Tareas y Trabajos Escolares/)).toBeInTheDocument()
      expect(screen.getByText('Taller de Fotosíntesis')).toBeInTheDocument()
    })

    // Click "Ver Detalle e Instrucciones"
    const detailBtn = screen.getAllByText(/Ver Detalle e Instrucciones/)[0]
    fireEvent.click(detailBtn)

    // Verify modal is open and in read-only supervisory mode
    expect(screen.getByText(/Descripción y Objetivos de la Actividad/i)).toBeInTheDocument()
    expect(screen.getByText(/Instrucciones Pedagógicas/i)).toBeInTheDocument()
    expect(screen.getByText(/La entrega y desarrollo de actividades académicas corresponde exclusivamente al estudiante/)).toBeInTheDocument()

    // Assert NO submission buttons exist in the DOM
    expect(screen.queryByText(/Entregar Tarea/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/Subir Archivo/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/Editar Entrega/i)).not.toBeInTheDocument()

    // Close modal
    fireEvent.click(screen.getByText('Cerrar Vista'))
    expect(screen.queryByText(/Descripción y Objetivos de la Actividad/i)).not.toBeInTheDocument()
  })

  it('navigates to "Calificaciones" view and renders official grades table on 0.0 - 5.0 scale', async () => {
    render(
      <MemoryRouter initialEntries={['/guardian?tab=grades']}>
        <GuardianPortal />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/Libreta Oficial de Calificaciones/)).toBeInTheDocument()
      expect(screen.getByText('Promedio Ponderado General')).toBeInTheDocument()
      expect(screen.getByText('4.8 / 5.0')).toBeInTheDocument()
    })
  })

  it('navigates to "Asistencia" view and displays summary statistics and log table', async () => {
    render(
      <MemoryRouter initialEntries={['/guardian?tab=attendance']}>
        <GuardianPortal />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/Control de Asistencia Escolar/)).toBeInTheDocument()
      expect(screen.getByText('Porcentaje Asistencia')).toBeInTheDocument()
      expect(screen.getByText('90%')).toBeInTheDocument()
      expect(screen.getAllByText('Inasistencias').length).toBeGreaterThan(0)
      expect(screen.getByText('Inasistencia sin justificar')).toBeInTheDocument()
    })
  })

  it('navigates to "Clases Virtuales" view and renders agenda and session modal', async () => {
    render(
      <MemoryRouter initialEntries={['/guardian?tab=virtual-classes']}>
        <GuardianPortal />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/Agenda de Clases Virtuales/)).toBeInTheDocument()
      expect(screen.getByText('Clase de Ciencias Naturales en Vivo')).toBeInTheDocument()
    })

    // Click "Consultar Agenda de Clase"
    const viewClassBtn = screen.getByText(/Consultar Agenda de Clase/)
    fireEvent.click(viewClassBtn)

    expect(screen.getByText(/Identificador de Sala/i)).toBeInTheDocument()
    expect(screen.getByText('ciencias-8a')).toBeInTheDocument()
    expect(screen.getByText(/Acompañamiento en Clase Virtual/)).toBeInTheDocument()
  })

  it('renders Phase 15 views for Comunicados, Noticias, and Convivencia', async () => {
    render(
      <MemoryRouter initialEntries={['/guardian?tab=communications']}>
        <GuardianPortal />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Comunicados Institucionales')).toBeInTheDocument()
      expect(screen.getByText('Circular de Fin de Periodo')).toBeInTheDocument()
    })

    // Navigate to Noticias
    fireEvent.click(screen.getByTestId('guardian-tab-news'))
    await waitFor(() => {
      expect(screen.getByText('Periódico Escolar y Noticias')).toBeInTheDocument()
      expect(screen.getAllByText('Gran Feria de la Ciencia 2026').length).toBeGreaterThan(0)
    })

    // Navigate to Convivencia
    fireEvent.click(screen.getByTestId('guardian-tab-incidents'))
    await waitFor(() => {
      expect(screen.getByText(/Observador de Convivencia/)).toBeInTheDocument()
      expect(screen.getByText('Excelente Convivencia Escolar')).toBeInTheDocument()
    })
  })

  it('navigates to "Mi Perfil" view and renders guardian contact info', async () => {
    render(
      <MemoryRouter initialEntries={['/guardian?tab=profile']}>
        <GuardianPortal />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Acudiente Verificado')).toBeInTheDocument()
      expect(screen.getAllByText(/52987654/).length).toBeGreaterThan(0)
      expect(screen.getAllByText(/3001234567/).length).toBeGreaterThan(0)
      expect(screen.getByText(/Calle 45 # 12-34, Bogotá/)).toBeInTheDocument()
    })
  })

  it('renders empty state gracefully when guardian has zero linked students', async () => {
    vi.mocked(guardianApi.listStudents).mockResolvedValue({ items: [], total: 0 })

    render(
      <MemoryRouter initialEntries={['/guardian?tab=dashboard']}>
        <GuardianPortal />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Sin estudiantes vinculados')).toBeInTheDocument()
    })
  })

  it('handles API error gracefully and provides a retry mechanism', async () => {
    vi.mocked(guardianApi.getProfile).mockRejectedValueOnce(new Error('Network error'))

    render(
      <MemoryRouter initialEntries={['/guardian?tab=dashboard']}>
        <GuardianPortal />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Error de Acceso')).toBeInTheDocument()
      expect(screen.getByText('Reintentar')).toBeInTheDocument()
    })
  })
})
