import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { CoordinatorsView } from '../pages/academic/CoordinatorsView'
import { coordinatorApi } from '../services/coordinator'
import { useAuth } from '../hooks/useAuth'

// Mock useAuth
vi.mock('../hooks/useAuth', () => ({
  useAuth: vi.fn(),
}))

// Mock coordinatorApi
vi.mock('../services/coordinator', () => ({
  coordinatorApi: {
    listCoordinators: vi.fn(),
    getCoordinator: vi.fn(),
    listCampuses: vi.fn(),
    createCoordinator: vi.fn(),
    resendInvitation: vi.fn(),
    updateCoordinatorStatus: vi.fn(),
  },
}))

describe('NTA-10-R9: CoordinatorsView and Invitation Lifecycle Frontend Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks()

    Object.defineProperty(window, 'location', {
      value: {
        origin: 'http://localhost:3000',
      },
      writable: true,
    })

    vi.mocked(useAuth).mockReturnValue({
      hasRole: vi.fn().mockImplementation((role: string) => role === 'rector'),
      hasPermission: vi.fn().mockReturnValue(true),
      user: {
        id: 'rector-uuid-1',
        email: 'rector@inst.edu.co',
        role_name: 'rector',
        institution_id: 'inst-uuid-1',
      },
    } as any)

    vi.mocked(coordinatorApi.listCampuses).mockResolvedValue([
      {
        id: 'campus-uuid-1',
        institution_id: 'inst-uuid-1',
        name: 'Sede Principal',
        dane_sede_code: '1110010001',
        is_main: true,
        is_active: true,
      },
      {
        id: 'campus-uuid-2',
        institution_id: 'inst-uuid-1',
        name: 'Sede B - Rural',
        dane_sede_code: '1110010002',
        is_main: false,
        is_active: true,
      },
    ])

    vi.mocked(coordinatorApi.listCoordinators).mockResolvedValue({
      items: [
        {
          id: 'coord-uuid-1',
          institution_id: 'inst-uuid-1',
          campus_id: null,
          campus_name: null,
          username: 'agomez',
          first_name: 'Ana María',
          last_name: 'Gómez',
          full_name: 'Ana María Gómez',
          email: 'agomez@inst.edu.co',
          role: 'coordinator',
          document_type: 'CC',
          document_number: '52123456',
          is_active: true,
          is_verified: true,
          invitation_id: 'inv-uuid-1',
          invitation_status: 'accepted',
          raw_invitation_token: null,
          invitation_url: null,
          email_delivery_status: 'SENT',
          created_at: '2026-10-10T10:00:00Z',
        },
      ],
      total: 1,
      page: 1,
      page_size: 20,
    })
  })

  it('renders coordinator list with institutional and campus scope badges', async () => {
    render(
      <MemoryRouter>
        <CoordinatorsView />
      </MemoryRouter>
    )

    expect(await screen.findByText('Coordinación Académica e Institucional')).toBeInTheDocument()
    expect(await screen.findByText('Ana María Gómez')).toBeInTheDocument()
    expect(screen.getByText('🌐 Institución Completa')).toBeInTheDocument()
    expect(screen.getByText('Activo')).toBeInTheDocument()
  })

  it('allows Rector to open invitation dialog, submit institution-wide invitation, and copy link', async () => {
    const user = userEvent.setup()

    const writeTextMock = vi.fn().mockResolvedValue(undefined)
    Object.defineProperty(navigator, 'clipboard', {
      value: {
        writeText: writeTextMock,
      },
      writable: true,
      configurable: true,
    })

    vi.mocked(coordinatorApi.listCoordinators).mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
    })

    const canonicalUrl = 'http://localhost:3000/auth/accept-invitation?token=coord_tok_sec_123'

    vi.mocked(coordinatorApi.createCoordinator).mockResolvedValue({
      id: 'coord-uuid-new',
      institution_id: 'inst-uuid-1',
      campus_id: null,
      campus_name: null,
      username: 'cruiz',
      first_name: 'Carlos',
      last_name: 'Ruiz',
      full_name: 'Carlos Ruiz',
      email: 'cruiz@inst.edu.co',
      role: 'coordinator',
      document_type: 'CC',
      document_number: '79987654',
      is_active: false,
      is_verified: false,
      invitation_id: 'inv-uuid-new',
      invitation_status: 'pending',
      raw_invitation_token: 'coord_tok_sec_123',
      invitation_url: canonicalUrl,
      email_delivery_status: 'EMAIL_NOT_CONFIGURED',
      created_at: '2026-10-10T12:00:00Z',
    })

    render(
      <MemoryRouter>
        <CoordinatorsView />
      </MemoryRouter>
    )

    // Open invitation dialog
    const inviteBtn = await screen.findByRole('button', { name: /Invitar Coordinador/i })
    await user.click(inviteBtn)

    expect(screen.getByText('Invitar Coordinador Académico')).toBeInTheDocument()

    // Fill form
    await user.type(screen.getByPlaceholderText(/Ej\. Carlos Alberto/i), 'Carlos')
    await user.type(screen.getByPlaceholderText(/Ej\. Gómez Restrepo/i), 'Ruiz')
    await user.type(screen.getByPlaceholderText(/Número de cédula o documento/i), '79987654')
    await user.type(screen.getByPlaceholderText(/coordinador@institucion\.edu\.co/i), 'cruiz@inst.edu.co')

    // Submit form
    const submitBtn = screen.getByRole('button', { name: /Emitir Invitación/i })
    await user.click(submitBtn)

    expect(coordinatorApi.createCoordinator).toHaveBeenCalledWith({
      first_name: 'Carlos',
      last_name: 'Ruiz',
      document_type: 'CC',
      document_number: '79987654',
      email: 'cruiz@inst.edu.co',
      campus_id: null,
    })

    // Outcome modal
    await waitFor(() => {
      expect(screen.getByText('Invitación Criptográfica Generada')).toBeInTheDocument()
      expect(screen.getAllByText(/Carlos Ruiz/i).length).toBeGreaterThanOrEqual(1)
    })

    // Copy link action
    const copyBtn = screen.getByRole('button', { name: /Copiar/i })
    await user.click(copyBtn)

    expect(writeTextMock).toHaveBeenCalledWith(canonicalUrl)
  })

  it('allows Rector to select specific campus scope for a coordinator', async () => {
    const user = userEvent.setup()

    vi.mocked(coordinatorApi.listCoordinators).mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
    })

    vi.mocked(coordinatorApi.createCoordinator).mockResolvedValue({
      id: 'coord-uuid-campus',
      institution_id: 'inst-uuid-1',
      campus_id: 'campus-uuid-2',
      campus_name: 'Sede B - Rural',
      username: 'emorales',
      first_name: 'Elena',
      last_name: 'Morales',
      full_name: 'Elena Morales',
      email: 'emorales@inst.edu.co',
      role: 'coordinator',
      document_type: 'CC',
      document_number: '10203040',
      is_active: false,
      is_verified: false,
      invitation_id: 'inv-uuid-2',
      invitation_status: 'pending',
      raw_invitation_token: 'campus_tok_789',
      invitation_url: 'http://localhost:3000/auth/accept-invitation?token=campus_tok_789',
      email_delivery_status: 'EMAIL_NOT_CONFIGURED',
      created_at: '2026-10-10T12:00:00Z',
    })

    render(
      <MemoryRouter>
        <CoordinatorsView />
      </MemoryRouter>
    )

    const inviteBtn = await screen.findByRole('button', { name: /Invitar Coordinador/i })
    await user.click(inviteBtn)

    await user.type(screen.getByPlaceholderText(/Ej\. Carlos Alberto/i), 'Elena')
    await user.type(screen.getByPlaceholderText(/Ej\. Gómez Restrepo/i), 'Morales')
    await user.type(screen.getByPlaceholderText(/Número de cédula o documento/i), '10203040')
    await user.type(screen.getByPlaceholderText(/coordinador@institucion\.edu\.co/i), 'emorales@inst.edu.co')

    // Click "Sede Específica" radio button
    const campusRadio = screen.getByLabelText(/Sede Específica/i)
    await user.click(campusRadio)

    // Select campus from dropdown
    const campusSelect = screen.getByRole('combobox', { name: /Seleccionar sede educativa/i })
    await user.selectOptions(campusSelect, 'campus-uuid-2')

    // Submit
    const submitBtn = screen.getByRole('button', { name: /Emitir Invitación/i })
    await user.click(submitBtn)

    expect(coordinatorApi.createCoordinator).toHaveBeenCalledWith({
      first_name: 'Elena',
      last_name: 'Morales',
      document_type: 'CC',
      document_number: '10203040',
      email: 'emorales@inst.edu.co',
      campus_id: 'campus-uuid-2',
    })
  })

  it('enforces exclusivity UX: disables scope choices and submit when global coordinator exists', async () => {
    const user = userEvent.setup()

    // Default mock from beforeEach has an active global coordinator (Ana María Gómez)
    render(
      <MemoryRouter>
        <CoordinatorsView />
      </MemoryRouter>
    )

    const inviteBtn = await screen.findByRole('button', { name: /Invitar Coordinador/i })
    await user.click(inviteBtn)

    // Warning banner is displayed
    expect(screen.getByText(/Exclusividad Institucional Activa/i)).toBeInTheDocument()
    expect(screen.getAllByText(/Ana María Gómez/i).length).toBeGreaterThanOrEqual(2)

    // Scope radios are disabled
    const globalRadio = screen.getByLabelText(/Toda la Institución \(Global\)/i)
    const campusRadio = screen.getByLabelText(/Sede Específica/i)
    expect(globalRadio).toBeDisabled()
    expect(campusRadio).toBeDisabled()

    // Submit button is disabled
    const submitBtn = screen.getByRole('button', { name: /Emitir Invitación/i })
    expect(submitBtn).toBeDisabled()
  })

  it('enforces exclusivity UX: disables global radio and labels occupied campus when campus coordinator exists', async () => {
    const user = userEvent.setup()

    vi.mocked(coordinatorApi.listCoordinators).mockResolvedValue({
      items: [
        {
          id: 'coord-campus-1',
          institution_id: 'inst-uuid-1',
          campus_id: 'campus-uuid-1',
          campus_name: 'Sede Principal',
          username: 'jrodriguez',
          first_name: 'Jorge',
          last_name: 'Rodríguez',
          full_name: 'Jorge Rodríguez',
          email: 'jrodriguez@inst.edu.co',
          role: 'coordinator',
          document_type: 'CC',
          document_number: '88776655',
          is_active: true,
          is_verified: true,
          invitation_id: 'inv-c1',
          invitation_status: 'accepted',
          raw_invitation_token: null,
          invitation_url: null,
          email_delivery_status: 'SENT',
          created_at: '2026-10-10T10:00:00Z',
        },
      ],
      total: 1,
      page: 1,
      page_size: 20,
    })

    render(
      <MemoryRouter>
        <CoordinatorsView />
      </MemoryRouter>
    )

    const inviteBtn = await screen.findByRole('button', { name: /Invitar Coordinador/i })
    await user.click(inviteBtn)

    // Global radio is disabled
    const globalRadio = screen.getByLabelText(/Toda la Institución \(Global\)/i)
    expect(globalRadio).toBeDisabled()

    // Explanatory note is visible
    expect(screen.getByText(/Alcance global deshabilitado/i)).toBeInTheDocument()

    // Campus select shows occupied campus as disabled
    const campusSelect = screen.getByRole('combobox', { name: /Seleccionar sede educativa/i })
    expect(campusSelect).toBeInTheDocument()

    const occupiedOption = screen.getByRole('option', { name: /Sede Principal.*Asignada a: Jorge Rodríguez/i })
    expect(occupiedOption).toBeDisabled()

    // Vacant campus option is enabled
    const vacantOption = screen.getByRole('option', { name: /Sede B - Rural/i })
    expect(vacantOption).not.toBeDisabled()
  })

  it('displays actionable error message when createCoordinator rejects with conflict', async () => {
    const user = userEvent.setup()

    vi.mocked(coordinatorApi.listCoordinators).mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
    })

    vi.mocked(coordinatorApi.createCoordinator).mockRejectedValue(
      new Error('La sede educativa ya cuenta con un Coordinador Académico asignado. Cada sede educativa solo puede tener un coordinador asignado.')
    )

    render(
      <MemoryRouter>
        <CoordinatorsView />
      </MemoryRouter>
    )

    const inviteBtn = await screen.findByRole('button', { name: /Invitar Coordinador/i })
    await user.click(inviteBtn)

    await user.type(screen.getByPlaceholderText(/Ej\. Carlos Alberto/i), 'Carlos')
    await user.type(screen.getByPlaceholderText(/Ej\. Gómez Restrepo/i), 'Ruiz')
    await user.type(screen.getByPlaceholderText(/Número de cédula o documento/i), '79987654')
    await user.type(screen.getByPlaceholderText(/coordinador@institucion\.edu\.co/i), 'cruiz@inst.edu.co')

    const submitBtn = screen.getByRole('button', { name: /Emitir Invitación/i })
    await user.click(submitBtn)

    // Error alert is displayed in modal
    expect(await screen.findByText(/La sede educativa ya cuenta con un Coordinador Académico asignado/i)).toBeInTheDocument()
  })

  it('hides create button when user lacks coordinator management role/permission', () => {
    vi.mocked(useAuth).mockReturnValue({
      hasRole: vi.fn().mockReturnValue(false),
      hasPermission: vi.fn().mockReturnValue(false),
      user: {
        id: 'student-uuid',
        role_name: 'student',
      },
    } as any)

    render(
      <MemoryRouter>
        <CoordinatorsView />
      </MemoryRouter>
    )

    expect(screen.queryByRole('button', { name: /Invitar Coordinador/i })).not.toBeInTheDocument()
  })
})
