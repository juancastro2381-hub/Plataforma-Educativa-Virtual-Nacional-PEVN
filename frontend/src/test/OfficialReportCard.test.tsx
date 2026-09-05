/**
 * PEVN Frontend — Official Academic Report Cards Unit Tests (Phase 16E)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { OfficialReportCard } from '@/components/evaluation/OfficialReportCard'
import { OfficialYearEndReportCard } from '@/components/evaluation/OfficialYearEndReportCard'
import type { StudentReportCardResponse, YearEndReportCardResponse } from '@/types/evaluation'

const mockPeriodicReportCard: StudentReportCardResponse = {
  institution: {
    id: 'inst-1',
    name: 'Colegio Nacional Integrado',
    dane_code: '123456789012',
  },
  campus: {
    id: 'camp-1',
    name: 'Sede Principal',
  },
  student: {
    id: 'stud-1',
    full_name: 'Juan Camilo Pérez Gómez',
    document_number: '1098765432',
    document_type: 'TI',
    simat_code: 'SIMAT-998877',
  },
  academic_year: {
    id: 'ay-2026',
    year: 2026,
  },
  period: {
    id: 'period-1',
    period_number: 1,
    name: 'Primer Período',
    weight_percentage: 25.0,
    is_closed: true,
  },
  group: {
    id: 'grp-9a',
    name: '9-A',
    grade_name: 'Noveno',
  },
  summary: {
    average_score: 4.35,
    performance_level: 'ALTO',
    total_subjects: 2,
    passed_subjects: 2,
    failed_subjects: 0,
    rank: 3,
    total_students: 32,
    total_absences: 2,
    unexcused_absences: 1,
  },
  subjects: [
    {
      subject_id: 'sub-mat',
      subject_name: 'Matemáticas',
      area_name: 'Matemáticas y Razonamiento',
      weekly_hours: 4,
      teacher_name: 'Prof. Carlos Mendoza',
      calculated_score: 4.5,
      final_score: 4.5,
      performance_level: 'SUPERIOR',
      is_passed: true,
      adjustment_reason: null,
      total_absences: 1,
      unexcused_absences: 1,
      observations: 'Excelente participación y comprensión conceptual.',
      achievements: [
        {
          code: 'MAT-01',
          description: 'Resuelve ecuaciones de primer y segundo grado con precisión.',
          level: 'SUPERIOR',
        },
      ],
      recoveries: [],
    },
    {
      subject_id: 'sub-soc',
      subject_name: 'Ciencias Sociales',
      area_name: 'Ciencias Humanas',
      weekly_hours: 3,
      teacher_name: 'Prof. Ana Gómez',
      calculated_score: 2.8,
      final_score: 3.5,
      performance_level: 'BASICO',
      is_passed: true,
      adjustment_reason: 'Nivelación formal del período aprobada',
      total_absences: 1,
      unexcused_absences: 0,
      observations: null,
      achievements: [],
      recoveries: [
        {
          initial_score: 2.8,
          recovery_score: 4.2,
          applied_cap: 3.5,
          final_adjusted_score: 3.5,
          recovery_date: '2026-04-20',
          act_number: 'REC-001',
        },
      ],
    },
  ],
}

const mockYearEndReportCard: YearEndReportCardResponse = {
  institution: {
    id: 'inst-1',
    name: 'Colegio Nacional Integrado',
    dane_code: '123456789012',
  },
  campus: {
    id: 'camp-1',
    name: 'Sede Principal',
  },
  student: {
    id: 'stud-1',
    full_name: 'Juan Camilo Pérez Gómez',
    document_number: '1098765432',
    simat_code: 'SIMAT-998877',
  },
  academic_year: {
    id: 'ay-2026',
    year: 2026,
    status: 'ACTIVE',
  },
  group: {
    id: 'grp-9a',
    name: '9-A',
    grade_name: 'Noveno',
  },
  summary: {
    cumulative_average: 4.15,
    performance_level: 'ALTO',
    failed_subjects_count: 0,
  },
  promotion: {
    status: 'PROMOVIDO',
    acta_number: 'ACTA-2026-045',
    decision_date: '2026-11-28',
    observations: 'Promovido al grado Décimo conforme al SIEE vigente.',
  },
  subjects: [
    {
      subject_id: 'sub-mat',
      subject_name: 'Matemáticas',
      area_name: 'Área de Matemáticas',
      period_grades: {
        1: { score: 4.5, weight: 25.0 },
        2: { score: 4.0, weight: 25.0 },
        3: { score: 4.2, weight: 25.0 },
        4: { score: 4.8, weight: 25.0 },
      },
      final_annual_score: 4.38,
      performance_level: 'ALTO',
      total_absences: 2,
      unexcused_absences: 1,
    },
  ],
}

describe('OfficialReportCard (Phase 16E)', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('renders institutional headers, DANE code, and student identification', () => {
    render(<OfficialReportCard reportCard={mockPeriodicReportCard} />)

    expect(screen.getByText('Colegio Nacional Integrado')).toBeInTheDocument()
    expect(screen.getByText(/CÓDIGO DANE: 123456789012/i)).toBeInTheDocument()
    expect(screen.getByText('Juan Camilo Pérez Gómez')).toBeInTheDocument()
    expect(screen.getByText(/TI 1098765432/i)).toBeInTheDocument()
    expect(screen.getByText(/SIMAT: SIMAT-998877/i)).toBeInTheDocument()
  })

  it('renders SEALED badge when period is closed', () => {
    render(<OfficialReportCard reportCard={mockPeriodicReportCard} />)

    expect(screen.getByText(/BOLETÍN OFICIAL SELLADO INSTITUCIONALMENTE/i)).toBeInTheDocument()
  })

  it('renders PROVISIONAL badge when period is open', () => {
    const openPeriodCard = {
      ...mockPeriodicReportCard,
      period: { ...mockPeriodicReportCard.period, is_closed: false },
    }
    render(<OfficialReportCard reportCard={openPeriodCard} />)

    expect(screen.getByText(/INFORME PROVISIONAL \(PERÍODO EN CURSO\)/i)).toBeInTheDocument()
  })

  it('renders academic summary KPIs (average, rank, absences, level)', () => {
    render(<OfficialReportCard reportCard={mockPeriodicReportCard} />)

    expect(screen.getByText('4.35')).toBeInTheDocument()
    expect(screen.getByText(/Puesto en el Grupo/i)).toBeInTheDocument()
    expect(screen.getByText(/de 32/i)).toBeInTheDocument()
  })

  it('renders subject list, achievements, and recovery caps', () => {
    render(<OfficialReportCard reportCard={mockPeriodicReportCard} />)

    expect(screen.getByText('Matemáticas')).toBeInTheDocument()
    expect(screen.getByText('Ciencias Sociales')).toBeInTheDocument()
    expect(screen.getByText(/Resuelve ecuaciones de primer y segundo grado/i)).toBeInTheDocument()

    // Recovery history with SIEE cap
    expect(screen.getByText(/Historial de Nivelación \/ Recuperación/i)).toBeInTheDocument()
    expect(screen.getByText(/Tope SIEE:/i)).toBeInTheDocument()
    expect(screen.getByText(/Acta: REC-001/i)).toBeInTheDocument()
  })

  it('triggers window.print when print button is clicked', () => {
    const printSpy = vi.spyOn(window, 'print').mockImplementation(() => {})
    render(<OfficialReportCard reportCard={mockPeriodicReportCard} />)

    const printBtn = screen.getByRole('button', { name: /Imprimir \/ Guardar PDF/i })
    fireEvent.click(printBtn)

    expect(printSpy).toHaveBeenCalledTimes(1)
  })
})

describe('OfficialYearEndReportCard (Phase 16E)', () => {
  it('renders multi-period grades and cumulative annual averages', () => {
    render(<OfficialYearEndReportCard reportCard={mockYearEndReportCard} />)

    expect(screen.getByText('Matemáticas')).toBeInTheDocument()
    expect(screen.getByText('4.38')).toBeInTheDocument() // final annual score
    expect(screen.getByText('4.15')).toBeInTheDocument() // cumulative average
  })

  it('renders PROMOVIDO banner with commission act number', () => {
    render(<OfficialYearEndReportCard reportCard={mockYearEndReportCard} />)

    expect(screen.getByText('PROMOVIDO AL SIGUIENTE GRADO')).toBeInTheDocument()
    expect(screen.getByText(/Acta Comisión: #ACTA-2026-045/i)).toBeInTheDocument()
    expect(screen.queryByText(/GRADUADO — BACHILLER ACADÉMICO/i)).not.toBeInTheDocument()
  })

  it('renders GRADUADO banner strictly when backend returns GRADUADO outcome', () => {
    const graduateReport: YearEndReportCardResponse = {
      ...mockYearEndReportCard,
      promotion: {
        status: 'GRADUADO',
        acta_number: 'GRD-2026-11',
        decision_date: '2026-12-05',
        observations: 'Grado 11 superado. Título de Bachiller Académico otorgado.',
      },
    }

    render(<OfficialYearEndReportCard reportCard={graduateReport} />)

    expect(screen.getByText('GRADUADO — BACHILLER ACADÉMICO')).toBeInTheDocument()
    expect(screen.queryByText('PROMOVIDO AL SIGUIENTE GRADO')).not.toBeInTheDocument()
    expect(screen.getByText(/Acta Comisión: #GRD-2026-11/i)).toBeInTheDocument()
  })

  it('renders NO_PROMOVIDO banner when student fails grade', () => {
    const failedReport: YearEndReportCardResponse = {
      ...mockYearEndReportCard,
      summary: {
        cumulative_average: 2.75,
        performance_level: 'BAJO',
        failed_subjects_count: 3,
      },
      promotion: {
        status: 'NO_PROMOVIDO',
        acta_number: 'ACTA-REP-09',
        decision_date: '2026-11-28',
        observations: 'Reprobó 3 asignaturas fundamentales.',
      },
    }

    render(<OfficialYearEndReportCard reportCard={failedReport} />)

    expect(screen.getByText('NO PROMOVIDO / REINICIA GRADO')).toBeInTheDocument()
    expect(screen.getByText(/Reprobó 3 asignaturas fundamentales/i)).toBeInTheDocument()
  })
})
