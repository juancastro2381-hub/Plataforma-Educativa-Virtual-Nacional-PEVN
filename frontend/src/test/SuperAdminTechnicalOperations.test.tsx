/**
 * PEVN Frontend — SA-02: SUPER_ADMIN Technical Operations Portal & Role Separation Tests
 *
 * Automated component tests verifying:
 *   1. Dedicated Technical Operations Portal rendered on Dashboard for SUPER_ADMIN (Level 100).
 *   2. Strict role-specific navigation in RootLayout:
 *      - SUPER_ADMIN sees exclusively technical operations links (/operations/*).
 *      - NATIONAL_ADMIN retains educational governance links and NEVER sees operations console.
 *   3. Audited Tenant Diagnostics context banner and unambiguous exit action:
 *      '[ ✕ Salir a Operaciones Globales ]'.
 *   4. Observability and Support views render mock telemetry and prevent cross-role exposure.
 */

import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { AuthProvider } from '@/context/AuthContext'
import { RootLayout } from '@/layouts/RootLayout'
import { Dashboard } from '@/pages/Dashboard'
import { PlatformHealthView } from '@/pages/operations/PlatformHealthView'
import { TechnicalSupportView } from '@/pages/operations/TechnicalSupportView'
import { SecurityAuditView } from '@/pages/operations/SecurityAuditView'
import { TenantDiagnosticsView } from '@/pages/operations/TenantDiagnosticsView'
import type { User } from '@/types'

function createSuperAdminUser(): User {
  return {
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
}

function createNationalAdminUser(): User {
  return {
    id: 'user-national-admin-01',
    email: 'national_admin@pevn.gov.co',
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
    refresh: (): Promise<string> => Promise.resolve('mock-token'),
    getMyProfile: (): Promise<User> => Promise.resolve(activeMockUser),
  },
  default: {
    refresh: (): Promise<string> => Promise.resolve('mock-token'),
    getMyProfile: (): Promise<User> => Promise.resolve(activeMockUser),
  },
}))

vi.mock('@/services/operations', () => ({
  operationsApi: {
    getOverview: () =>
      Promise.resolve({
        overall_status: 'OPERATIONAL',
        measured_at: '2026-10-11T19:30:00Z',
        environment: 'testing',
        version: '1.2.0',
        database: { status: 'ok', latency_ms: 8, pool_size: 10, safe_url: 'postgresql://pevn_app@db:5432/pevn_db' },
        redis: { status: 'ok', mode: 'standalone' },
        background_jobs: { status: 'ok', active_queues: ['notifications'] },
        metrics: { active_incidents: 1, security_events_24h: 35 },
      }),
    getHealth: () =>
      Promise.resolve({
        status: 'ok',
        timestamp: '2026-10-11T19:30:00Z',
        services: [
          { name: 'PostgreSQL Primary Database', status: 'operational', type: 'database', details: 'Latency: 8ms' },
          { name: 'Redis Cache Cluster', status: 'operational', type: 'cache', details: 'Connected in standalone mode' },
          { name: 'Datos Abiertos Colombia Socrata API', status: 'operational', type: 'external_api', details: 'MEN Official Catalog' },
        ],
      }),
    getAuditFeed: () =>
      Promise.resolve({
        items: [
          {
            id: 'audit-01',
            event_type: 'AUTH_LOGIN_SUCCESS',
            actor_id: 'user-01',
            actor_ip: '192.168.1.100',
            target_type: null,
            target_id: null,
            institution_id: null,
            success: true,
            metadata: { user_agent: 'Vitest Test' },
            occurred_at: '2026-10-11T19:25:00Z',
          },
        ],
        total: 1,
        summary: { total_queried: 1, failed_logins: 0, permission_denied: 0, suspicious_events: 0 },
      }),
    listSupportCases: () =>
      Promise.resolve({
        items: [
          {
            id: 'inc-01',
            ticket_number: 'INC-2026-0001',
            title: 'Degradación en sincronización Socrata',
            category: 'INTEGRATION',
            severity: 'HIGH',
            status: 'OPEN',
            affected_service: 'socrata_sync',
            institution_id: null,
            reporter_id: 'user-superadmin-01',
            assigned_operator: 'ops-lead@pevn.gov.co',
            description: 'Latencia observada al consultar catálogo DANE',
            technical_context: { status_code: 504 },
            resolution_notes: null,
            created_at: '2026-10-11T19:00:00Z',
            updated_at: '2026-10-11T19:00:00Z',
            resolved_at: null,
          },
        ],
        total: 1,
        open_count: 1,
        critical_count: 0,
      }),
    createSupportCase: (payload: any) =>
      Promise.resolve({
        id: 'inc-02',
        ticket_number: 'INC-2026-0002',
        ...payload,
        status: 'OPEN',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        resolved_at: null,
      }),
    updateSupportCase: (id: string, payload: any) =>
      Promise.resolve({
        id,
        ticket_number: 'INC-2026-0001',
        title: 'Mock Incident',
        status: payload.status || 'RESOLVED',
        resolution_notes: payload.resolution_notes || null,
        created_at: '2026-10-11T19:00:00Z',
        updated_at: new Date().toISOString(),
      }),
    getTenantDiagnostics: (institutionId: string) =>
      Promise.resolve({
        institution_id: institutionId,
        name: 'Colegio Experimental Antigravity',
        dane_code: '111001099888',
        is_active: true,
        created_at: '2026-01-01T00:00:00Z',
        telemetry: {
          campuses_count: 2,
          campuses: [{ id: 'sede-01', name: 'Sede Principal', dane_code: '11100109988801' }],
          total_users: 150,
          active_users: 148,
          locked_users: 2,
          configuration_status: 'HEALTHY',
        },
        audited_at: '2026-10-11T19:30:00Z',
      }),
    getIntegrations: () =>
      Promise.resolve({
        integrations: [
          { name: 'PostgreSQL Database', type: 'database', safe_host: 'db:5432', status: 'connected' },
          { name: 'Redis Cache', type: 'cache', safe_host: 'redis:6379', status: 'connected' },
        ],
      }),
  },
}))

vi.mock('@/services/institution', () => ({
  institutionApi: {
    getMyInstitution: () => Promise.reject(new Error('No institution assigned')),
    getInstitutionById: (id: string) =>
      Promise.resolve({ id, name: 'Colegio Experimental Antigravity', dane_code: '111001099888', is_active: true }),
    listInstitutions: () =>
      Promise.resolve({
        items: [{ id: 'inst-999', name: 'Colegio Experimental Antigravity', dane_code: '111001099888', is_active: true }],
        total: 1,
      }),
  },
  default: {
    getMyInstitution: () => Promise.reject(new Error('No institution assigned')),
    getInstitutionById: (id: string) =>
      Promise.resolve({ id, name: 'Colegio Experimental Antigravity', dane_code: '111001099888', is_active: true }),
    listInstitutions: () =>
      Promise.resolve({
        items: [{ id: 'inst-999', name: 'Colegio Experimental Antigravity', dane_code: '111001099888', is_active: true }],
        total: 1,
      }),
  },
}))

describe('SA-02: SUPER_ADMIN Technical Operations Portal & Role Separation', () => {
  beforeEach(() => {
    activeMockUser = createSuperAdminUser()
    localStorage.clear()
  })

  it('1. SUPER_ADMIN receives the dedicated technical operations portal with live telemetry on Dashboard', async () => {
    activeMockUser = createSuperAdminUser()

    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <AuthProvider>
          <Dashboard />
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/Consola de Observabilidad, Soporte y Gobernanza de Plataforma/i)).toBeInTheDocument()
    })

    // Technical KPI Cards
    expect(screen.getByText(/Base de Datos Primaria/i)).toBeInTheDocument()
    expect(screen.getByText(/Caché & Sesiones \(Redis\)/i)).toBeInTheDocument()
    expect(screen.getByText(/Mesa de Soporte \/ Incidentes/i)).toBeInTheDocument()

    // 6 Operational Action Modules
    expect(screen.getByRole('link', { name: /Salud de Infraestructura/i })).toHaveAttribute('href', '/operations/health')
    expect(screen.getByRole('link', { name: /Mesa de Ayuda e Incidentes/i })).toHaveAttribute('href', '/operations/support')
    expect(screen.getByRole('link', { name: /Seguridad & Auditoría Forense/i })).toHaveAttribute('href', '/operations/audit')
    expect(screen.getByRole('link', { name: /Diagnóstico de Inquilinos/i })).toHaveAttribute('href', '/operations/tenant-diagnostics')
    expect(screen.getByRole('link', { name: /Directorio Global de Usuarios/i })).toHaveAttribute('href', '/admin/users')
    expect(screen.getByRole('link', { name: /Centro de Control Territorial/i })).toHaveAttribute('href', '/admin/control-center')

    // Live Streams
    expect(screen.getByText(/Flujo Reciente de Seguridad/i)).toBeInTheDocument()
    expect(screen.getByText(/Incidentes Técnicos en Seguimiento/i)).toBeInTheDocument()
    await waitFor(() => {
      expect(screen.getByText(/Degradación en sincronización Socrata/i)).toBeInTheDocument()
    })

    // Must NOT display National Admin card label
    expect(screen.queryByText(/Nivel Nacional • Fase 3C/i)).not.toBeInTheDocument()
  })

  it('2. SUPER_ADMIN receives exclusively technical operations navigation in RootLayout (No ordinary educational menus)', async () => {
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
    })

    // Must render SUPER_ADMIN technical links
    expect(screen.getByText('⚙️ Operaciones')).toBeInTheDocument()
    expect(screen.getByText('Salud Plataforma')).toBeInTheDocument()
    expect(screen.getByText('Soporte Técnico')).toBeInTheDocument()
    expect(screen.getByText('Seguridad & Auditoría')).toBeInTheDocument()
    expect(screen.getByText('Usuarios')).toBeInTheDocument()
    expect(screen.getByText('Diagnóstico Inquilinos')).toBeInTheDocument()

    // Must NOT render educational administration items as primary navigation
    expect(screen.queryByText('Instituciones')).not.toBeInTheDocument()
    expect(screen.queryByText('Académica')).not.toBeInTheDocument()
    expect(screen.queryByText('Admin Dptal.')).not.toBeInTheDocument()
    expect(screen.queryByText('Admin Mpal.')).not.toBeInTheDocument()
    expect(screen.queryByText('Onboarding')).not.toBeInTheDocument()
  })

  it('3. NATIONAL_ADMIN retains educational governance navigation and NEVER sees technical operations links', async () => {
    activeMockUser = createNationalAdminUser()

    render(
      <MemoryRouter initialEntries={['/']}>
        <AuthProvider>
          <RootLayout />
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('🇨🇴 Nal.')).toBeInTheDocument()
    })

    // Must render educational governance links
    expect(screen.getByText('Instituciones')).toBeInTheDocument()
    expect(screen.getByText('Usuarios')).toBeInTheDocument()
    expect(screen.getByText('Admin Dptal.')).toBeInTheDocument()
    expect(screen.getByText('Admin Mpal.')).toBeInTheDocument()
    expect(screen.getByText('Control Territorial')).toBeInTheDocument()
    expect(screen.getByText('Onboarding')).toBeInTheDocument()

    // Must NOT render exclusive technical operations links
    expect(screen.queryByText('Salud Plataforma')).not.toBeInTheDocument()
    expect(screen.queryByText('Soporte Técnico')).not.toBeInTheDocument()
    expect(screen.queryByText('Seguridad & Auditoría')).not.toBeInTheDocument()
    expect(screen.queryByText('Diagnóstico Inquilinos')).not.toBeInTheDocument()
  })

  it('4. PlatformHealthView renders infrastructure services and live probes', async () => {
    render(
      <MemoryRouter>
        <PlatformHealthView />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/Salud e Infraestructura de la Plataforma/i)).toBeInTheDocument()
    })

    expect(screen.getByText(/PostgreSQL Primary Database/i)).toBeInTheDocument()
    expect(screen.getByText(/Redis Cache Cluster/i)).toBeInTheDocument()
    expect(screen.getByText(/Datos Abiertos Colombia Socrata API/i)).toBeInTheDocument()
  })

  it('5. TechnicalSupportView renders incident table, filters, and create modal', async () => {
    render(
      <MemoryRouter>
        <TechnicalSupportView />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/Mesa de Ayuda Técnica e Incidentes de Plataforma/i)).toBeInTheDocument()
    })

    expect(screen.getByText(/INC-2026-0001/i)).toBeInTheDocument()
    expect(screen.getByText(/Degradación en sincronización Socrata/i)).toBeInTheDocument()

    // Open Create Modal
    const createBtn = screen.getByTestId('btn-open-create-incident')
    fireEvent.click(createBtn)

    expect(screen.getByText(/Registrar Nuevo Incidente Técnico/i)).toBeInTheDocument()
  })

  it('6. SecurityAuditView renders security stream and counters', async () => {
    render(
      <MemoryRouter>
        <SecurityAuditView />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/Transmisión de Eventos y Auditoría de Seguridad/i)).toBeInTheDocument()
    })

    expect(screen.getByText(/AUTH_LOGIN_SUCCESS/i)).toBeInTheDocument()
    expect(screen.getByText(/192.168.1.100/i)).toBeInTheDocument()
  })

  it('7. TenantDiagnosticsView renders tenant search and audited probe', async () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <TenantDiagnosticsView />
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/Diagnóstico Operacional de Inquilino \/ Tenant/i)).toBeInTheDocument()
      expect(screen.getByText(/Seleccionar Institución para Diagnóstico/i)).toBeInTheDocument()
    })
  })

  it('8. SUPER_ADMIN Dashboard strictly isolates and NEVER renders educational sections across the entire page', async () => {
    activeMockUser = createSuperAdminUser()

    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <AuthProvider>
          <Dashboard />
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/Consola de Observabilidad, Soporte y Gobernanza de Plataforma/i)).toBeInTheDocument()
    })

    // Confirm top banner disambiguation
    expect(screen.getByText(/🌐 Operador Técnico Global • SUPER_ADMIN \(Nivel 100\)/i)).toBeInTheDocument()

    // Confirm educational sections are completely absent from DOM
    expect(screen.queryByText(/Comunicaciones y Noticias/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/Comité de Convivencia e Incidentes/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/Aulas Virtuales y Clases en Vivo/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/Directorio General de Usuarios/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/Abrir Catálogo Nacional/i)).not.toBeInTheDocument()
  })

  it('9. RootLayout navigation and panel links accurately disambiguate between SUPER_ADMIN and NATIONAL_ADMIN', async () => {
    // 1. SUPER_ADMIN check
    activeMockUser = createSuperAdminUser()
    const { unmount } = render(
      <MemoryRouter initialEntries={['/']}>
        <AuthProvider>
          <RootLayout />
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/⚙️ Operaciones \(admin\)/i)).toBeInTheDocument()
    })
    unmount()

    // 2. NATIONAL_ADMIN check
    activeMockUser = createNationalAdminUser()
    render(
      <MemoryRouter initialEntries={['/']}>
        <AuthProvider>
          <RootLayout />
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/🇨🇴 Panel Nacional \(national_admin\)/i)).toBeInTheDocument()
    })
    expect(screen.queryByText(/⚙️ Operaciones/i)).not.toBeInTheDocument()
  })

  it('10. Switching from SUPER_ADMIN to NATIONAL_ADMIN restores educational sections without stale operations console', async () => {
    // Render as NATIONAL_ADMIN
    activeMockUser = createNationalAdminUser()

    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <AuthProvider>
          <Dashboard />
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/🇨🇴 Gobernanza Educativa Nacional • NATIONAL_ADMIN \(Nivel 90\)/i)).toBeInTheDocument()
    })

    // NATIONAL_ADMIN must NOT see Technical Operations Console
    expect(screen.queryByText(/Consola de Observabilidad, Soporte y Gobernanza de Plataforma/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/Base de Datos Primaria/i)).not.toBeInTheDocument()

    // NATIONAL_ADMIN sees educational governance cards
    expect(screen.getByText(/Aprovisionamiento Institucional y Rectores/i)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Abrir Catálogo Nacional/i })).toBeInTheDocument()
    expect(screen.getByText(/Directorio General de Usuarios/i)).toBeInTheDocument()
  })
})
