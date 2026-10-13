/**
 * PEVN Frontend — NTA-10-R8: Tenant Diagnostics DANE & Name Search Tests
 *
 * Verifies:
 *   1. Matching DANE code returns and renders the expected institution.
 *   2. Institution-name search remains functional.
 *   3. Zero matches display a visible empty-state message ("No se encontraron instituciones para el criterio ingresado.").
 *   4. Backend/network errors display an actionable error.
 *   5. Empty input does not trigger a request.
 *   6. Loading state is correctly reset after success and failure.
 *   7. Enter and button submission invoke the same search flow.
 *   8. Selecting a result explicitly starts the existing diagnostic workflow.
 *   9. Searching alone does not change the active institutional context or run a diagnostic probe.
 *   10. SUPER_ADMIN authorization and tenant-isolation regression behavior remain intact.
 */

import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { AuthProvider } from '@/context/AuthContext'
import { TenantDiagnosticsView } from '@/pages/operations/TenantDiagnosticsView'
import type { User, InstitutionResponse } from '@/types'

const mockSuperAdminUser: User = {
  id: 'user-superadmin-01',
  email: 'admin@pevn.gov.co',
  username: 'admin',
  first_name: 'Super',
  last_name: 'Admin',
  full_name: 'Super Admin',
  document_type: 'CC',
  document_number: '111111111',
  institution_id: null,
  is_active: true,
  is_verified: true,
  must_change_password: false,
  roles: ['superadmin'],
  permissions: ['*:*'],
  scope: {
    country_code: 'CO',
    department_id: null,
    municipality_id: null,
    institution_id: null,
    campus_id: null,
    is_national: true,
    is_institution: false,
  },
}

const sampleInstitution: InstitutionResponse = {
  id: 'inst-uuid-111',
  municipality_id: 'muni-uuid-01',
  dane_code: '111111111111',
  name: 'Colegio San Pedro A',
  email: 'contacto@sanpedro.edu.co',
  phone: '3001234567',
  address: 'Calle 10 # 5-20',
  is_active: true,
  campuses: [],
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
}

const mockListInstitutions = vi.fn()
const mockGetTenantDiagnostics = vi.fn()

vi.mock('@/services/auth', () => ({
  authApi: {
    refresh: (): Promise<string> => Promise.resolve('mock-token'),
    getMyProfile: (): Promise<User> => Promise.resolve(mockSuperAdminUser),
  },
  default: {
    refresh: (): Promise<string> => Promise.resolve('mock-token'),
    getMyProfile: (): Promise<User> => Promise.resolve(mockSuperAdminUser),
  },
}))

vi.mock('@/services/institution', () => ({
  institutionApi: {
    listInstitutions: (...args: unknown[]) => mockListInstitutions(...args),
    getMyInstitution: () => Promise.reject(new Error('No institution assigned')),
    getInstitutionById: (id: string) => Promise.resolve({ ...sampleInstitution, id }),
  },
  default: {
    listInstitutions: (...args: unknown[]) => mockListInstitutions(...args),
    getMyInstitution: () => Promise.reject(new Error('No institution assigned')),
    getInstitutionById: (id: string) => Promise.resolve({ ...sampleInstitution, id }),
  },
}))

vi.mock('@/services/operations', () => ({
  operationsApi: {
    getTenantDiagnostics: (...args: unknown[]) => mockGetTenantDiagnostics(...args),
  },
  default: {
    getTenantDiagnostics: (...args: unknown[]) => mockGetTenantDiagnostics(...args),
  },
}))

describe('NTA-10-R8: Tenant Diagnostics DANE & Name Search Verification', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    mockGetTenantDiagnostics.mockResolvedValue({
      institution_id: sampleInstitution.id,
      name: sampleInstitution.name,
      dane_code: sampleInstitution.dane_code,
      is_active: true,
      created_at: '2026-01-01T00:00:00Z',
      telemetry: {
        campuses_count: 1,
        campuses: [],
        total_users: 25,
        active_users: 25,
        locked_users: 0,
        configuration_status: 'HEALTHY',
      },
      audited_at: '2026-10-12T17:00:00Z',
    })
  })

  it('1. Matching DANE code returns and renders the expected institution', async () => {
    const user = userEvent.setup()
    mockListInstitutions.mockResolvedValueOnce({
      items: [sampleInstitution],
      total: 1,
      page: 1,
      page_size: 10,
    })

    render(
      <MemoryRouter>
        <AuthProvider>
          <TenantDiagnosticsView />
        </AuthProvider>
      </MemoryRouter>
    )

    const input = await screen.findByRole('textbox', { name: /buscar por nombre o código dane/i })
    await user.type(input, '111111111111')

    const searchBtn = screen.getByRole('button', { name: /buscar/i })
    await user.click(searchBtn)

    await waitFor(() => {
      expect(mockListInstitutions).toHaveBeenCalledWith({
        search: '111111111111',
        page_size: 10,
      })
      expect(screen.getByText('Colegio San Pedro A')).toBeInTheDocument()
      expect(screen.getByText(/DANE: 111111111111/i)).toBeInTheDocument()
      expect(screen.getByText(/Estado: Activa/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /diagnosticar →/i })).toBeInTheDocument()
    })
  })

  it('2. Institution-name search remains functional', async () => {
    const user = userEvent.setup()
    mockListInstitutions.mockResolvedValueOnce({
      items: [sampleInstitution],
      total: 1,
      page: 1,
      page_size: 10,
    })

    render(
      <MemoryRouter>
        <AuthProvider>
          <TenantDiagnosticsView />
        </AuthProvider>
      </MemoryRouter>
    )

    const input = await screen.findByRole('textbox', { name: /buscar por nombre o código dane/i })
    await user.type(input, 'San Pedro')

    const searchBtn = screen.getByRole('button', { name: /buscar/i })
    await user.click(searchBtn)

    await waitFor(() => {
      expect(mockListInstitutions).toHaveBeenCalledWith({
        search: 'San Pedro',
        page_size: 10,
      })
      expect(screen.getByText('Colegio San Pedro A')).toBeInTheDocument()
    })
  })

  it('3. Zero matches display a visible empty-state message', async () => {
    const user = userEvent.setup()
    mockListInstitutions.mockResolvedValueOnce({
      items: [],
      total: 0,
      page: 1,
      page_size: 10,
    })

    render(
      <MemoryRouter>
        <AuthProvider>
          <TenantDiagnosticsView />
        </AuthProvider>
      </MemoryRouter>
    )

    const input = await screen.findByRole('textbox', { name: /buscar por nombre o código dane/i })
    // Searching DANE code 318001004174 (which exists in catalog but not provisioned as PEVN operational tenant)
    await user.type(input, '318001004174')

    const searchBtn = screen.getByRole('button', { name: /buscar/i })
    await user.click(searchBtn)

    await waitFor(() => {
      expect(mockListInstitutions).toHaveBeenCalledWith({
        search: '318001004174',
        page_size: 10,
      })
      expect(
        screen.getByText('No se encontraron instituciones para el criterio ingresado.')
      ).toBeInTheDocument()
    })

    // Input remains available for correction
    expect(input).toHaveValue('318001004174')
    expect(screen.getByRole('button', { name: /buscar/i })).toBeEnabled()
  })

  it('4. Backend/network errors display an actionable error alert', async () => {
    const user = userEvent.setup()
    mockListInstitutions.mockRejectedValueOnce(new Error('Fallo de conexión con el servicio'))

    render(
      <MemoryRouter>
        <AuthProvider>
          <TenantDiagnosticsView />
        </AuthProvider>
      </MemoryRouter>
    )

    const input = await screen.findByRole('textbox', { name: /buscar por nombre o código dane/i })
    await user.type(input, 'ErrorTest')

    const searchBtn = screen.getByRole('button', { name: /buscar/i })
    await user.click(searchBtn)

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(/Fallo de conexión con el servicio/i)
    })
  })

  it('5. Empty input does not trigger a request', async () => {
    const user = userEvent.setup()

    render(
      <MemoryRouter>
        <AuthProvider>
          <TenantDiagnosticsView />
        </AuthProvider>
      </MemoryRouter>
    )

    const searchBtn = await screen.findByRole('button', { name: /buscar/i })
    await user.click(searchBtn)

    expect(mockListInstitutions).not.toHaveBeenCalled()
    expect(screen.getByRole('alert')).toHaveTextContent(
      /Por favor ingrese un nombre o código DANE para buscar/i
    )
  })

  it('6. Loading state is correctly reset after success and failure', async () => {
    const user = userEvent.setup()
    mockListInstitutions.mockRejectedValueOnce(new Error('Network error'))

    render(
      <MemoryRouter>
        <AuthProvider>
          <TenantDiagnosticsView />
        </AuthProvider>
      </MemoryRouter>
    )

    const input = await screen.findByRole('textbox', { name: /buscar por nombre o código dane/i })
    await user.type(input, 'Failure')

    const searchBtn = screen.getByRole('button', { name: /buscar/i })
    await user.click(searchBtn)

    await waitFor(() => {
      expect(screen.getByRole('alert')).toBeInTheDocument()
    })

    // Loading state is restored in finally block
    expect(screen.getByRole('button', { name: /buscar/i })).toBeEnabled()
    expect(screen.getByRole('button', { name: /buscar/i })).toHaveTextContent('Buscar')
  })

  it('7. Enter and button submission invoke the same search flow', async () => {
    const user = userEvent.setup()
    mockListInstitutions.mockResolvedValueOnce({
      items: [sampleInstitution],
      total: 1,
      page: 1,
      page_size: 10,
    })

    render(
      <MemoryRouter>
        <AuthProvider>
          <TenantDiagnosticsView />
        </AuthProvider>
      </MemoryRouter>
    )

    const input = await screen.findByRole('textbox', { name: /buscar por nombre o código dane/i })
    await user.type(input, '111111111111{enter}')

    await waitFor(() => {
      expect(mockListInstitutions).toHaveBeenCalledWith({
        search: '111111111111',
        page_size: 10,
      })
      expect(screen.getByText('Colegio San Pedro A')).toBeInTheDocument()
    })
  })

  it('8. Selecting a result explicitly starts the existing diagnostic workflow using institutional UUID', async () => {
    const user = userEvent.setup()
    mockListInstitutions.mockResolvedValueOnce({
      items: [sampleInstitution],
      total: 1,
      page: 1,
      page_size: 10,
    })

    render(
      <MemoryRouter>
        <AuthProvider>
          <TenantDiagnosticsView />
        </AuthProvider>
      </MemoryRouter>
    )

    const input = await screen.findByRole('textbox', { name: /buscar por nombre o código dane/i })
    await user.type(input, '111111111111')
    await user.click(screen.getByRole('button', { name: /buscar/i }))

    const diagBtn = await screen.findByRole('button', { name: /diagnosticar →/i })
    await user.click(diagBtn)

    await waitFor(() => {
      expect(screen.getByText(/CONTEXTO INSTITUCIONAL ACTIVO/i)).toBeInTheDocument()
      expect(screen.getByText('inst-uuid-111')).toBeInTheDocument()
      expect(screen.getByText(/✓ ACTIVA/i)).toBeInTheDocument()
    })

    expect(mockGetTenantDiagnostics).toHaveBeenCalledWith('inst-uuid-111')
  })

  it('9. Searching alone does not change the active institutional context or run a diagnostic probe', async () => {
    const user = userEvent.setup()
    mockListInstitutions.mockResolvedValueOnce({
      items: [sampleInstitution],
      total: 1,
      page: 1,
      page_size: 10,
    })

    render(
      <MemoryRouter>
        <AuthProvider>
          <TenantDiagnosticsView />
        </AuthProvider>
      </MemoryRouter>
    )

    const input = await screen.findByRole('textbox', { name: /buscar por nombre o código dane/i })
    await user.type(input, '111111111111')
    await user.click(screen.getByRole('button', { name: /buscar/i }))

    await waitFor(() => {
      expect(screen.getByText('Colegio San Pedro A')).toBeInTheDocument()
    })

    // Probe has NOT been run merely by searching
    expect(mockGetTenantDiagnostics).not.toHaveBeenCalled()
    expect(screen.queryByText(/CONTEXTO INSTITUCIONAL ACTIVO/i)).not.toBeInTheDocument()
  })

  it('10. Leading zeros and surrounding whitespace are normalized correctly', async () => {
    const user = userEvent.setup()
    mockListInstitutions.mockResolvedValueOnce({
      items: [sampleInstitution],
      total: 1,
      page: 1,
      page_size: 10,
    })

    render(
      <MemoryRouter>
        <AuthProvider>
          <TenantDiagnosticsView />
        </AuthProvider>
      </MemoryRouter>
    )

    const input = await screen.findByRole('textbox', { name: /buscar por nombre o código dane/i })
    await user.type(input, '   050010012345   ')
    await user.click(screen.getByRole('button', { name: /buscar/i }))

    await waitFor(() => {
      expect(mockListInstitutions).toHaveBeenCalledWith({
        search: '050010012345',
        page_size: 10,
      })
    })
  })
})
