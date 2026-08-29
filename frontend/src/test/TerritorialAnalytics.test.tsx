/**
 * PEVN Frontend — Territorial Analytics Component Tests
 *
 * Tests TerritorialAnalyticsView, KPI rendering, department distribution table,
 * and municipality breakdown.
 */

import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { AuthProvider } from '@/context/AuthContext'
import { TerritorialAnalyticsView } from '@/pages/analytics/TerritorialAnalyticsView'
import { analyticsApi } from '@/services/analytics'
const { mockAdminUser } = vi.hoisted(() => ({
  mockAdminUser: {
    id: 'u-admin-01',
    email: 'admin@mineducacion.gov.co',
    username: 'admin',
    first_name: 'Admin',
    last_name: 'Nacional',
    full_name: 'Admin Nacional',
    document_type: 'CC' as const,
    document_number: '9988776655',
    institution_id: null,
    is_active: true,
    is_verified: true,
    must_change_password: false,
    roles: ['national_admin'],
    permissions: ['institutions:read'],
    scope: {
      country_code: 'CO',
      department_id: null,
      municipality_id: null,
      institution_id: null,
      campus_id: null,
      is_national: true,
      is_institution: false,
    },
  },
}))

vi.mock('@/services/auth', () => ({
  authApi: {
    refresh: vi.fn().mockResolvedValue('mock-token'),
    getMyProfile: vi.fn().mockResolvedValue(mockAdminUser),
  },
  default: {
    refresh: vi.fn().mockResolvedValue('mock-token'),
    getMyProfile: vi.fn().mockResolvedValue(mockAdminUser),
  },
}))

vi.mock('@/services/analytics', () => ({
  analyticsApi: {
    getTerritorialSummary: vi.fn(),
    getDepartmentDistribution: vi.fn(),
    getMunicipalityDistribution: vi.fn(),
    getInstitutionalKPIs: vi.fn(),
  },
  default: {
    getTerritorialSummary: vi.fn(),
    getDepartmentDistribution: vi.fn(),
    getMunicipalityDistribution: vi.fn(),
    getInstitutionalKPIs: vi.fn(),
  },
}))

describe('Territorial Analytics Dashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks()

    vi.mocked(analyticsApi.getTerritorialSummary).mockResolvedValue({
      scope_level: 'NATIONAL',
      jurisdiction_name: 'República de Colombia',
      total_departments: 33,
      total_municipalities: 1122,
      total_institutions: 13540,
      provisioned_institutions: 450,
      provisioning_rate_percent: 3.32,
      total_campuses: 45200,
      active_students: 12000,
      active_teachers: 980,
      active_groups: 420,
      sector_breakdown: {
        official: 10200,
        non_official: 3340,
      },
      zone_breakdown: {
        urban: 28000,
        rural: 17200,
      },
      computed_at: '2026-08-28T00:00:00Z',
    })

    vi.mocked(analyticsApi.getDepartmentDistribution).mockResolvedValue({
      items: [
        {
          department_code: '11',
          department_name: 'Bogotá D.C.',
          total_municipalities: 1,
          total_institutions: 1500,
          official_institutions: 1200,
          non_official_institutions: 300,
          total_campuses: 2500,
          provisioned_institutions: 120,
        },
        {
          department_code: '05',
          department_name: 'Antioquia',
          total_municipalities: 125,
          total_institutions: 2400,
          official_institutions: 1900,
          non_official_institutions: 500,
          total_campuses: 4800,
          provisioned_institutions: 85,
        },
      ],
      total_count: 2,
      computed_at: '2026-08-28T00:00:00Z',
    })

    vi.mocked(analyticsApi.getMunicipalityDistribution).mockResolvedValue({
      department_code: '11',
      items: [
        {
          municipality_code: '11001',
          municipality_name: 'Bogotá D.C.',
          department_code: '11',
          department_name: 'Bogotá D.C.',
          total_institutions: 1500,
          official_institutions: 1200,
          non_official_institutions: 300,
          total_campuses: 2500,
          provisioned_institutions: 120,
        },
      ],
      total_count: 1,
      computed_at: '2026-08-28T00:00:00Z',
    })
  })

  it('renders TerritorialAnalyticsView and displays summary KPI metrics and department table', async () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <TerritorialAnalyticsView />
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/Tablero de Analítica Territorial/i)).toBeInTheDocument()
      expect(screen.getByText(/13[.,]540/i)).toBeInTheDocument()
      expect(screen.getByText('Bogotá D.C.')).toBeInTheDocument()
      expect(screen.getByText('Antioquia')).toBeInTheDocument()
    })

    // Click "Ver Municipios" for Bogotá
    const verMunicipiosBtns = screen.getAllByRole('button', { name: /Ver Municipios/i })
    await userEvent.click(verMunicipiosBtns[0])

    await waitFor(() => {
      expect(analyticsApi.getMunicipalityDistribution).toHaveBeenCalledWith('11')
      expect(screen.getByText(/Municipios en Departamento 11/i)).toBeInTheDocument()
    })
  })
})
