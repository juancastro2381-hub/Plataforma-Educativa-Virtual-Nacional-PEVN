/**
 * PEVN Frontend — Student Portal Unit and Integration Tests (Phase 14B)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { StudentPortal } from '@/pages/student/StudentPortal'
import { studentApi } from '@/services/student'
import { MemoryRouter } from 'react-router-dom'

// Mock studentApi
vi.mock('@/services/student', () => ({
  studentApi: {
    getProfile: vi.fn(),
    getDashboard: vi.fn(),
    listSubjects: vi.fn(),
    listActivities: vi.fn(),
    getActivity: vi.fn(),
    listGrades: vi.fn(),
    listAttendance: vi.fn(),
    listVirtualClassrooms: vi.fn(),
    getVirtualClassroom: vi.fn(),
    listRecordings: vi.fn(),
  },
}))

const mockProfile = {
  student_id: '11111111-2222-3333-4444-555555555555',
  user_id: 'user-st-1',
  first_name: 'Valentina',
  last_name: 'Gómez',
  full_name: 'Valentina Gómez',
  email: 'valentina.gomez@sena.edu.co',
  document_type: 'TI',
  document_number: '1098765432',
  code_simat: 'SIMAT-2026-VAL',
  birth_date: '2010-05-15',
  institution_id: 'inst-1',
  institution_name: 'Colegio Santa Librada',
  campus_name: 'Sede Principal',
  grade_name: '10',
  group_id: 'grp-10a',
  group_name: '10-A',
  academic_year_id: 'ay-2026',
  academic_year_name: '2026',
  enrollment_status: 'ACTIVE',
}

const mockSubjects = {
  items: [
    {
      subject_id: 'subj-fisica',
      name: 'Física Clásica',
      weekly_hours: 4,
      knowledge_area_name: 'Ciencias Naturales',
      teacher_id: 'tch-1',
      teacher_name: 'Prof. Carlos Mendoza',
      teacher_email: 'carlos.mendoza@santalibrada.edu.co',
    },
    {
      subject_id: 'subj-matematicas',
      name: 'Matemáticas y Trigonometría',
      weekly_hours: 5,
      knowledge_area_name: 'Matemáticas',
      teacher_id: 'tch-2',
      teacher_name: 'Prof. Diana Romero',
      teacher_email: 'diana.romero@santalibrada.edu.co',
    },
  ],
  total: 2,
}

const mockActivities = {
  items: [
    {
      id: 'act-1',
      title: 'Taller de Dinámica y Leyes de Newton',
      description: 'Resolver los ejercicios del capítulo 4 sobre fuerzas de rozamiento.',
      activity_type: 'WORKSHOP',
      status: 'PUBLISHED',
      submission_status: 'PENDING',
      publication_date: '2026-09-01T08:00:00Z',
      due_date: '2026-09-10T23:59:00Z',
      max_score: 5.0,
      score: null,
      feedback: null,
      graded_at: null,
      subject_id: 'subj-fisica',
      subject_name: 'Física Clásica',
      teacher_name: 'Prof. Carlos Mendoza',
      instructions: 'Leer con atención y adjuntar procedimiento.',
      resource_url: 'https://cdn.pevn.gov.co/docs/taller_dinamica.pdf',
    },
    {
      id: 'act-2',
      title: 'Examen de Vectores y Cinemática',
      description: 'Evaluación parcial de conceptos de movimiento uniforme acelerado.',
      activity_type: 'EXAM',
      status: 'PUBLISHED',
      submission_status: 'GRADED',
      publication_date: '2026-08-20T08:00:00Z',
      due_date: '2026-08-25T14:00:00Z',
      max_score: 5.0,
      score: 4.8,
      feedback: '¡Excelente desarrollo de las ecuaciones vectoriales!',
      graded_at: '2026-08-26T10:00:00Z',
      subject_id: 'subj-fisica',
      subject_name: 'Física Clásica',
      teacher_name: 'Prof. Carlos Mendoza',
      instructions: 'Completar en 60 minutos.',
      resource_url: null,
    },
    {
      id: 'act-3',
      title: 'Guía de Funciones Trigonométricas',
      description: 'Ejercicios de identidades trigonométricas fundamentales.',
      activity_type: 'HOMEWORK',
      status: 'PUBLISHED',
      submission_status: 'OVERDUE',
      publication_date: '2026-08-15T08:00:00Z',
      due_date: '2026-08-28T23:59:00Z',
      max_score: 5.0,
      score: null,
      feedback: null,
      graded_at: null,
      subject_id: 'subj-matematicas',
      subject_name: 'Matemáticas y Trigonometría',
      teacher_name: 'Prof. Diana Romero',
      instructions: 'Entregar en hojas cuadriculadas.',
      resource_url: null,
    },
  ],
  total: 3,
}

const mockGrades = {
  items: [
    {
      grade_id: 'gr-1',
      activity_id: 'act-2',
      activity_title: 'Examen de Vectores y Cinemática',
      activity_type: 'EXAM',
      subject_id: 'subj-fisica',
      subject_name: 'Física Clásica',
      score: 4.8,
      max_score: 5.0,
      feedback: '¡Excelente desarrollo de las ecuaciones vectoriales!',
      status: 'GRADED',
      graded_at: '2026-08-26T10:00:00Z',
      teacher_name: 'Prof. Carlos Mendoza',
    },
  ],
  total: 1,
  average_score: 4.8,
}

const mockAttendance = {
  items: [
    {
      id: 'att-1',
      attendance_date: '2026-09-01',
      status: 'PRESENT',
      remarks: 'Puntual',
      subject_name: 'Física Clásica',
      teacher_name: 'Prof. Carlos Mendoza',
    },
    {
      id: 'att-2',
      attendance_date: '2026-08-30',
      status: 'ABSENT',
      remarks: 'Cita médica justificada',
      subject_name: 'Matemáticas y Trigonometría',
      teacher_name: 'Prof. Diana Romero',
    },
  ],
  total: 2,
  summary: {
    total_sessions: 2,
    present_count: 1,
    absent_count: 1,
    excused_count: 0,
    late_count: 0,
    attendance_rate: 50.0,
  },
}

const mockVirtualClassrooms = {
  items: [
    {
      id: 'vc-1',
      title: 'Clase de Física en Vivo - Dinámica',
      description: 'Explicación interactiva de diagramas de cuerpo libre.',
      status: 'RUNNING',
      scheduled_start_time: '2026-09-01T10:00:00Z',
      scheduled_end_time: '2026-09-01T11:00:00Z',
      subject_name: 'Física Clásica',
      teacher_name: 'Prof. Carlos Mendoza',
      can_join: true,
      room_name: 'pevn-librada-fisica-10a',
      has_recordings: true,
    },
  ],
  total: 1,
}

const mockDashboard = {
  profile: mockProfile,
  total_subjects: 2,
  pending_activities_count: 1,
  overdue_activities_count: 1,
  graded_activities_count: 1,
  attendance_summary: mockAttendance.summary,
  upcoming_virtual_classrooms: mockVirtualClassrooms.items,
  upcoming_activities: mockActivities.items,
  recent_grades: mockGrades.items,
}

describe('StudentPortal Master Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(studentApi.getDashboard).mockResolvedValue(mockDashboard as any)
    vi.mocked(studentApi.listSubjects).mockResolvedValue(mockSubjects as any)
    vi.mocked(studentApi.listActivities).mockResolvedValue(mockActivities as any)
    vi.mocked(studentApi.listGrades).mockResolvedValue(mockGrades as any)
    vi.mocked(studentApi.listAttendance).mockResolvedValue(mockAttendance as any)
    vi.mocked(studentApi.listVirtualClassrooms).mockResolvedValue(mockVirtualClassrooms as any)
  })

  it('renders student header identity, SIMAT badge, and dashboard metrics', async () => {
    render(
      <MemoryRouter initialEntries={['/student?tab=dashboard']}>
        <StudentPortal />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Valentina Gómez')).toBeInTheDocument()
      expect(screen.getByText('SIMAT: SIMAT-2026-VAL')).toBeInTheDocument()
      expect(screen.getByText(/Colegio Santa Librada/i)).toBeInTheDocument()
    })

    // Check Dashboard KPI cards
    expect(screen.getByText('Tareas Pendientes')).toBeInTheDocument()
    expect(screen.getByText('Tareas Vencidas')).toBeInTheDocument()
    expect(screen.getByText('Asignaturas')).toBeInTheDocument()
    expect(screen.getByText('Asistencia Global')).toBeInTheDocument()
  })

  it('renders live class action banner with INGRESAR A CLASE button', async () => {
    render(
      <MemoryRouter initialEntries={['/student?tab=dashboard']}>
        <StudentPortal />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('INGRESAR A CLASE AHORA')).toBeInTheDocument()
    })

    expect(screen.getAllByText(/CLASE EN VIVO/i).length).toBeGreaterThanOrEqual(1)
  })

  it('switches between tabs: Mis Asignaturas, Mis Tareas, Mis Calificaciones, Mi Asistencia, Clases Virtuales, Mi Perfil', async () => {
    render(
      <MemoryRouter initialEntries={['/student?tab=dashboard']}>
        <StudentPortal />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Valentina Gómez')).toBeInTheDocument()
    })

    // Click "Mis Asignaturas"
    fireEvent.click(screen.getByText('Mis Asignaturas'))
    await waitFor(() => {
      expect(screen.getByText('Plan de Estudios y Asignaturas Matriculadas')).toBeInTheDocument()
      expect(screen.getByText('Física Clásica')).toBeInTheDocument()
      expect(screen.getByText('Matemáticas y Trigonometría')).toBeInTheDocument()
    })

    // Click "Mis Tareas"
    fireEvent.click(screen.getByText('Mis Tareas'))
    await waitFor(() => {
      expect(screen.getByText('Taller de Dinámica y Leyes de Newton')).toBeInTheDocument()
      expect(screen.getByText('Guía de Funciones Trigonométricas')).toBeInTheDocument()
    })

    // Click "Mis Calificaciones"
    fireEvent.click(screen.getByText('Mis Calificaciones'))
    await waitFor(() => {
      expect(screen.getByText('Libreta de Calificaciones y Evaluaciones')).toBeInTheDocument()
      expect(screen.getByText('Examen de Vectores y Cinemática')).toBeInTheDocument()
    })

    // Click "Mi Asistencia"
    fireEvent.click(screen.getByText('Mi Asistencia'))
    await waitFor(() => {
      expect(screen.getByText('Control y Registro de Asistencia Escolar')).toBeInTheDocument()
      expect(screen.getByText('TOTAL SESIONES')).toBeInTheDocument()
    })

    // Click "Clases Virtuales"
    fireEvent.click(screen.getByText('Clases Virtuales'))
    await waitFor(() => {
      expect(screen.getByText('Aulas Virtuales y Clases Sincrónicas')).toBeInTheDocument()
    })

    // Click "Mi Perfil"
    fireEvent.click(screen.getByText('Mi Perfil'))
    await waitFor(() => {
      expect(screen.getByText('Información de Identidad')).toBeInTheDocument()
      expect(screen.getByText('Matrícula Institucional Activa')).toBeInTheDocument()
    })
  })

  it('opens Task Detail modal with instructions and feedback', async () => {
    render(
      <MemoryRouter initialEntries={['/student?tab=dashboard']}>
        <StudentPortal />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Valentina Gómez')).toBeInTheDocument()
    })

    // Switch to tasks
    fireEvent.click(screen.getByText('Mis Tareas'))
    await waitFor(() => {
      expect(screen.getByText('Taller de Dinámica y Leyes de Newton')).toBeInTheDocument()
    })

    // Click on instructions button
    const viewButtons = screen.getAllByText('Ver Instrucciones')
    fireEvent.click(viewButtons[0])

    await waitFor(() => {
      expect(screen.getByText('📝 Instrucciones de la Actividad')).toBeInTheDocument()
      expect(screen.getByText('Cerrar')).toBeInTheDocument()
    })

    // Close modal
    fireEvent.click(screen.getByText('Cerrar'))
    await waitFor(() => {
      expect(screen.queryByText('📝 Instrucciones de la Actividad')).not.toBeInTheDocument()
    })
  })
})
