/**
 * PEVN Frontend — Teacher Portal Unit and Integration Tests (Phase 13D.5)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { TeacherPortal } from '@/pages/teacher/TeacherPortal'
import { teacherApi } from '@/services/teacher'
import { MemoryRouter } from 'react-router-dom'

// Mock useAuth
vi.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({
    user: { id: 'teacher-1', roles: ['teacher'], permissions: ['evaluations:read', 'evaluations:grade', 'evaluations:recovery'] },
    hasPermission: () => true,
    hasRole: () => false,
  }),
}))

// Mock evaluationApi
vi.mock('@/services/evaluation', () => ({
  evaluationApi: {
    listAcademicPeriods: vi.fn().mockResolvedValue({ items: [], total: 0 }),
    getActiveSieePolicy: vi.fn().mockResolvedValue(null),
    getPeriodSheet: vi.fn().mockResolvedValue(null),
  },
}))

// Mock teacherApi
vi.mock('@/services/teacher', () => ({
  teacherApi: {
    getDashboardSummary: vi.fn(),
    listAssignments: vi.fn(),
    listGroups: vi.fn(),
    getGroupRoster: vi.fn(),
    listActivities: vi.fn(),
    getActivity: vi.fn(),
    createActivity: vi.fn(),
    updateActivity: vi.fn(),
    publishActivity: vi.fn(),
    closeActivity: vi.fn(),
    deleteActivity: vi.fn(),
    getActivityGrades: vi.fn(),
    batchUpdateActivityGrades: vi.fn(),
    getDailyAttendance: vi.fn(),
    recordDailyAttendance: vi.fn(),
    listPlanning: vi.fn(),
    createPlanning: vi.fn(),
    updatePlanning: vi.fn(),
    deletePlanning: vi.fn(),
  },
}))

const mockSummary = {
  teacher_id: '11111111-1111-1111-1111-111111111111',
  teacher_name: 'Prof. Carlos Mendoza',
  specialty_area: 'Ciencias Naturales',
  institution_id: 'inst-1',
  institution_name: 'Colegio Nacional Santander',
  active_academic_year: 'Año Escolar 2026 (Activo)',
  total_active_assignments: 3,
  total_assigned_groups: 2,
  total_assigned_subjects: 2,
  total_active_activities: 4,
  total_pending_grades: 12,
  total_enrolled_students: 45,
}

const mockAssignments = {
  items: [
    {
      id: 'asg-1',
      teacher_id: '11111111-1111-1111-1111-111111111111',
      subject_id: 'sub-1',
      subject_name: 'Física Clásica',
      knowledge_area_name: 'Ciencias Naturales',
      group_id: 'grp-1',
      group_name: '10-A',
      grade_name: 'Décimo',
      campus_name: 'Sede Principal',
      shift: 'MAÑANA',
      academic_year_id: 'ay-1',
      academic_year_name: '2026',
      weekly_hours: 4,
      is_active: true,
    },
  ],
  total: 1,
}

const mockGroups = {
  items: [
    {
      group_id: 'grp-1',
      group_name: '10-A',
      grade_name: 'Décimo',
      campus_name: 'Sede Principal',
      shift: 'MAÑANA',
      academic_year_id: 'ay-1',
      academic_year_name: '2026',
      capacity_limit: 40,
      active_enrolled_count: 35,
      subjects_taught: ['Física Clásica'],
    },
  ],
  total: 1,
}

const mockRoster = {
  group_id: 'grp-1',
  group_name: '10-A',
  academic_year_id: 'ay-1',
  academic_year_name: '2026',
  campus_name: 'Sede Principal',
  shift: 'MAÑANA',
  total_students: 2,
  students: [
    {
      student_id: 'st-1',
      enrollment_id: 'enr-1',
      first_name: 'Ana',
      last_name: 'García',
      full_name: 'Ana García',
      document_type: 'TI',
      document_number: '10203040',
      code_simat: 'SIM-101',
      simat_code: 'SIM-101',
      enrollment_status: 'MATRICULADO',
      has_disability: false,
      disability_type: null,
      guardian_names: ['María García (Madre)'],
      guardian_phones: ['3001234567'],
    },
  ],
}

const mockActivities = {
  items: [
    {
      id: 'act-1',
      teacher_id: '11111111-1111-1111-1111-111111111111',
      academic_assignment_id: 'asg-1',
      subject_name: 'Física Clásica',
      group_id: 'grp-1',
      group_name: '10-A',
      title: 'Taller 1: Cinemática',
      description: 'Problemas de MRU y MRUA',
      activity_type: 'WORKSHOP' as const,
      max_score: 5.0,
      weight_percentage: 20.0,
      due_date: '2026-03-15T23:59:00Z',
      status: 'PUBLISHED' as const,
      total_submissions: 30,
      total_graded: 25,
      created_at: '2026-02-01T00:00:00Z',
      updated_at: '2026-02-01T00:00:00Z',
    },
    {
      id: 'act-2',
      teacher_id: '11111111-1111-1111-1111-111111111111',
      academic_assignment_id: 'asg-1',
      subject_name: 'Física Clásica',
      group_id: 'grp-1',
      group_name: '10-A',
      title: 'Taller 2: Leyes de Newton (Borrador)',
      description: 'Actividad borrador en preparación',
      activity_type: 'WORKSHOP' as const,
      max_score: 5.0,
      weight_percentage: 20.0,
      due_date: '2026-04-01T23:59:00Z',
      status: 'DRAFT' as const,
      total_submissions: 0,
      total_graded: 0,
      created_at: '2026-02-15T00:00:00Z',
      updated_at: '2026-02-15T00:00:00Z',
    },
  ],
  total: 2,
}

const mockGradesheet = {
  activity_id: 'act-1',
  activity_title: 'Taller 1: Cinemática',
  group_name: '10-A',
  subject_name: 'Física Clásica',
  max_score: 5.0,
  items: [
    {
      id: 'grade-1',
      activity_id: 'act-1',
      student_id: 'st-1',
      student_name: 'Ana García',
      student_document: 'TI: 10203040',
      score: 4.5,
      feedback: 'Excelente desarrollo de ecuaciones.',
      status: 'GRADED' as const,
      graded_at: '2026-02-10T12:00:00Z',
    },
  ],
  total: 1,
}

const mockAttendance = {
  group_id: 'grp-1',
  group_name: '10-A',
  attendance_date: '2026-02-15',
  total_students: 1,
  total_present: 1,
  total_absent: 0,
  items: [
    {
      student_id: 'st-1',
      student_name: 'Ana García',
      student_document: 'TI: 10203040',
      status: 'PRESENT' as const,
      remarks: 'Asistencia puntual',
    },
  ],
}

const mockPlanning = {
  items: [
    {
      id: 'plan-1',
      institution_id: 'inst-1',
      teacher_id: '11111111-1111-1111-1111-111111111111',
      teacher_name: 'Prof. Carlos Mendoza',
      subject_id: 'sub-1',
      subject_name: 'Física Clásica',
      group_id: 'grp-1',
      group_name: '10-A',
      academic_year_id: 'ay-1',
      academic_year_name: '2026',
      unit_name: 'Unidad 1: Mecánica Clásica',
      competencies: 'Razonamiento científico',
      learning_objectives: 'Comprender las leyes de movimiento',
      methodology: 'Laboratorios virtuales',
      evaluation_criteria: 'Rúbrica de laboratorio',
      resources: 'Guía física',
      status: 'APPROVED' as const,
      start_date: '2026-02-01',
      end_date: '2026-03-30',
      created_at: '2026-02-01T00:00:00Z',
      updated_at: '2026-02-01T00:00:00Z',
    },
  ],
  total: 1,
}

describe('TeacherPortal Component Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(teacherApi.getDashboardSummary).mockResolvedValue(mockSummary as any)
    vi.mocked(teacherApi.listAssignments).mockResolvedValue(mockAssignments as any)
    vi.mocked(teacherApi.listGroups).mockResolvedValue(mockGroups as any)
    vi.mocked(teacherApi.getGroupRoster).mockResolvedValue(mockRoster as any)
    vi.mocked(teacherApi.listActivities).mockResolvedValue(mockActivities as any)
    vi.mocked(teacherApi.updateActivity).mockResolvedValue(mockActivities.items[0] as any)
    vi.mocked(teacherApi.getActivityGrades).mockResolvedValue(mockGradesheet as any)
    vi.mocked(teacherApi.getDailyAttendance).mockResolvedValue(mockAttendance as any)
    vi.mocked(teacherApi.listPlanning).mockResolvedValue(mockPlanning as any)
    vi.mocked(teacherApi.updatePlanning).mockResolvedValue(mockPlanning.items[0] as any)
  })

  it('renders all 7 navigation subtabs and displays dashboard summary KPIs', async () => {
    render(
      <MemoryRouter initialEntries={['/teacher?tab=dashboard']}>
        <TeacherPortal />
      </MemoryRouter>
    )

    // Check title
    expect(screen.getByText('Portal Docente Institucional')).toBeInTheDocument()

    // Check subtabs
    expect(screen.getByRole('button', { name: /Inicio/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Mi Carga/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Mis Grupos/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Actividades/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Calificaciones/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Asistencia/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Planeación/i })).toBeInTheDocument()

    // Wait for dashboard data
    await waitFor(() => {
      expect(screen.getByText('¡Bienvenido, Prof. Carlos Mendoza!')).toBeInTheDocument()
    })

    expect(screen.getByText('Colegio Nacional Santander • Ciencias Naturales')).toBeInTheDocument()
  })

  it('navigates to Mi Carga and displays assigned subjects and groups without UUIDs', async () => {
    render(
      <MemoryRouter initialEntries={['/teacher?tab=load']}>
        <TeacherPortal />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Mi Carga Académica Asignada')).toBeInTheDocument()
    })

    expect(screen.getByText('Física Clásica')).toBeInTheDocument()
    expect(screen.getByText('Grupo 10-A')).toBeInTheDocument()
    expect(screen.getByText('4 h/sem')).toBeInTheDocument()
  })

  it('navigates to Mis Grupos and opens official student roster modal', async () => {
    render(
      <MemoryRouter initialEntries={['/teacher?tab=dashboard']}>
        <TeacherPortal />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('¡Bienvenido, Prof. Carlos Mendoza!')).toBeInTheDocument()
    })

    const tab = screen.getByRole('button', { name: /Mis Grupos/i })
    fireEvent.click(tab)

    await waitFor(() => {
      expect(screen.getByText('Mis Grupos y Salones de Clase')).toBeInTheDocument()
    })

    expect(screen.getByText('Grupo 10-A')).toBeInTheDocument()

    const openBtn = screen.getByTestId('btn-open-roster')
    expect(openBtn).toBeInTheDocument()

    // Open Roster
    fireEvent.click(openBtn)

    await waitFor(() => {
      expect(teacherApi.getGroupRoster).toHaveBeenCalledWith('grp-1')
    })

    await waitFor(() => {
      expect(screen.getByText('Planilla Pedagógica Oficial')).toBeInTheDocument()
    })

    expect(screen.getByText('Ana García')).toBeInTheDocument()
    expect(screen.getByText('TI: 10203040')).toBeInTheDocument()
    expect(screen.getByText('SIM-101')).toBeInTheDocument()
  })

  it('navigates to Actividades and displays active assignments with actions', async () => {
    render(
      <MemoryRouter initialEntries={['/teacher?tab=activities']}>
        <TeacherPortal />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Actividades Académicas y Evaluaciones')).toBeInTheDocument()
    })

    expect(screen.getByText('Taller 1: Cinemática')).toBeInTheDocument()
    expect(screen.getByText('PUBLICADA')).toBeInTheDocument()
    expect(screen.getByText('+ Nueva Actividad Académica')).toBeInTheDocument()
  })

  it('navigates to Calificaciones and renders official gradesheet table with score bounds', async () => {
    render(
      <MemoryRouter initialEntries={['/teacher?tab=grades']}>
        <TeacherPortal />
      </MemoryRouter>
    )

    // Switch to Activity grading sub-mode
    const actBtn = await screen.findByRole('button', { name: /Calificar por Actividad/i })
    fireEvent.click(actBtn)

    await waitFor(() => {
      expect(screen.getByText('Planilla de Calificaciones y Retroalimentación')).toBeInTheDocument()
    })

    await waitFor(() => {
      expect(screen.getByText('Ana García')).toBeInTheDocument()
    })

    expect(screen.getByDisplayValue('4.5')).toBeInTheDocument()
    expect(screen.getByDisplayValue('Excelente desarrollo de ecuaciones.')).toBeInTheDocument()
    expect(screen.getByText('EVALUADO')).toBeInTheDocument()
  })

  it('navigates to Asistencia and renders student attendance list with present toggle', async () => {
    render(
      <MemoryRouter initialEntries={['/teacher?tab=attendance']}>
        <TeacherPortal />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Control Diario de Asistencia Escolar')).toBeInTheDocument()
    })

    await waitFor(() => {
      expect(screen.getByText('Ana García')).toBeInTheDocument()
    })

    expect(screen.getByText('✅ Marcar Todos Presentes')).toBeInTheDocument()
    expect(screen.getAllByText('💾 Guardar Asistencia').length).toBeGreaterThan(0)
  })

  it('navigates to Planeación and displays curricular lesson plans', async () => {
    render(
      <MemoryRouter initialEntries={['/teacher?tab=dashboard']}>
        <TeacherPortal />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('¡Bienvenido, Prof. Carlos Mendoza!')).toBeInTheDocument()
    })

    const tab = screen.getByRole('button', { name: /Planeación/i })
    fireEvent.click(tab)

    await waitFor(() => {
      expect(screen.getByText('Planeación Curricular y Unidades Didácticas')).toBeInTheDocument()
    })

    await waitFor(() => {
      expect(screen.getByText('Unidad 1: Mecánica Clásica')).toBeInTheDocument()
    })

    expect(screen.getByText('APROBADA')).toBeInTheDocument()
    expect(screen.getByText('+ Nueva Planeación Curricular')).toBeInTheDocument()
  })

  it('Phase B3: allows editing an activity in DRAFT status and preserves draft state', async () => {
    render(
      <MemoryRouter initialEntries={['/teacher?tab=activities']}>
        <TeacherPortal />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Taller 2: Leyes de Newton (Borrador)')).toBeInTheDocument()
    })

    // Expect edit button for DRAFT activity
    const editButtons = screen.getAllByRole('button', { name: /✏️ Editar/i })
    expect(editButtons.length).toBeGreaterThan(0)
    fireEvent.click(editButtons[0])

    // Verify modal opens
    await waitFor(() => {
      expect(screen.getByText('Editar Actividad Académica (Borrador)')).toBeInTheDocument()
    })

    const saveButton = screen.getByRole('button', { name: /💾 Guardar Cambios \(Borrador\)/i })
    fireEvent.click(saveButton)

    await waitFor(() => {
      expect(teacherApi.updateActivity).toHaveBeenCalledWith(
        'act-2',
        expect.objectContaining({
          title: 'Taller 2: Leyes de Newton (Borrador)',
        })
      )
    })
  })

  it('Phase B3: allows editing a curricular lesson plan and persists changes', async () => {
    render(
      <MemoryRouter initialEntries={['/teacher?tab=planning']}>
        <TeacherPortal />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Unidad 1: Mecánica Clásica')).toBeInTheDocument()
    })

    // Expect edit button for plan
    const editButton = screen.getByRole('button', { name: /✏️ Editar/i })
    fireEvent.click(editButton)

    // Verify modal opens
    await waitFor(() => {
      expect(screen.getByText('Editar Unidad de Planeación Curricular')).toBeInTheDocument()
    })

    const saveButton = screen.getByRole('button', { name: /💾 Guardar Cambios/i })
    fireEvent.click(saveButton)

    await waitFor(() => {
      expect(teacherApi.updatePlanning).toHaveBeenCalledWith(
        'plan-1',
        expect.objectContaining({
          unit_name: 'Unidad 1: Mecánica Clásica',
        })
      )
    })
  })

  it('Phase B3: navigates contextually from Mis Grupos preserving group context in target tab', async () => {
    render(
      <MemoryRouter initialEntries={['/teacher?tab=groups']}>
        <TeacherPortal />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Mis Grupos y Salones de Clase')).toBeInTheDocument()
    })

    // Click contextual Activities button for group grp-1
    const contextActBtn = screen.getByTestId('btn-context-activities-grp-1')
    fireEvent.click(contextActBtn)

    // Verify navigation to activities with group context
    await waitFor(() => {
      expect(screen.getByText('Actividades Académicas y Evaluaciones')).toBeInTheDocument()
    })
  })

  it('Phase B3: navigates contextually from Dashboard with status filter for published activities', async () => {
    render(
      <MemoryRouter initialEntries={['/teacher?tab=dashboard']}>
        <TeacherPortal />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('¡Bienvenido, Prof. Carlos Mendoza!')).toBeInTheDocument()
    })

    // Click KPI card Actividades Publicadas
    const kpiBtn = screen.getByTestId('kpi-activities')
    fireEvent.click(kpiBtn)

    // Verify tab switched to Actividades
    await waitFor(() => {
      expect(screen.getByText('Actividades Académicas y Evaluaciones')).toBeInTheDocument()
    })
  })
})
