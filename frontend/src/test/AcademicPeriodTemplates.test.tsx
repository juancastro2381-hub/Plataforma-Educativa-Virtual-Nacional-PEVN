/**
 * PEVN Frontend — Academic Period Templates Test Suite (NTA-10-R7)
 *
 * Validates the Rector guided template configuration wizard:
 * 1. Action button renders and opens the wizard modal.
 * 2. Displays legal autonomy notices (Decreto 1290 de 2009, SIEE autonomy).
 * 3. Shows template options (2, 3, 4, 5 periods, and custom).
 * 4. Step 2 previews periods and detects existing periods non-destructively.
 * 5. Step 3 validates 100% weight sum dynamically.
 * 6. Step 4 enforces SIEE compliance checkbox before provisioning/activating.
 * 7. Calls academicApi.provisionPeriodTemplate with compliant payload.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AcademicPeriodsView } from '../pages/academic/AcademicPeriodsView'
import { PeriodTemplateWizardModal } from '../components/academic/PeriodTemplateWizardModal'
import { academicApi } from '../services/academic'
import { useAuth } from '../hooks/useAuth'
import type {
  AcademicYearResponse,
  PeriodTemplatePreviewResponse,
  PeriodTemplateProvisionResponse,
} from '../types'

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
    previewPeriodTemplate: vi.fn(),
    provisionPeriodTemplate: vi.fn(),
  },
}))

describe('NTA-10-R7: Academic Period Templates & SIEE Configuration Wizard', () => {
  const mockYear: AcademicYearResponse = {
    id: 'year-valparaiso-2027',
    institution_id: 'inst-valparaiso',
    year: 2027,
    name: 'Año Lectivo 2027 - I.E VALPARAISO',
    start_date: '2027-01-20',
    end_date: '2027-11-28',
    status: 'ACTIVE',
    calendar_type: 'CALENDAR_A',
    created_at: '2027-01-01T00:00:00Z',
    updated_at: '2027-01-01T00:00:00Z',
  }

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(useAuth).mockReturnValue({
      hasPermission: vi.fn().mockReturnValue(true),
      user: { id: 'u-rector', email: 'rector@valparaiso.edu.co' },
    } as any)

    vi.mocked(academicApi.listAcademicYears).mockResolvedValue({
      items: [mockYear],
      total: 1,
    })

    vi.mocked(academicApi.listAcademicPeriods).mockResolvedValue({
      items: [
        {
          id: 'period-existing-1',
          academic_year_id: 'year-valparaiso-2027',
          period_number: 1,
          name: 'Primer Período',
          weight_percentage: 25,
          start_date: '2027-01-20',
          end_date: '2027-04-03',
          is_closed: false,
          created_at: '2027-01-01T00:00:00Z',
          updated_at: '2027-01-01T00:00:00Z',
        },
      ],
      total: 1,
    })
  })

  it('renders the "✨ Configurar períodos académicos" primary button in AcademicPeriodsView', async () => {
    render(<AcademicPeriodsView />)

    await waitFor(() => {
      expect(screen.getByText(/Períodos de Evaluación y Calendario Escolar/i)).toBeInTheDocument()
    })

    const buttons = screen.getAllByRole('button', { name: /✨ Configurar períodos académicos/i })
    expect(buttons.length).toBeGreaterThan(0)
    expect(buttons[0]).not.toBeDisabled()
  })

  it('opens PeriodTemplateWizardModal when clicking "✨ Configurar períodos académicos"', async () => {
    render(<AcademicPeriodsView />)

    await waitFor(() => {
      expect(screen.getByText(/Períodos de Evaluación y Calendario Escolar/i)).toBeInTheDocument()
    })

    const buttons = screen.getAllByRole('button', { name: /✨ Configurar períodos académicos/i })
    await userEvent.click(buttons[0])

    // Modal should now be open
    expect(screen.getByText('Configuración de Períodos Académicos y SIEE')).toBeInTheDocument()
    // Autonomy banner visible
    expect(screen.getByText(/Principios Legales y Autonomía Institucional/i)).toBeInTheDocument()
  })

  it('displays standard template options with non-mandatory MEN disclaimer', () => {
    render(
      <PeriodTemplateWizardModal
        isOpen={true}
        onClose={vi.fn()}
        academicYear={mockYear}
        onSuccess={vi.fn()}
      />
    )

    // Check step 1 content
    expect(screen.getByText(/4 Períodos — Cuatro Períodos de Evaluación/i)).toBeInTheDocument()
    expect(screen.getByText(/2 Períodos — Semestral/i)).toBeInTheDocument()
    expect(screen.getByText(/3 Períodos — Tres Períodos de Evaluación/i)).toBeInTheDocument()
    expect(screen.getByText(/5 Períodos — Cinco Períodos de Evaluación/i)).toBeInTheDocument()
    expect(screen.getByText(/Configuración Personalizada/i)).toBeInTheDocument()

    // MEN disclaimer
    expect(
      screen.getByText(/Plantilla de referencia institucional — no obligatoria por el MEN/i)
    ).toBeInTheDocument()
  })

  it('previews template and identifies existing periods non-destructively in Step 2', async () => {
    const mockPreviewResponse: PeriodTemplatePreviewResponse = {
      academic_year_id: 'year-valparaiso-2027',
      academic_year_name: 'Año Lectivo 2027 - I.E VALPARAISO',
      academic_year_year: 2027,
      academic_year_start: '2027-01-20',
      academic_year_end: '2027-11-28',
      calendar_type: 'CALENDAR_A',
      academic_year_status: 'ACTIVE',
      template_type: 'PERIODS_4',
      template_label: '4 Períodos — Cuatro Períodos de Evaluación',
      regulatory_disclaimer:
        'Configuración sujeta a la autonomía institucional consagrada en el Decreto 1290 de 2009.',
      existing_periods: [
        {
          id: 'period-existing-1',
          academic_year_id: 'year-valparaiso-2027',
          period_number: 1,
          name: 'Primer Período',
          start_date: '2027-01-20',
          end_date: '2027-04-03',
          weight_percentage: 25,
          is_closed: false,
        },
      ],
      proposed_periods: [
        {
          period_number: 1,
          name: 'Primer Período',
          weight_percentage: 25,
          start_date: '2027-01-20',
          end_date: '2027-04-03',
          is_existing: true,
          existing_period_id: 'period-existing-1',
        },
        {
          period_number: 2,
          name: 'Segundo Período',
          weight_percentage: 25,
          start_date: '2027-04-06',
          end_date: '2027-06-19',
          is_existing: false,
        },
        {
          period_number: 3,
          name: 'Tercer Período',
          weight_percentage: 25,
          start_date: '2027-07-06',
          end_date: '2027-09-18',
          is_existing: false,
        },
        {
          period_number: 4,
          name: 'Cuarto Período',
          weight_percentage: 25,
          start_date: '2027-09-21',
          end_date: '2027-11-28',
          is_existing: false,
        },
      ],
      total_weight_existing: 25,
      total_weight_proposed: 75,
      total_weight_combined: 100,
      has_conflicts: false,
      conflict_messages: [],
      is_complete: true,
    }

    vi.mocked(academicApi.previewPeriodTemplate).mockResolvedValue(mockPreviewResponse)

    render(
      <PeriodTemplateWizardModal
        isOpen={true}
        onClose={vi.fn()}
        academicYear={mockYear}
        onSuccess={vi.fn()}
      />
    )

    // Click on "Generar Propuesta no Destructiva →"
    const nextBtn = screen.getByRole('button', { name: /Generar Propuesta no Destructiva →/i })
    await userEvent.click(nextBtn)

    // Should call preview API
    await waitFor(() => {
      expect(academicApi.previewPeriodTemplate).toHaveBeenCalledWith('year-valparaiso-2027', {
        template_type: 'PERIODS_4',
        custom_period_count: undefined,
      })
    })

    // Step 2 should display reconciliation notes and badge
    await waitFor(() => {
      expect(screen.getByText('Garantía de Preservación de Datos Existentes')).toBeInTheDocument()
      expect(screen.getByText(/Períodos en base de datos:/i)).toBeInTheDocument()
      expect(screen.getByText('Existente (Conservado)')).toBeInTheDocument()
    })
  })

  it('validates 100% total weight and controls advancing to Step 4', async () => {
    const mockPreviewResponse: PeriodTemplatePreviewResponse = {
      academic_year_id: 'year-valparaiso-2027',
      academic_year_name: 'Año Lectivo 2027 - I.E VALPARAISO',
      academic_year_year: 2027,
      academic_year_start: '2027-01-20',
      academic_year_end: '2027-11-28',
      calendar_type: 'CALENDAR_A',
      academic_year_status: 'ACTIVE',
      template_type: 'PERIODS_4',
      template_label: '4 Períodos',
      regulatory_disclaimer: 'Plantilla de referencia institucional',
      existing_periods: [],
      proposed_periods: [
        { period_number: 1, name: 'P1', weight_percentage: 25, start_date: '2027-01-20', end_date: '2027-04-03', is_existing: false },
        { period_number: 2, name: 'P2', weight_percentage: 25, start_date: '2027-04-06', end_date: '2027-06-19', is_existing: false },
        { period_number: 3, name: 'P3', weight_percentage: 25, start_date: '2027-07-06', end_date: '2027-09-18', is_existing: false },
        { period_number: 4, name: 'P4', weight_percentage: 25, start_date: '2027-09-21', end_date: '2027-11-28', is_existing: false },
      ],
      total_weight_existing: 0,
      total_weight_proposed: 100,
      total_weight_combined: 100,
      has_conflicts: false,
      conflict_messages: [],
      is_complete: true,
    }
    vi.mocked(academicApi.previewPeriodTemplate).mockResolvedValue(mockPreviewResponse)

    render(
      <PeriodTemplateWizardModal
        isOpen={true}
        onClose={vi.fn()}
        academicYear={mockYear}
        onSuccess={vi.fn()}
      />
    )

    // Go to step 2
    await userEvent.click(screen.getByRole('button', { name: /Generar Propuesta no Destructiva →/i }))
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Personalizar y Ajustar Fechas\/Pesos →/i })).toBeInTheDocument()
    })

    // Go to step 3
    await userEvent.click(screen.getByRole('button', { name: /Personalizar y Ajustar Fechas\/Pesos →/i }))
    await waitFor(() => {
      expect(screen.getByText('Ajuste de Ponderaciones y Fechas')).toBeInTheDocument()
    })

    // Balance bar should show 100%
    expect(screen.getByText(/Ponderación Total: 100.00% \/ 100%/i)).toBeInTheDocument()

    // Next step button is enabled
    const toStep4Btn = screen.getByRole('button', { name: /Conformidad SIEE y Activación →/i })
    expect(toStep4Btn).not.toBeDisabled()

    // Now change one weight to make sum != 100%
    const weightInputs = screen.getAllByRole('spinbutton')
    await userEvent.clear(weightInputs[0])
    await userEvent.type(weightInputs[0], '20')

    // Sum is now 95%
    await waitFor(() => {
      expect(screen.getByText(/Ponderación Total: 95.00% \/ 100%/i)).toBeInTheDocument()
    })

    // Next button should now be disabled
    expect(toStep4Btn).toBeDisabled()
  })

  it('requires SIEE compliance confirmation in Step 4 before activation', async () => {
    const mockPreviewResponse: PeriodTemplatePreviewResponse = {
      academic_year_id: 'year-valparaiso-2027',
      academic_year_name: 'Año Lectivo 2027 - I.E VALPARAISO',
      academic_year_year: 2027,
      academic_year_start: '2027-01-20',
      academic_year_end: '2027-11-28',
      calendar_type: 'CALENDAR_A',
      academic_year_status: 'ACTIVE',
      template_type: 'SEMESTRAL_2',
      template_label: '2 Períodos — Semestral',
      regulatory_disclaimer: 'Plantilla de referencia institucional',
      existing_periods: [],
      proposed_periods: [
        { period_number: 1, name: 'Primer Semestre', weight_percentage: 50, start_date: '2027-01-20', end_date: '2027-06-15', is_existing: false },
        { period_number: 2, name: 'Segundo Semestre', weight_percentage: 50, start_date: '2027-07-01', end_date: '2027-11-28', is_existing: false },
      ],
      total_weight_existing: 0,
      total_weight_proposed: 100,
      total_weight_combined: 100,
      has_conflicts: false,
      conflict_messages: [],
      is_complete: true,
    }
    vi.mocked(academicApi.previewPeriodTemplate).mockResolvedValue(mockPreviewResponse)
    const mockProvisionResponse: PeriodTemplateProvisionResponse = {
      academic_year_id: 'year-valparaiso-2027',
      provisioned_count: 2,
      retained_count: 0,
      total_periods: 2,
      total_weight: 100,
      is_activated: true,
      academic_year_status: 'ACTIVE',
      periods: [],
      compliance_summary: {
        confirmed_by_rector: true,
        siee_version: '',
      },
    }
    vi.mocked(academicApi.provisionPeriodTemplate).mockResolvedValue(mockProvisionResponse)

    const handleSuccess = vi.fn().mockResolvedValue(undefined)
    const handleClose = vi.fn()

    render(
      <PeriodTemplateWizardModal
        isOpen={true}
        onClose={handleClose}
        academicYear={mockYear}
        onSuccess={handleSuccess}
      />
    )

    // Select Semestral
    await userEvent.click(screen.getByText(/2 Períodos — Semestral/i))

    // Step 1 -> 2
    await userEvent.click(screen.getByRole('button', { name: /Generar Propuesta no Destructiva →/i }))
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Personalizar y Ajustar Fechas\/Pesos →/i })).toBeInTheDocument()
    })

    // Step 2 -> 3
    await userEvent.click(screen.getByRole('button', { name: /Personalizar y Ajustar Fechas\/Pesos →/i }))
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Conformidad SIEE y Activación →/i })).toBeInTheDocument()
    })

    // Step 3 -> 4
    await userEvent.click(screen.getByRole('button', { name: /Conformidad SIEE y Activación →/i }))
    await waitFor(() => {
      expect(screen.getByText('Resumen de la Configuración a Registrar')).toBeInTheDocument()
    })

    // Checkbox is unchecked initially
    const confirmCheckbox = screen.getByRole('checkbox')
    expect(confirmCheckbox).not.toBeChecked()

    // Activation button must be disabled
    const activateBtn = screen.getByRole('button', { name: /✨ Aprovisionar y Activar Configuración/i })
    expect(activateBtn).toBeDisabled()

    // Check the compliance confirmation
    await userEvent.click(confirmCheckbox)
    expect(confirmCheckbox).toBeChecked()

    // Activation button should now be enabled
    expect(activateBtn).not.toBeDisabled()

    // Click activation button
    await userEvent.click(activateBtn)

    // Verify API called with SIEE metadata and activate_immediately = true
    await waitFor(() => {
      expect(academicApi.provisionPeriodTemplate).toHaveBeenCalledWith(
        'year-valparaiso-2027',
        expect.objectContaining({
          template_type: 'SEMESTRAL_2',
          periods: expect.arrayContaining([
            expect.objectContaining({ period_number: 1, weight_percentage: 50 }),
            expect.objectContaining({ period_number: 2, weight_percentage: 50 }),
          ]),
          activate_immediately: true,
          compliance: expect.objectContaining({
            confirmed_by_rector: true,
          }),
        })
      )
    })

    // Success callback called
    await waitFor(() => {
      expect(handleSuccess).toHaveBeenCalled()
      expect(handleClose).toHaveBeenCalled()
    })
  })
})
