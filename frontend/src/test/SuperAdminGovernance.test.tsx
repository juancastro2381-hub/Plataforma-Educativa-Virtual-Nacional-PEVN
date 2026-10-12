/**
 * PEVN Frontend — SA-01: SuperAdmin Global Governance & Identity Tests
 *
 * Automated component tests verifying:
 *   1. Dedicated Global Governance Console rendered on Dashboard for SUPER_ADMIN.
 *   2. Identity and Scope disambiguation: '🌐 Global' and 'Nivel 100'.
 *   3. Prevention of misleading National Admin or Rector labels for SUPER_ADMIN.
 *   4. RootLayout scope badge rendering.
 *   5. Navigation access to authorized global administration links.
 */

import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { AuthProvider } from '@/context/AuthContext'
import { RootLayout } from '@/layouts/RootLayout'
import { Dashboard } from '@/pages/Dashboard'
import type { User } from '@/types'

function createSuperAdminUser(): User {
  return {
    id: 'user-superadmin-01',
    email: 'admin@pevn.edu.co',
    username: 'admin',
    first_name: 'Root',
    last_name: 'SuperAdmin',
    full_name: 'Root SuperAdmin',
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
}

function createNationalAdminUser(): User {
  return {
    id: 'user-national-admin-01',
    email: 'national_admin@pevn.edu.co',
    username: 'national_admin',
    first_name: 'National',
    last_name: 'Administrator',
    full_name: 'National Administrator',
    document_type: 'CC',
    document_number: '222222222',
    institution_id: null,
    is_active: true,
    is_verified: true,
    must_change_password: false,
    roles: ['national_admin'],
    permissions: ['institutions:read', 'institutions:create', 'users:read'],
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
}

let activeMockUser: User = createSuperAdminUser()

vi.mock('@/services/auth', () => ({
  authApi: {
    refresh: (): Promise<string> => Promise.resolve('mock-sa-token'),
    getMyProfile: (): Promise<User> => Promise.resolve(activeMockUser),
  },
  default: {
    refresh: (): Promise<string> => Promise.resolve('mock-sa-token'),
    getMyProfile: (): Promise<User> => Promise.resolve(activeMockUser),
  },
}))

vi.mock('@/services/institution', () => ({
  institutionApi: {
    getMyInstitution: () => Promise.reject(new Error('No institution assigned')),
    getInstitutionById: (id: string) => Promise.resolve({ id, name: 'Colegio Demo', is_active: true }),
  },
  default: {
    getMyInstitution: () => Promise.reject(new Error('No institution assigned')),
    getInstitutionById: (id: string) => Promise.resolve({ id, name: 'Colegio Demo', is_active: true }),
  },
}))

describe('SA-01: SUPER_ADMIN Global Platform Governance Frontend', () => {
  beforeEach(() => {
    activeMockUser = createSuperAdminUser()
    localStorage.clear()
  })

  it('renders dedicated Global Platform Governance Console for SuperAdmin on Dashboard', async () => {
    activeMockUser = createSuperAdminUser()

    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <AuthProvider>
          <Dashboard />
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/Root SuperAdmin/i)).toBeInTheDocument()
    })

    expect(
      screen.getByText(/Consola de Observabilidad, Soporte y Gobernanza de Plataforma|Centro de Comando y Gobernanza Técnica Global/i)
    ).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Directorio Global de Usuarios/i })).toHaveAttribute('href', '/admin/users')
    expect(screen.getByRole('link', { name: /Centro de Control Territorial/i })).toHaveAttribute('href', '/admin/control-center')
    expect(screen.getByRole('link', { name: /Salud de Infraestructura|Gobernanza Territorial SED/i })).toBeInTheDocument()

    // Must NOT display National Admin card label
    expect(screen.queryByText(/Nivel Nacional • Fase 3C/i)).not.toBeInTheDocument()
  })

  it('disambiguates SuperAdmin scope and level 100 identity', async () => {
    activeMockUser = createSuperAdminUser()

    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <AuthProvider>
          <Dashboard />
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/🌐 Global \(Operador Técnico del Estado \/ Plataforma\)/i)).toBeInTheDocument()
      expect(screen.getByText(/Nivel 100 • Dominio Global Técnico y Configuración/i)).toBeInTheDocument()
    })
  })

  it('renders RootLayout scope badge as Global for SuperAdmin', async () => {
    activeMockUser = createSuperAdminUser()

    render(
      <MemoryRouter initialEntries={['/']}>
        <AuthProvider>
          <RootLayout />
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('🌐 Global')).toBeInTheDocument()
      expect(screen.getByText('⚙️ Operaciones')).toBeInTheDocument()
      expect(screen.getByText('Salud Plataforma')).toBeInTheDocument()
      expect(screen.getByText('Usuarios')).toBeInTheDocument()
    })
  })

  it('renders standard National Admin card when role is national_admin', async () => {
    activeMockUser = createNationalAdminUser()

    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <AuthProvider>
          <Dashboard />
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/Nivel Nacional • Fase 3C/i)).toBeInTheDocument()
      expect(screen.getByText(/Aprovisionamiento Institucional y Rectores/i)).toBeInTheDocument()
      expect(screen.getByText(/Abrir Catálogo Nacional →/i)).toBeInTheDocument()
    })

    // Must NOT display SuperAdmin console
    expect(screen.queryByText(/GOBERNANZA GLOBAL DE LA PLATAFORMA • NIVEL 100/i)).not.toBeInTheDocument()
  })
})
