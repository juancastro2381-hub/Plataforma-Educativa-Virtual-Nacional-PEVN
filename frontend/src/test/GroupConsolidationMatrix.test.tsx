/**
 * PEVN Frontend — Group Consolidation Matrix Unit Tests (Phase 16E)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { GroupConsolidationMatrix } from '@/components/evaluation/GroupConsolidationMatrix'
import type { GroupConsolidationMatrixResponse } from '@/types/evaluation'

const mockMatrixData: GroupConsolidationMatrixResponse = {
  group: {
    id: 'grp-9a',
    name: '9-A',
    grade_name: 'Noveno',
  },
  period: {
    id: 'period-1',
    period_number: 1,
    name: 'Primer Período',
  },
  subjects: [
    { id: 'sub-mat', name: 'Matemáticas' },
    { id: 'sub-esp', name: 'Lengua Castellana' },
    { id: 'sub-cie', name: 'Ciencias Naturales' },
  ],
  students: [
    {
      student_id: 'st-1',
      student_name: 'Álvarez María',
      simat_code: 'SIMAT-001',
      subjects: {
        'sub-mat': { score: 4.8, level: 'SUPERIOR' },
        'sub-esp': { score: 4.5, level: 'ALTO' },
        'sub-cie': { score: 4.6, level: 'SUPERIOR' },
      },
      average: 4.63,
      total_absences: 0,
      rank: 1,
    },
    {
      student_id: 'st-2',
      student_name: 'Pérez Juan',
      simat_code: 'SIMAT-002',
      subjects: {
        'sub-mat': { score: 3.5, level: 'BASICO' },
        'sub-esp': { score: 3.8, level: 'BASICO' },
        'sub-cie': { score: 4.0, level: 'ALTO' },
      },
      average: 3.77,
      total_absences: 3,
      rank: 2,
    },
    {
      student_id: 'st-3',
      student_name: 'Torres Carlos',
      simat_code: null,
      subjects: {
        'sub-mat': { score: 2.5, level: 'BAJO' },
        'sub-esp': { score: 2.8, level: 'BAJO' },
        'sub-cie': { score: 3.0, level: 'BASICO' },
      },
      average: 2.77,
      total_absences: 5,
      rank: 3,
    },
  ],
  total_students: 3,
}

describe('GroupConsolidationMatrix (Phase 16E)', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('renders group header, period information, and student count', () => {
    render(<GroupConsolidationMatrix matrix={mockMatrixData} />)

    expect(screen.getByText(/Sábana de Notas Consolidada — 9-A \(Primer Período\)/i)).toBeInTheDocument()
    expect(screen.getByText(/3 estudiantes registrados • 3 asignaturas evaluadas/i)).toBeInTheDocument()
    expect(screen.getByText(/Noveno — GRUPO 9-A • PRIMER PERÍODO/i)).toBeInTheDocument()
  })

  it('renders table columns for all subjects and student rows with rankings', () => {
    render(<GroupConsolidationMatrix matrix={mockMatrixData} />)

    // Check subjects
    expect(screen.getByTitle('Matemáticas')).toBeInTheDocument()
    expect(screen.getByTitle('Lengua Castellana')).toBeInTheDocument()
    expect(screen.getByTitle('Ciencias Naturales')).toBeInTheDocument()

    // Check students
    expect(screen.getByText('Álvarez María')).toBeInTheDocument()
    expect(screen.getByText('SIMAT-001')).toBeInTheDocument()
    expect(screen.getByText('4.63')).toBeInTheDocument()

    expect(screen.getByText('Pérez Juan')).toBeInTheDocument()
    expect(screen.getByText('3.77')).toBeInTheDocument()

    expect(screen.getByText('Torres Carlos')).toBeInTheDocument()
    expect(screen.getByText('2.77')).toBeInTheDocument()
  })

  it('handles CSV export download trigger correctly', () => {
    // Mock URL.createObjectURL and URL.revokeObjectURL
    const createObjectUrlMock = vi.fn().mockReturnValue('blob:http://localhost/test-uuid')
    const revokeObjectUrlMock = vi.fn()
    window.URL.createObjectURL = createObjectUrlMock
    window.URL.revokeObjectURL = revokeObjectUrlMock

    // Mock HTMLAnchorElement click
    const clickSpy = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})

    render(<GroupConsolidationMatrix matrix={mockMatrixData} />)

    const csvBtn = screen.getByRole('button', { name: /Exportar a CSV/i })
    fireEvent.click(csvBtn)

    expect(createObjectUrlMock).toHaveBeenCalled()
    expect(clickSpy).toHaveBeenCalled()
    expect(revokeObjectUrlMock).toHaveBeenCalled()
  })

  it('triggers window.print when print button is clicked', () => {
    const printSpy = vi.spyOn(window, 'print').mockImplementation(() => {})
    render(<GroupConsolidationMatrix matrix={mockMatrixData} />)

    const printBtn = screen.getByRole('button', { name: /Imprimir \/ PDF/i })
    fireEvent.click(printBtn)

    expect(printSpy).toHaveBeenCalledTimes(1)
  })

  it('renders empty message when no students exist in matrix', () => {
    const emptyMatrix: GroupConsolidationMatrixResponse = {
      ...mockMatrixData,
      students: [],
      total_students: 0,
    }

    render(<GroupConsolidationMatrix matrix={emptyMatrix} />)

    expect(
      screen.getByText(/No se registran notas de estudiantes en este salón/i)
    ).toBeInTheDocument()
  })
})
