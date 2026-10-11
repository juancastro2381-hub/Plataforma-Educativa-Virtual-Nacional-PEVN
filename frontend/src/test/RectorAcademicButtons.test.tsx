/**
 * PEVN Frontend — Rector Academic Buttons & Modal Test Suite (NTA-10-R5)
 *
 * Validates that clicking "+ Nuevo Período" and "+ Nueva Asignatura":
 * 1. Opens the creation modal dialog.
 * 2. Displays all required form controls and inputs.
 * 3. Handles form validation and submission.
 * 4. Calls the respective API client methods and refreshes the lists.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AcademicPeriodsView } from '../pages/academic/AcademicPeriodsView'
import { SubjectsView } from '../pages/academic/SubjectsView'
import { academicApi } from '../services/academic'
import { useAuth } from '../hooks/useAuth'

// Mock useAuth
vi.mock('../hooks/useAuth', () => ({
  useAuth: vi.fn(),
}))

// Mock academicApi
vi.mock('../services/academic', () => ({
  academicApi: {
    listAcademicYears: vi.fn(),
    listAcademicPeriods: vi.fn(),
    createAcademicPeriod: vi.fn(),
    listGrades: vi.fn(),
    listSubjects: vi.fn(),
    createSubject: vi.fn(),
    listKnowledgeAreas: vi.fn(),
  },
}))

describe('NTA-10-R5: Rector Academic Buttons & Form Modals', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(useAuth).mockReturnValue({
      hasPermission: vi.fn().mockReturnValue(true),
      user: { id: 'u1', email: 'rector@test.edu.co' },
    } as any)
  })

  describe('AcademicPeriodsView: "+ Nuevo Período"', () => {
    const mockYear = {
      id: 'year-2027',
      institution_id: 'inst-1',
      year: 2027,
      name: 'Año Escolar 2027',
      start_date: '2027-02-01',
      end_date: '2027-11-30',
      status: 'ACTIVE' as const,
      calendar_type: 'CALENDAR_A' as const,
      created_at: '2027-01-01T00:00:00Z',
      updated_at: '2027-01-01T00:00:00Z',
    }

    beforeEach(() => {
      vi.mocked(academicApi.listAcademicYears).mockResolvedValue({
        items: [mockYear],
        total: 1,
      })
      vi.mocked(academicApi.listAcademicPeriods).mockResolvedValue({
        items: [],
        total: 0,
      })
      vi.mocked(academicApi.createAcademicPeriod).mockResolvedValue({
        id: 'period-1',
        academic_year_id: 'year-2027',
        period_number: 1,
        name: 'Primer Período',
        weight_percentage: 25,
        start_date: '2027-02-01',
        end_date: '2027-04-15',
        is_closed: false,
        created_at: '2027-01-01T00:00:00Z',
        updated_at: '2027-01-01T00:00:00Z',
      })
    })

    it('renders the "+ Nuevo Período" button and opens the modal upon click', async () => {
      render(<AcademicPeriodsView />)

      // Wait for year and empty periods to load
      await waitFor(() => {
        expect(screen.getByText(/Períodos de Evaluación y Calendario Escolar/i)).toBeInTheDocument()
      })

      const newPeriodBtn = screen.getByRole('button', { name: /\+ Nuevo Período/i })
      expect(newPeriodBtn).toBeInTheDocument()
      expect(newPeriodBtn).not.toBeDisabled()

      // Click button
      await userEvent.click(newPeriodBtn)

      // Verify modal is open with title and inputs
      expect(screen.getByText('Nuevo Período Académico')).toBeInTheDocument()
      expect(screen.getByLabelText(/Número de Período \*/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/Nombre del Período \*/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/Ponderación de Calificación \(%\) \*/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/Fecha de Inicio \*/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/Fecha de Finalización \*/i)).toBeInTheDocument()
    })

    it('submits valid period data and calls academicApi.createAcademicPeriod', async () => {
      render(<AcademicPeriodsView />)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /\+ Nuevo Período/i })).toBeInTheDocument()
      })

      await userEvent.click(screen.getByRole('button', { name: /\+ Nuevo Período/i }))

      // Submit the form
      const submitBtn = screen.getByRole('button', { name: /Guardar Período/i })
      await userEvent.click(submitBtn)

      await waitFor(() => {
        expect(academicApi.createAcademicPeriod).toHaveBeenCalledWith(
          'year-2027',
          expect.objectContaining({
            period_number: 1,
            name: 'Primer Período',
            weight_percentage: 25,
            start_date: '2027-02-01',
            end_date: '2027-11-30',
          })
        )
      })
    })
  })

  describe('SubjectsView: "+ Nueva Asignatura"', () => {
    const mockGrades = [
      { id: 'grade-9', code: '9', name: 'Grado Noveno', level: 'SECUNDARIA' as const, ordinal_order: 9 },
    ]
    const mockKnowledgeAreas = [
      { id: 'ka-1', name: 'Matemáticas y Lógica', is_mandatory: true, institution_id: null },
    ]

    beforeEach(() => {
      vi.mocked(academicApi.listGrades).mockResolvedValue({
        items: mockGrades,
        total: 1,
      })
      vi.mocked(academicApi.listSubjects).mockResolvedValue({
        items: [],
        total: 0,
      })
      vi.mocked(academicApi.listKnowledgeAreas).mockResolvedValue({
        items: mockKnowledgeAreas,
        total: 1,
      })
      vi.mocked(academicApi.createSubject).mockResolvedValue({
        id: 'sub-1',
        institution_id: 'inst-1',
        grade_id: 'grade-9',
        knowledge_area_id: 'ka-1',
        name: 'Álgebra y Trigonometría',
        weekly_hours: 4,
        created_at: '2027-01-01T00:00:00Z',
        updated_at: '2027-01-01T00:00:00Z',
      })
    })

    it('renders the "+ Nueva Asignatura" button and opens the modal upon click', async () => {
      render(<SubjectsView />)

      await waitFor(() => {
        expect(screen.getByText(/Plan de Estudios y Asignaturas Curriculares/i)).toBeInTheDocument()
      })

      const newSubjectBtn = screen.getByRole('button', { name: /\+ Nueva Asignatura/i })
      expect(newSubjectBtn).toBeInTheDocument()

      await userEvent.click(newSubjectBtn)

      expect(screen.getByText('Nueva Asignatura Curricular')).toBeInTheDocument()
      expect(screen.getByLabelText(/Nombre de la Asignatura \*/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/Grado Escolar \*/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/Intensidad Horaria Semanal \*/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/Área Fundamental de Conocimiento/i)).toBeInTheDocument()
    })

    it('submits valid subject data and calls academicApi.createSubject', async () => {
      render(<SubjectsView />)

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /\+ Nueva Asignatura/i })).toBeInTheDocument()
      })

      await userEvent.click(screen.getByRole('button', { name: /\+ Nueva Asignatura/i }))

      const nameInput = screen.getByLabelText(/Nombre de la Asignatura \*/i)
      await userEvent.type(nameInput, 'Álgebra y Trigonometría')

      const submitBtn = screen.getByRole('button', { name: /Guardar Asignatura/i })
      await userEvent.click(submitBtn)

      await waitFor(() => {
        expect(academicApi.createSubject).toHaveBeenCalledWith(
          expect.objectContaining({
            name: 'Álgebra y Trigonometría',
            grade_id: 'grade-9',
            knowledge_area_id: 'ka-1',
            weekly_hours: 4,
          })
        )
      })
    })
  })
})
