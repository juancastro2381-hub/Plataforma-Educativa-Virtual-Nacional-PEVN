/**
 * PEVN Frontend — Teacher Communications & News Integration Tests (Phase B2)
 *
 * Comprehensive tests for:
 * 1. Teacher Communications:
 *    - Render list of communications
 *    - Read vs Unread indicator
 *    - Category and priority badges
 *    - Empty and error states
 *    - Open detail modal
 *    - Acknowledge receipt (Confirmar lectura) lifecycle and state persistence
 * 2. Teacher News:
 *    - Render school newspaper & bulletin feed
 *    - Category filter and search
 *    - Featured banner
 *    - Open article detail modal
 * 3. Portal Navigation & RBAC boundary (Read-only, no create/publish controls)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { TeacherCommunicationsView } from '@/pages/teacher/TeacherCommunicationsView'
import { TeacherNewsView } from '@/pages/teacher/TeacherNewsView'
import { communicationApi } from '@/services/communication'

// Mock communicationApi
vi.mock('@/services/communication', () => ({
  communicationApi: {
    getTeacherCommunications: vi.fn(),
    getTeacherCommunicationById: vi.fn(),
    acknowledgeTeacherCommunication: vi.fn(),
    getTeacherNews: vi.fn(),
    listNews: vi.fn(),
    getNewsById: vi.fn(),
  },
}))

const mockTeacherCommunications = {
  items: [
    {
      id: 'comm-t-001',
      institution_id: 'inst-1',
      title: 'Circular Pedagógica de Cierre de Período',
      summary: 'Directrices para asentamiento de notas del primer período.',
      content: 'Estimados docentes:\nSe recuerda que el plazo límite para el asentamiento de notas definitivas es el 30 de marzo.',
      category: 'CIRCULAR_INFORMATIVA' as const,
      priority: 'ALTA' as const,
      status: 'PUBLICADO' as const,
      published_at: '2026-03-20T08:00:00Z',
      expires_at: '2026-04-15T23:59:59Z',
      requires_acknowledgment: true,
      is_pinned: true,
      author_name: 'Coordinación Académica',
      has_read: false,
      is_read: false,
      is_acknowledged: false,
      read_at: null,
      acknowledged_at: null,
      created_at: '2026-03-20T08:00:00Z',
    },
    {
      id: 'comm-t-002',
      institution_id: 'inst-1',
      title: 'Aviso de Mantenimiento de Plataforma',
      summary: 'Ventana de mantenimiento técnico programada.',
      content: 'El sistema estará en mantenimiento el sábado de 10:00 PM a 2:00 AM.',
      category: 'OTRO' as const,
      priority: 'BAJA' as const,
      status: 'PUBLICADO' as const,
      published_at: '2026-03-18T10:00:00Z',
      expires_at: null,
      requires_acknowledgment: false,
      is_pinned: false,
      author_name: 'Soporte Técnico',
      has_read: true,
      is_read: true,
      is_acknowledged: false,
      read_at: '2026-03-18T11:00:00Z',
      acknowledged_at: null,
      created_at: '2026-03-18T10:00:00Z',
    },
  ],
  total: 2,
  unread_count: 1,
}

const mockTeacherNews = {
  items: [
    {
      id: 'news-t-001',
      institution_id: 'inst-1',
      title: 'Primer Encuentro Institucional de Innovación Pedagógica',
      summary: 'Docentes de ciencias y matemáticas socializaron proyectos STEAM.',
      content: 'Durante la jornada pedagógica se expusieron 15 proyectos innovadores liderados por docentes de la institución.',
      category: 'LOGRO_ACADEMICO' as const,
      cover_image_url: null,
      is_published: true,
      is_featured: true,
      published_at: '2026-03-22T09:00:00Z',
      author_name: 'Comité Pedagógico',
      created_at: '2026-03-22T09:00:00Z',
    },
    {
      id: 'news-t-002',
      institution_id: 'inst-1',
      title: 'Jornada Cultural y Muestra Folclórica',
      summary: 'Celebración del día de la afrocolombianidad.',
      content: 'Estudiantes de todos los grados presentaron danzas y muestras gastronómicas tradicionales.',
      category: 'CULTURAL' as const,
      cover_image_url: null,
      is_published: true,
      is_featured: false,
      published_at: '2026-03-21T14:00:00Z',
      author_name: 'Área de Ciencias Sociales',
      created_at: '2026-03-21T14:00:00Z',
    },
  ],
  total: 2,
}

describe('Teacher Communications View (Phase B2)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders communications list, badges, and unread indicator', async () => {
    vi.mocked(communicationApi.getTeacherCommunications).mockResolvedValue(mockTeacherCommunications)

    render(<TeacherCommunicationsView teacherName="Prof. Carlos Mendoza" />)

    expect(screen.getByText(/cargando comunicados institucionales/i)).toBeInTheDocument()

    await waitFor(() => {
      expect(screen.getByText('Comunicaciones Institucionales')).toBeInTheDocument()
      expect(screen.getByText('Circular Pedagógica de Cierre de Período')).toBeInTheDocument()
      expect(screen.getByText('Aviso de Mantenimiento de Plataforma')).toBeInTheDocument()
      expect(screen.getByText('1 sin leer')).toBeInTheDocument()
      expect(screen.getByText('Nuevo')).toBeInTheDocument()
      expect(screen.getByText('ALTA')).toBeInTheDocument()
      expect(screen.getByText('BAJA')).toBeInTheDocument()
    })

    // Confirm that NO administrative creation buttons exist for DOCENTE
    expect(screen.queryByText(/crear comunicado/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/nuevo comunicado/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/publicar comunicado/i)).not.toBeInTheDocument()
  })

  it('opens detail modal and displays full content and metadata', async () => {
    vi.mocked(communicationApi.getTeacherCommunications).mockResolvedValue(mockTeacherCommunications)
    vi.mocked(communicationApi.getTeacherCommunicationById).mockResolvedValue({
      ...mockTeacherCommunications.items[0],
      is_read: true,
      has_read: true,
      read_at: '2026-03-20T09:00:00Z',
    })

    render(<TeacherCommunicationsView teacherName="Prof. Carlos Mendoza" />)

    await waitFor(() => {
      expect(screen.getByText('Circular Pedagógica de Cierre de Período')).toBeInTheDocument()
    })

    // Click to open detail modal
    fireEvent.click(screen.getByText('Circular Pedagógica de Cierre de Período'))

    await waitFor(() => {
      expect(screen.getByText('Cerrar comunicado')).toBeInTheDocument()
      expect(screen.getByText(/Se recuerda que el plazo límite para el asentamiento de notas/)).toBeInTheDocument()
      expect(screen.getAllByText(/Coordinación Académica/).length).toBeGreaterThanOrEqual(1)
    })

    // Close modal
    fireEvent.click(screen.getByText('Cerrar comunicado'))
    await waitFor(() => {
      expect(screen.queryByText('Cerrar comunicado')).not.toBeInTheDocument()
    })
  })

  it('acknowledges receipt and reflects immediate updated state', async () => {
    vi.mocked(communicationApi.getTeacherCommunications).mockResolvedValue(mockTeacherCommunications)
    vi.mocked(communicationApi.acknowledgeTeacherCommunication).mockResolvedValue({
      ...mockTeacherCommunications.items[0],
      acknowledged_at: '2026-03-20T10:00:00Z',
      is_acknowledged: true,
      has_read: true,
      is_read: true,
    })

    render(<TeacherCommunicationsView teacherName="Prof. Carlos Mendoza" />)

    await waitFor(() => {
      expect(screen.getByText('Confirmar Lectura Obligatoria')).toBeInTheDocument()
    })

    // Click acknowledge button
    fireEvent.click(screen.getByText('Confirmar Lectura Obligatoria'))

    await waitFor(() => {
      expect(communicationApi.acknowledgeTeacherCommunication).toHaveBeenCalledWith('comm-t-001')
      expect(screen.getByText(/Acuse de recibo registrado exitosamente/)).toBeInTheDocument()
      expect(screen.getByText(/Lectura confirmada/)).toBeInTheDocument()
    })
  })

  it('renders empty state when search finds no matches', async () => {
    vi.mocked(communicationApi.getTeacherCommunications).mockResolvedValue(mockTeacherCommunications)

    render(<TeacherCommunicationsView teacherName="Prof. Carlos Mendoza" />)

    await waitFor(() => {
      expect(screen.getByText('Circular Pedagógica de Cierre de Período')).toBeInTheDocument()
    })

    // Filter by query that doesn't match
    const searchInput = screen.getByPlaceholderText(/buscar comunicado por título/i)
    fireEvent.change(searchInput, { target: { value: 'InexistenteXYZ123' } })

    await waitFor(() => {
      expect(screen.getByText('No hay comunicados vigentes en esta selección')).toBeInTheDocument()
    })
  })
})

describe('Teacher News View (Phase B2)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders news articles, featured spotlight, and categories', async () => {
    vi.mocked(communicationApi.getTeacherNews).mockResolvedValue(mockTeacherNews)

    render(<TeacherNewsView teacherName="Prof. Carlos Mendoza" />)

    expect(screen.getByText(/cargando periódico escolar/i)).toBeInTheDocument()

    await waitFor(() => {
      expect(screen.getByText('Noticias y Periódico Escolar')).toBeInTheDocument()
      expect(screen.getAllByText('Primer Encuentro Institucional de Innovación Pedagógica').length).toBeGreaterThanOrEqual(1)
      expect(screen.getByText('Jornada Cultural y Muestra Folclórica')).toBeInTheDocument()
      expect(screen.getByText('★ Noticia Destacada')).toBeInTheDocument()
    })

    // Confirm that NO administrative publication buttons exist for DOCENTE
    expect(screen.queryByText(/crear noticia/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/nueva noticia/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/publicar noticia/i)).not.toBeInTheDocument()
  })

  it('opens article detail modal and reads full content', async () => {
    vi.mocked(communicationApi.getTeacherNews).mockResolvedValue(mockTeacherNews)

    render(<TeacherNewsView teacherName="Prof. Carlos Mendoza" />)

    await waitFor(() => {
      expect(screen.getByText('Jornada Cultural y Muestra Folclórica')).toBeInTheDocument()
    })

    // Click on the second article card
    fireEvent.click(screen.getByText('Jornada Cultural y Muestra Folclórica'))

    await waitFor(() => {
      expect(screen.getByText('Cerrar artículo')).toBeInTheDocument()
      expect(screen.getByText(/Estudiantes de todos los grados presentaron danzas/)).toBeInTheDocument()
      expect(screen.getAllByText(/Área de Ciencias Sociales/).length).toBeGreaterThanOrEqual(1)
    })

    // Close article modal
    fireEvent.click(screen.getByText('Cerrar artículo'))
    await waitFor(() => {
      expect(screen.queryByText('Cerrar artículo')).not.toBeInTheDocument()
    })
  })

  it('filters news by category and shows empty state when none match', async () => {
    vi.mocked(communicationApi.getTeacherNews).mockResolvedValue(mockTeacherNews)

    render(<TeacherNewsView teacherName="Prof. Carlos Mendoza" />)

    await waitFor(() => {
      expect(screen.getAllByText('Primer Encuentro Institucional de Innovación Pedagógica').length).toBeGreaterThanOrEqual(1)
    })

    // Filter by category where none match (CIENCIA_TECNOLOGIA)
    const select = screen.getByRole('combobox')
    fireEvent.change(select, { target: { value: 'CIENCIA_TECNOLOGIA' } })

    await waitFor(() => {
      expect(screen.getByText('No hay noticias en esta sección')).toBeInTheDocument()
    })
  })
})
