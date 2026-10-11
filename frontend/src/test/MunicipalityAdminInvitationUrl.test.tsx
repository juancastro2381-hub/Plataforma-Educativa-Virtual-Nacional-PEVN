import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { MunicipalityAdminsView } from '../pages/admin/MunicipalityAdminsView'
import { municipalityAdminApi } from '../services/municipalityAdmin'
import { useAuth } from '../hooks/useAuth'

// Mock useAuth
vi.mock('../hooks/useAuth', () => ({
  useAuth: vi.fn(),
}))

// Mock municipalityAdminApi
vi.mock('../services/municipalityAdmin', () => ({
  municipalityAdminApi: {
    listMunicipalities: vi.fn(),
    listDepartments: vi.fn(),
    listMunicipalityAdmins: vi.fn(),
    createMunicipalityAdmin: vi.fn(),
    resendInvitation: vi.fn(),
    updateStatus: vi.fn(),
    reassignMunicipality: vi.fn(),
  },
}))

describe('NTA-10-R6: MunicipalityAdminsView Invitation URL Dialog Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks()

    Object.defineProperty(window, 'location', {
      value: {
        origin: 'http://localhost:3000',
      },
      writable: true,
    })

    vi.mocked(useAuth).mockReturnValue({
      hasRole: vi.fn().mockImplementation((role: string) => role === 'department_admin'),
      hasPermission: vi.fn().mockReturnValue(true),
      user: {
        id: 'dept-admin-1',
        email: 'dept.admin@sed.gov.co',
        scope: {
          department_id: 'dept-uuid-santander',
        },
      },
    } as any)

    vi.mocked(municipalityAdminApi.listMunicipalities).mockResolvedValue([
      {
        id: 'muni-uuid-1',
        code: '68001',
        name: 'Bucaramanga',
        department_name: 'Santander',
        department_code: '68',
      },
    ] as any)

    vi.mocked(municipalityAdminApi.listMunicipalityAdmins).mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 12,
    })
  })

  it('renders activation dialog with single-origin URL and copies exact link', async () => {
    const user = userEvent.setup()

    // Mock clipboard writeText
    const writeTextMock = vi.fn().mockResolvedValue(undefined)
    Object.defineProperty(navigator, 'clipboard', {
      value: {
        writeText: writeTextMock,
      },
      writable: true,
      configurable: true,
    })

    const canonicalUrl = 'http://localhost:3000/auth/accept-invitation?token=canonical_tok_888'

    vi.mocked(municipalityAdminApi.createMunicipalityAdmin).mockResolvedValue({
      id: 'admin-new-1',
      full_name: 'Luis Soto',
      email: 'lsoto@ptocarreno.co',
      username: 'lsoto',
      municipality_name: 'PUERTO CARREÑO',
      municipality_id: 'muni-uuid-1',
      municipality_code: '99001',
      department_name: 'Vichada',
      department_code: '99',
      is_active: false,
      is_verified: false,
      roles: ['municipality_admin'],
      document_type: 'CC',
      document_number: '12345678',
      created_at: '2026-10-10T12:00:00Z',
      email_delivery_status: 'EMAIL_NOT_CONFIGURED',
      invitation_url: canonicalUrl,
      raw_invitation_token: 'canonical_tok_888',
    } as any)

    render(
      <MemoryRouter>
        <MunicipalityAdminsView />
      </MemoryRouter>
    )

    // Open create modal
    const openBtn = await screen.findByRole('button', { name: /Asignar administrador municipal/i })
    await user.click(openBtn)

    // Fill form
    const muniSelect = screen.getByRole('combobox', { name: /Seleccionar municipio \*/i })
    await user.selectOptions(muniSelect, 'muni-uuid-1')

    await user.type(screen.getByRole('textbox', { name: /Nombres \*/i }), 'Luis')
    await user.type(screen.getByRole('textbox', { name: /Apellidos \*/i }), 'Soto')
    await user.type(screen.getByRole('textbox', { name: /Correo institucional \*/i }), 'lsoto@ptocarreno.co')
    await user.type(screen.getByRole('textbox', { name: /Nombre de usuario \*/i }), 'lsoto')

    // Submit form
    const submitBtn = screen.getByRole('button', { name: /Crear cuenta e invitar/i })
    await user.click(submitBtn)

    // Verify Invitation Outcome Dialog appears
    await waitFor(() => {
      expect(screen.getByText(/Invitación de activación/i)).toBeInTheDocument()
    })

    // Check displayed URL input: MUST contain exactly one origin, NO duplication
    const urlInput = screen.getByLabelText(/Enlace de invitación de un solo uso/i) as HTMLInputElement
    expect(urlInput.value).toBe(canonicalUrl)
    expect(urlInput.value).not.toContain('http://localhost:3000http://localhost:3000')

    // Test Copy Button action
    const copyBtn = screen.getByRole('button', { name: /Copiar enlace/i })
    await user.click(copyBtn)

    expect(writeTextMock).toHaveBeenCalledWith(canonicalUrl)
    await waitFor(() => {
      expect(screen.getByText(/Copiado/i)).toBeInTheDocument()
    })
  })
})
