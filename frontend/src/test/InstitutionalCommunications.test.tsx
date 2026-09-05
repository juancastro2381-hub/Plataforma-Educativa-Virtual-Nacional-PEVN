/**
 * PEVN Frontend — Phase 15 Communications, News & School Life Integration Tests
 *
 * Tests:
 * - Student & Guardian communications feeds
 * - Read acknowledgment actions
 * - School news & article modals
 * - Personal and child Observador del Estudiante coexistence records
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { StudentCommunicationsView } from '@/pages/student/StudentCommunicationsView'
import { StudentNewsView } from '@/pages/student/StudentNewsView'
import { StudentIncidentsView } from '@/pages/student/StudentIncidentsView'
import { GuardianCommunicationsView } from '@/pages/guardian/GuardianCommunicationsView'
import { GuardianNewsView } from '@/pages/guardian/GuardianNewsView'
import { GuardianIncidentsView } from '@/pages/guardian/GuardianIncidentsView'
import { communicationApi } from '@/services/communication'

// Mock communicationApi
vi.mock('@/services/communication', () => ({
  communicationApi: {
    getStudentCommunications: vi.fn(),
    acknowledgeStudentCommunication: vi.fn(),
    getStudentNews: vi.fn(),
    getStudentIncidents: vi.fn(),
    getGuardianCommunications: vi.fn(),
    acknowledgeGuardianCommunication: vi.fn(),
    getGuardianNews: vi.fn(),
    getChildIncidents: vi.fn(),
  },
}))

const mockCommunications = {
  items: [
    {
      id: 'comm-101',
      institution_id: 'inst-1',
      title: 'Circular de Entrega de Boletines',
      content: 'La entrega de boletines se realizará el viernes a las 8:00 AM.',
      category: 'CIRCULAR_INFORMATIVA' as const,
      priority: 'ALTA' as const,
      status: 'PUBLICADO' as const,
      published_at: '2026-09-01T08:00:00Z',
      expires_at: '2026-10-01T08:00:00Z',
      requires_acknowledgment: true,
      is_pinned: true,
      author_name: 'Rectoría',
      has_read: false,
      read_at: null,
      acknowledged_at: null,
      created_at: '2026-09-01T08:00:00Z',
    },
  ],
  total: 1,
  unread_count: 1,
}

const mockNews = {
  items: [
    {
      id: 'news-101',
      institution_id: 'inst-1',
      title: 'Campeonato Intercolegiado de Fútbol 2026',
      summary: 'Nuestro equipo clasificó a la final departamental.',
      content: 'Felicitamos a los estudiantes de la selección por su desempeño.',
      category: 'DEPORTES' as const,
      cover_image_url: null,
      is_published: true,
      is_featured: true,
      published_at: '2026-09-01T08:00:00Z',
      author_name: 'Prof. De Educación Física',
      created_at: '2026-09-01T08:00:00Z',
    },
  ],
  total: 1,
}

const mockIncidents = {
  items: [
    {
      id: 'inc-101',
      institution_id: 'inst-1',
      student_id: 'st-1',
      student_name: 'Mateo Gómez Castro',
      student_document: '1098765432',
      reporter_name: 'Prof. Carlos Mendoza',
      situation_type: 'TIPO_I' as const,
      incident_date: '2026-09-01T10:00:00Z',
      location: 'Aula 8-A',
      description: 'Llegada tarde reiterada a primera hora de clase.',
      student_version: 'Dificultades con el transporte escolar.',
      pedagogical_measures: 'Diálogo reflexivo y acuerdo de puntualidad.',
      commitments: 'Organizar horarios de salida con anticipación.',
      status: 'EN_SEGUIMIENTO' as const,
      is_visible_to_guardian: true,
      is_visible_to_student: true,
      closed_at: null,
      closed_by_name: null,
      created_at: '2026-09-01T10:00:00Z',
      follow_ups: [
        {
          id: 'fol-1',
          author_user_id: 'user-t-1',
          author_name: 'Prof. Carlos Mendoza',
          follow_up_date: '2026-09-02T08:00:00Z',
          notes: 'El estudiante asistió puntualmente durante la semana.',
          created_at: '2026-09-02T08:00:00Z',
        },
      ],
    },
  ],
  total: 1,
}

describe('Phase 15 — Institutional Communications, News & School Life (Frontend)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(communicationApi.getStudentCommunications).mockResolvedValue(mockCommunications)
    vi.mocked(communicationApi.getGuardianCommunications).mockResolvedValue(mockCommunications)
    vi.mocked(communicationApi.getStudentNews).mockResolvedValue(mockNews)
    vi.mocked(communicationApi.getGuardianNews).mockResolvedValue(mockNews)
    vi.mocked(communicationApi.getStudentIncidents).mockResolvedValue(mockIncidents)
    vi.mocked(communicationApi.getChildIncidents).mockResolvedValue(mockIncidents)
  })

  it('renders Student Communications and acknowledges receipt', async () => {
    vi.mocked(communicationApi.acknowledgeStudentCommunication).mockResolvedValue({
      ...mockCommunications.items[0],
      acknowledged_at: '2026-09-01T12:00:00Z',
      has_read: true,
    })

    render(<StudentCommunicationsView />)

    await waitFor(() => {
      expect(screen.getByText('Mis Comunicados Institucionales')).toBeInTheDocument()
      expect(screen.getByText('Circular de Entrega de Boletines')).toBeInTheDocument()
      expect(screen.getByText(/Confirmar lectura obligatoria/)).toBeInTheDocument()
    })

    const ackBtn = screen.getByText(/Confirmar lectura obligatoria/)
    fireEvent.click(ackBtn)

    await waitFor(() => {
      expect(communicationApi.acknowledgeStudentCommunication).toHaveBeenCalledWith('comm-101')
      expect(screen.getByText(/Lectura confirmada/)).toBeInTheDocument()
    })
  })

  it('renders Student News Feed and opens article detail modal', async () => {
    render(<StudentNewsView />)

    await waitFor(() => {
      expect(screen.getByText('Periódico Escolar y Novedades')).toBeInTheDocument()
      expect(screen.getAllByText('Campeonato Intercolegiado de Fútbol 2026').length).toBeGreaterThan(0)
    })

    // Click read article
    const readBtn = screen.getByText('Leer artículo →')
    fireEvent.click(readBtn)

    expect(screen.getByText('Cerrar artículo')).toBeInTheDocument()
    expect(screen.getByText('Felicitamos a los estudiantes de la selección por su desempeño.')).toBeInTheDocument()

    fireEvent.click(screen.getByText('Cerrar artículo'))
    expect(screen.queryByText('Cerrar artículo')).not.toBeInTheDocument()
  })

  it('renders Student Observador de Convivencia with pedagogical measures', async () => {
    render(<StudentIncidentsView />)

    await waitFor(() => {
      expect(screen.getByText('Mi Observador de Convivencia')).toBeInTheDocument()
      expect(screen.getByText('Llegada tarde reiterada a primera hora de clase.')).toBeInTheDocument()
      expect(screen.getByText('Medidas Pedagógicas Formativas')).toBeInTheDocument()
      expect(screen.getByText('Diálogo reflexivo y acuerdo de puntualidad.')).toBeInTheDocument()
      expect(screen.getByText('Mis Compromisos')).toBeInTheDocument()
      expect(screen.getByText('El estudiante asistió puntualmente durante la semana.')).toBeInTheDocument()
    })
  })

  it('renders Guardian Observador de Convivencia for selected child', async () => {
    render(
      <GuardianIncidentsView
        selectedStudentId="st-1"
        selectedStudentName="Mateo Gómez Castro"
      />
    )

    await waitFor(() => {
      expect(screen.getByText(/Observador de Convivencia — Mateo Gómez Castro/)).toBeInTheDocument()
      expect(screen.getByText('Tipo I')).toBeInTheDocument()
      expect(screen.getByText('En Seguimiento Pedagógico')).toBeInTheDocument()
      expect(screen.getByText('Medidas Pedagógicas Aplicadas')).toBeInTheDocument()
    })
  })

  it('renders Guardian Observador empty state when no student is selected', async () => {
    render(
      <GuardianIncidentsView
        selectedStudentId={null}
        selectedStudentName={null}
      />
    )

    expect(screen.getByText('Seleccione un estudiante')).toBeInTheDocument()
  })

  it('renders Guardian Communications View and acknowledges receipt', async () => {
    vi.mocked(communicationApi.acknowledgeGuardianCommunication).mockResolvedValue({
      ...mockCommunications.items[0],
      acknowledged_at: '2026-09-01T12:00:00Z',
      has_read: true,
    })

    render(<GuardianCommunicationsView />)

    await waitFor(() => {
      expect(screen.getByText('Comunicados Institucionales')).toBeInTheDocument()
      expect(screen.getByText('Circular de Entrega de Boletines')).toBeInTheDocument()
    })

    const ackBtn = screen.getByText(/Confirmar lectura obligatoria/)
    fireEvent.click(ackBtn)

    await waitFor(() => {
      expect(communicationApi.acknowledgeGuardianCommunication).toHaveBeenCalledWith('comm-101')
      expect(screen.getByText(/Lectura confirmada/)).toBeInTheDocument()
    })
  })

  it('renders Guardian News View and opens article detail modal', async () => {
    render(<GuardianNewsView />)

    await waitFor(() => {
      expect(screen.getByText('Periódico Escolar y Noticias')).toBeInTheDocument()
      expect(screen.getAllByText('Campeonato Intercolegiado de Fútbol 2026').length).toBeGreaterThan(0)
    })

    const readBtn = screen.getByText('Leer artículo →')
    fireEvent.click(readBtn)

    expect(screen.getByText('Cerrar artículo')).toBeInTheDocument()
  })
})
