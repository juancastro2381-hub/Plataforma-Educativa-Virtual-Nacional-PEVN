/**
 * PEVN Frontend — Directive SIEE Evaluation & Period Lifecycle Unit and Integration Tests (Phase 16D)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { DirectiveEvaluationManagementView } from '@/pages/academic/DirectiveEvaluationManagementView'
import { academicApi } from '@/services/academic'
import { evaluationApi } from '@/services/evaluation'
import type {
  AcademicPeriodResponse,
  AcademicYearResponse,
  GroupResponse,
  PeriodSheetResponse,
  SieePolicyResponse,
  SubjectResponse,
} from '@/types'

// Mock services
vi.mock('@/services/academic', () => ({
  academicApi: {
    listAcademicYears: vi.fn(),
    listGroups: vi.fn(),
    listSubjects: vi.fn(),
  },
}))

vi.mock('@/services/evaluation', () => ({
  evaluationApi: {
    getActiveSieePolicy: vi.fn(),
    listAcademicPeriods: vi.fn(),
    getPeriodSheet: vi.fn(),
    closePeriod: vi.fn(),
    unlockPeriod: vi.fn(),
  },
}))

// Mock useAuth
vi.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({
    user: { id: 'rector-1', roles: ['rector'], permissions: ['evaluations:read', 'evaluations:close_period', 'evaluations:reopen_period'] },
    hasPermission: (perm: string) => ['evaluations:read', 'evaluations:close_period', 'evaluations:reopen_period'].includes(perm),
    hasRole: () => true,
  }),
}))

const mockYears: AcademicYearResponse[] = [
  {
    id: 'ay-2026',
    institution_id: 'inst-1',
    year: 2026,
    name: 'Año Lectivo 2026',
    start_date: '2026-01-15',
    end_date: '2026-11-30',
    calendar_type: 'CALENDAR_A',
    status: 'ACTIVE',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  },
]

const mockPeriods: AcademicPeriodResponse[] = [
  {
    id: 'period-1',
    academic_year_id: 'ay-2026',
    period_number: 1,
    name: 'Primer Período',
    weight_percentage: 25.0,
    start_date: '2026-02-01',
    end_date: '2026-04-15',
    is_closed: false,
  },
  {
    id: 'period-2',
    academic_year_id: 'ay-2026',
    period_number: 2,
    name: 'Segundo Período',
    weight_percentage: 25.0,
    start_date: '2026-04-16',
    end_date: '2026-06-30',
    is_closed: true,
  },
]

const mockSieePolicy: SieePolicyResponse = {
  id: 'policy-1',
  institution_id: 'inst-1',
  academic_year_id: 'ay-2026',
  version: 1,
  name: 'SIEE Santander',
  description: 'Reglamento de evaluación',
  is_active: true,
  scale_type: 'NUMERIC_1_5',
  scale_min: 1.0,
  scale_max: 5.0,
  min_passing_score: 3.0,
  scale_decimals: 1,
  rounding_mode: 'ROUND_HALF_UP',
  period_weight_mode: 'EQUAL_WEIGHT',
  allow_remedial_exams: true,
  recovery_grade_cap: 3.5,
  max_remedial_attempts: 2,
  max_failed_subjects_for_promotion: 2,
  max_failed_core_subjects: 1,
  attendance_affects_promotion: true,
  min_attendance_percentage: 75,
  threshold_bajo_max: 2.9,
  threshold_basico_max: 3.9,
  threshold_alto_max: 4.5,
  threshold_superior_max: 5.0,
}

const mockGroups: GroupResponse[] = [
  {
    id: 'grp-9a',
    campus_id: 'campus-1',
    academic_year_id: 'ay-2026',
    grade_id: 'grade-9',
    name: '9-A',
    shift: 'MANANA',
    capacity_limit: 35,
    group_director_teacher_id: null,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  },
]

const mockSubjects: SubjectResponse[] = [
  {
    id: 'sub-mat',
    institution_id: 'inst-1',
    knowledge_area_id: 'ka-1',
    grade_id: 'grade-9',
    name: 'Matemáticas',
    weekly_hours: 4,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  },
]

const mockSheet: PeriodSheetResponse = {
  period: { id: 'period-1', name: 'Primer Período', period_number: 1, weight_percentage: 25.0, is_closed: false },
  group: { id: 'grp-9a', name: '9-A' },
  subject: { id: 'sub-mat', name: 'Matemáticas' },
  policy: { id: 'policy-1', name: 'SIEE Santander', min_passing_score: 3.0, scale_min: 1.0, scale_max: 5.0, recovery_grade_cap: 3.5 },
  activities: [],
  achievements: [],
  students: [
    {
      student_id: 'st-1',
      enrollment_id: 'enr-1',
      simat_code: 'SIM-001',
      first_name: 'Santiago',
      last_name: 'Castro',
      document_number: '1234567890',
      activity_grades: {},
      calculated_score: 4.2,
      final_score: 4.2,
      adjustment_reason: null,
      performance_level: 'ALTO',
      total_absences: 0,
      unexcused_absences: 0,
      observations: null,
      is_locked: false,
      recoveries: [],
    },
  ],
}

describe('DirectiveEvaluationManagementView (Phase 16D)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(academicApi.listAcademicYears).mockResolvedValue({ items: mockYears, total: 1 })
    vi.mocked(evaluationApi.getActiveSieePolicy).mockResolvedValue(mockSieePolicy)
    vi.mocked(academicApi.listGroups).mockResolvedValue({ items: mockGroups, total: 1 })
    vi.mocked(academicApi.listSubjects).mockResolvedValue({ items: mockSubjects, total: 1 })
    vi.mocked(evaluationApi.listAcademicPeriods).mockResolvedValue({ items: mockPeriods, total: 2 })
    vi.mocked(evaluationApi.getPeriodSheet).mockResolvedValue(mockSheet)
  })

  it('1. Renders the Directive evaluation console with period table and SIEE policy details', async () => {
    render(<DirectiveEvaluationManagementView />)

    expect(
      await screen.findByText(/Gestión Institucional de Evaluación y Períodos Académicos/i)
    ).toBeInTheDocument()

    // Period list table
    expect(await screen.findByText(/Primer Período/i)).toBeInTheDocument()
    expect(screen.getByText(/Segundo Período/i)).toBeInTheDocument()

    // Status badges
    expect(screen.getByText(/🟢 ABIERTO/i)).toBeInTheDocument()
    expect(screen.getByText(/🔒 CERRADO \/ SELLADO/i)).toBeInTheDocument()

    // Policy details
    expect(screen.getByText(/Reglamento de Evaluación Institucional SIEE/i)).toBeInTheDocument()
    expect(screen.getByText(/1.0 – 5.0 \(1 decimales\)/i)).toBeInTheDocument()
  })

  it('2. Opens confirmation modal and seals period when closing period', async () => {
    vi.mocked(evaluationApi.closePeriod).mockResolvedValue({
      period_id: 'period-1',
      is_closed: true,
    })

    render(<DirectiveEvaluationManagementView />)

    // Find "Cerrar y Sellar" button for Period 1
    const closeBtn = await screen.findByRole('button', { name: /🔒 Cerrar y Sellar/i })
    fireEvent.click(closeBtn)

    expect(screen.getByText(/Confirmación de Cierre y Sellado/i)).toBeInTheDocument()
    expect(screen.getByText(/Una vez sellado, ningún docente podrá asentar o modificar notas/i)).toBeInTheDocument()

    // Confirm close
    const confirmBtn = screen.getByRole('button', { name: /Sí, Cerrar y Sellar/i })
    fireEvent.click(confirmBtn)

    await waitFor(() => {
      expect(evaluationApi.closePeriod).toHaveBeenCalledWith('period-1')
    })
  })

  it('3. Enforces mandatory justification (min 10 chars) when reopening a sealed period', async () => {
    vi.mocked(evaluationApi.unlockPeriod).mockResolvedValue({
      period_id: 'period-2',
      is_closed: false,
    })

    render(<DirectiveEvaluationManagementView />)

    // Find "Reabrir Período" button for Period 2
    const reopenBtn = await screen.findByRole('button', { name: /🔓 Reabrir Período/i })
    fireEvent.click(reopenBtn)

    expect(screen.getByText(/Reapertura de Período Académico/i)).toBeInTheDocument()

    const submitReopenBtn = screen.getByRole('button', { name: /^Reabrir Período$/i })
    expect(submitReopenBtn).toBeDisabled()

    // Enter short justification (<10 chars)
    const textarea = screen.getByPlaceholderText(/Indique el motivo institucional/i)
    fireEvent.change(textarea, { target: { value: 'error' } })
    expect(submitReopenBtn).toBeDisabled()

    // Enter valid justification (>=10 chars)
    fireEvent.change(textarea, { target: { value: 'Acta Consejo Académico #12 - Corrección de calificaciones extemporáneas' } })
    expect(submitReopenBtn).not.toBeDisabled()

    fireEvent.click(submitReopenBtn)

    await waitFor(() => {
      expect(evaluationApi.unlockPeriod).toHaveBeenCalledWith(
        'period-2',
        expect.objectContaining({
          reason: 'Acta Consejo Académico #12 - Corrección de calificaciones extemporáneas',
        })
      )
    })
  })

  it('4. Allows institutional inspection of group period sheets', async () => {
    render(<DirectiveEvaluationManagementView />)

    const inspectBtn = await screen.findByRole('button', { name: /Consultar Sábana/i })
    fireEvent.click(inspectBtn)

    expect(await screen.findByText(/Santiago/i)).toBeInTheDocument()
    expect(screen.getAllByText('4.20').length).toBeGreaterThanOrEqual(1)
  })
})
