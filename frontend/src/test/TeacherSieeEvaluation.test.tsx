/**
 * PEVN Frontend — Teacher SIEE Evaluation Unit and Integration Tests (Phase 16D)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { TeacherSieeEvaluationView } from '@/pages/teacher/TeacherSieeEvaluationView'
import { evaluationApi } from '@/services/evaluation'
import type { TeacherAssignmentItemResponse } from '@/types/teacher'
import type { PeriodSheetResponse, SieePolicyResponse, AcademicPeriodResponse } from '@/types'

// Mock evaluationApi
vi.mock('@/services/evaluation', () => ({
  evaluationApi: {
    listAcademicPeriods: vi.fn(),
    getActiveSieePolicy: vi.fn(),
    getPeriodSheet: vi.fn(),
    savePeriodGrades: vi.fn(),
    recordRecoveryGrade: vi.fn(),
  },
}))

// Mock useAuth
vi.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({
    user: { id: 'teacher-user-1', roles: ['teacher'], permissions: ['evaluations:read', 'evaluations:grade', 'evaluations:recovery'] },
    hasPermission: (perm: string) => ['evaluations:read', 'evaluations:grade', 'evaluations:recovery'].includes(perm),
    hasRole: () => false,
  }),
}))

const mockAssignments: TeacherAssignmentItemResponse[] = [
  {
    id: 'asg-1',
    teacher_id: 't-1',
    subject_id: 'sub-mat',
    subject_name: 'Matemáticas',
    knowledge_area_name: 'Matemáticas',
    group_id: 'grp-9a',
    group_name: '9-A',
    grade_name: 'Noveno',
    campus_name: 'Sede Principal',
    shift: 'MAÑANA',
    academic_year_id: 'ay-2026',
    academic_year_name: '2026',
    weekly_hours: 4,
    is_active: true,
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
  name: 'SIEE Institucional Santander',
  description: 'Reglamento de evaluación institucional',
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

const mockSheetOpen: PeriodSheetResponse = {
  period: {
    id: 'period-1',
    name: 'Primer Período',
    period_number: 1,
    weight_percentage: 25.0,
    is_closed: false,
  },
  group: {
    id: 'grp-9a',
    name: '9-A',
    grade_name: 'Noveno',
  },
  subject: {
    id: 'sub-mat',
    name: 'Matemáticas',
  },
  policy: {
    id: 'policy-1',
    name: 'SIEE Institucional Santander',
    min_passing_score: 3.0,
    scale_min: 1.0,
    scale_max: 5.0,
    recovery_grade_cap: 3.5,
  },
  activities: [
    {
      id: 'act-1',
      title: 'Taller Álgebra',
      activity_type: 'WORKSHOP',
      max_score: 5.0,
      weight_percentage: 50.0,
      due_date: '2026-03-10',
    },
  ],
  achievements: [],
  students: [
    {
      student_id: 'st-1',
      enrollment_id: 'enr-1',
      simat_code: 'SIM-001',
      first_name: 'Mateo',
      last_name: 'Gómez',
      document_number: '1098765432',
      activity_grades: { 'act-1': 4.5 },
      calculated_score: 4.5,
      final_score: 4.5,
      adjustment_reason: null,
      performance_level: 'ALTO',
      total_absences: 1,
      unexcused_absences: 0,
      observations: null,
      is_locked: false,
      recoveries: [],
    },
    {
      student_id: 'st-2',
      enrollment_id: 'enr-2',
      simat_code: 'SIM-002',
      first_name: 'Valentina',
      last_name: 'López',
      document_number: '1098765433',
      activity_grades: { 'act-1': 2.0 },
      calculated_score: 2.0,
      final_score: 2.0,
      adjustment_reason: null,
      performance_level: 'BAJO',
      total_absences: 4,
      unexcused_absences: 2,
      observations: null,
      is_locked: false,
      recoveries: [],
    },
  ],
}

describe('TeacherSieeEvaluationView (Phase 16D)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(evaluationApi.listAcademicPeriods).mockResolvedValue({
      items: mockPeriods,
      total: mockPeriods.length,
    })
    vi.mocked(evaluationApi.getActiveSieePolicy).mockResolvedValue(mockSieePolicy)
    vi.mocked(evaluationApi.getPeriodSheet).mockResolvedValue(mockSheetOpen)
  })

  it('1. Renders the SIEE evaluation sheet with students, calculated and final scores', async () => {
    render(<TeacherSieeEvaluationView assignments={mockAssignments} />)

    expect(await screen.findByText(/Evaluación Periódica SIEE y Consolidación/i)).toBeInTheDocument()
    expect(await screen.findByText(/Gómez, Mateo/i)).toBeInTheDocument()
    expect(screen.getByText(/López, Valentina/i)).toBeInTheDocument()

    // Calculated scores
    expect(screen.getByText('4.50')).toBeInTheDocument()
    expect(screen.getByText('2.00')).toBeInTheDocument()

    // Performance level badges
    expect(screen.getByText('ALTO')).toBeInTheDocument()
    expect(screen.getByText('BAJO')).toBeInTheDocument()

    // Status badge
    expect(screen.getByText(/PERÍODO ABIERTO/i)).toBeInTheDocument()
  })

  it('2. Shows SIEE institutional policy parameters when toggled', async () => {
    render(<TeacherSieeEvaluationView assignments={mockAssignments} />)

    const toggleBtn = await screen.findByText(/Ver Parámetros SIEE/i)
    fireEvent.click(toggleBtn)

    expect(screen.getByText(/Reglas Institucionales del SIEE/i)).toBeInTheDocument()
    expect(screen.getByText(/1.0 – 5.0/i)).toBeInTheDocument()
    expect(screen.getByText(/3.5 \(Cap SIEE\)/i)).toBeInTheDocument()
  })

  it('3. Disables grade inputs and displays warning when period is closed', async () => {
    const closedSheet: PeriodSheetResponse = {
      ...mockSheetOpen,
      period: { ...mockSheetOpen.period, id: 'period-2', is_closed: true },
    }
    vi.mocked(evaluationApi.getPeriodSheet).mockResolvedValue(closedSheet)

    render(<TeacherSieeEvaluationView assignments={mockAssignments} />)

    // Switch period to closed period
    const periodSelect = await screen.findByLabelText(/Período Académico:/i)
    fireEvent.change(periodSelect, { target: { value: 'period-2' } })

    expect(await screen.findByText(/PERÍODO CERRADO \(SELLADO\)/i)).toBeInTheDocument()
    expect(screen.getByText(/Período Académico Sellado Institucionalmente:/i)).toBeInTheDocument()

    // Input must be disabled
    const scoreInputs = screen.getAllByRole('spinbutton')
    scoreInputs.forEach((input) => {
      expect(input).toBeDisabled()
    })
  })

  it('4. Requires adjustment reason when final score differs from calculated score', async () => {
    render(<TeacherSieeEvaluationView assignments={mockAssignments} />)

    expect(await screen.findByText(/Gómez, Mateo/i)).toBeInTheDocument()

    // Modify final score from 4.5 to 4.8 without adjustment reason
    const scoreInputs = screen.getAllByRole('spinbutton')
    const mateoFinalInput = scoreInputs.find((i) => (i as HTMLInputElement).value === '4.5')
    expect(mateoFinalInput).toBeDefined()

    fireEvent.change(mateoFinalInput!, { target: { value: '4.8' } })

    // Save button should now be enabled
    const saveBtn = screen.getByRole('button', { name: /Guardar Calificaciones/i })
    expect(saveBtn).not.toBeDisabled()

    fireEvent.click(saveBtn)

    // Validation error should block save
    expect(
      await screen.findByText(/Debe registrar un motivo pedagógico de ajuste para Mateo Gómez/i)
    ).toBeInTheDocument()

    // Backend save was NOT called
    expect(evaluationApi.savePeriodGrades).not.toHaveBeenCalled()
  })

  it('5. Successfully saves grades when adjustment reason is provided', async () => {
    vi.mocked(evaluationApi.savePeriodGrades).mockResolvedValue({
      saved_count: 2,
      period_id: 'period-1',
      group_id: 'grp-9a',
      subject_id: 'sub-mat',
    })

    render(<TeacherSieeEvaluationView assignments={mockAssignments} />)

    expect(await screen.findByText(/Gómez, Mateo/i)).toBeInTheDocument()

    // Modify final score
    const scoreInputs = screen.getAllByRole('spinbutton')
    const mateoFinalInput = scoreInputs.find((i) => (i as HTMLInputElement).value === '4.5')
    fireEvent.change(mateoFinalInput!, { target: { value: '4.8' } })

    // Provide adjustment reason
    const reasonInputs = screen.getAllByPlaceholderText(/Explicación del ajuste \*/i)
    fireEvent.change(reasonInputs[0], { target: { value: 'Excelente participación y trabajo colaborativo' } })

    // Click save
    const saveBtn = screen.getByRole('button', { name: /Guardar Calificaciones/i })
    fireEvent.click(saveBtn)

    await waitFor(() => {
      expect(evaluationApi.savePeriodGrades).toHaveBeenCalledWith(
        expect.objectContaining({
          period_id: 'period-1',
          group_id: 'grp-9a',
          subject_id: 'sub-mat',
          items: expect.arrayContaining([
            expect.objectContaining({
              student_id: 'st-1',
              final_score: 4.8,
              adjustment_reason: 'Excelente participación y trabajo colaborativo',
            }),
          ]),
        })
      )
    })
  })

  it('6. Opens recovery modal displaying original score and SIEE recovery cap', async () => {
    render(<TeacherSieeEvaluationView assignments={mockAssignments} />)

    expect(await screen.findByText(/López, Valentina/i)).toBeInTheDocument()

    // Valentina has failing grade (2.0 < 3.0), so "+ Nivelar" button is available
    const recoverBtn = screen.getByRole('button', { name: /\+ Nivelar/i })
    fireEvent.click(recoverBtn)

    expect(await screen.findByText(/Registrar Nivelación \/ Recuperación/i)).toBeInTheDocument()
    expect(screen.getByText(/Nota inicial del período:/i)).toBeInTheDocument()
    expect(screen.getByText(/Tope máximo SIEE \(Cap\):/i)).toBeInTheDocument()
    expect(screen.getByText(/3.50/i)).toBeInTheDocument()
  })
})
