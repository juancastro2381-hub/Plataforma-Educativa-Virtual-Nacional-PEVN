/**
 * PEVN Frontend — UsersView Component Unit & Integration Tests
 *
 * Validates that the institutional user directory:
 *   1. Displays canonical roles with their human-readable labels:
 *      - 'rector' -> 'Rector / Director'
 *      - 'teacher' -> 'Docente'
 *      - 'guardian' -> 'Acudiente / Tutor'
 *      - 'student' -> 'Estudiante'
 *   2. Displays 'Sin roles' when the user has a genuinely empty roles array ([]).
 *   3. Displays user details and assigned roles correctly inside the User Details Modal.
 */

import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { UsersView } from '@pages/admin/UsersView'
import { usersApi } from '@/services/users'
import type { UserListResponse, UserResponse } from '@/types'

// Mock useAuth
vi.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({
    user: {
      id: 'rector-uuid-1',
      email: 'rector@inst.edu.co',
      roles: ['rector'],
      scope: {
        institution_id: 'inst-1',
        jurisdiction_name: 'ALEGRIA DE APRENDER',
        is_national: () => false,
      },
    },
    hasPermission: () => true,
    hasRole: () => true,
  }),
}))

// Mock usersApi
vi.mock('@/services/users', () => ({
  usersApi: {
    searchUsers: vi.fn(),
    getUserById: vi.fn(),
  },
}))

describe('UsersView — Role Serialization and Rendering in Directory', () => {
  const mockUsers: UserResponse[] = [
    {
      id: 'u-1',
      email: 'rector@inst.edu.co',
      username: 'rector_mary',
      first_name: 'Mary',
      last_name: 'Garcia',
      full_name: 'Mary Garcia',
      document_type: 'CC',
      document_number: '195668544',
      institution_id: 'inst-1',
      is_active: true,
      is_verified: true,
      roles: ['rector'],
      created_at: '2026-10-29T14:31:19Z',
      updated_at: '2026-10-30T07:00:50Z',
    },
    {
      id: 'u-2',
      email: 'docente@inst.edu.co',
      username: 'mauro_doc',
      first_name: 'Mauro',
      last_name: 'Diaz',
      full_name: 'Mauro Diaz',
      document_type: 'CC',
      document_number: '898970000',
      institution_id: 'inst-1',
      is_active: true,
      is_verified: false,
      roles: ['teacher'],
      created_at: '2026-10-30T07:22:20Z',
      updated_at: '2026-10-30T09:23:26Z',
    },
    {
      id: 'u-3',
      email: 'acudiente@example.com',
      username: 'andres_g',
      first_name: 'Andres',
      last_name: 'Gonzalez',
      full_name: 'Andres Gonzalez',
      document_type: 'CC',
      document_number: '456632100',
      institution_id: 'inst-1',
      is_active: true,
      is_verified: false,
      roles: ['guardian'],
      created_at: '2026-10-30T08:23:36Z',
      updated_at: '2026-10-30T09:25:46Z',
    },
    {
      id: 'u-4',
      email: 'estudiante@colegio.edu.co',
      username: 'danna_g',
      first_name: 'Danna',
      last_name: 'Gonzalez',
      full_name: 'Danna Gonzalez',
      document_type: 'TI',
      document_number: '100033355',
      institution_id: 'inst-1',
      is_active: true,
      is_verified: false,
      roles: ['student'],
      created_at: '2026-10-30T07:19:59Z',
      updated_at: '2026-10-30T09:25:17Z',
    },
    {
      id: 'u-5',
      email: 'sinroles@inst.edu.co',
      username: 'sin_roles_user',
      first_name: 'Usuario',
      last_name: 'Sin Asignar',
      full_name: 'Usuario Sin Asignar',
      document_type: 'CC',
      document_number: '77665544',
      institution_id: 'inst-1',
      is_active: true,
      is_verified: false,
      roles: [],
      created_at: '2026-10-30T09:00:00Z',
      updated_at: '2026-10-30T09:00:00Z',
    },
  ]

  const mockListResponse: UserListResponse = {
    items: mockUsers,
    total: 5,
    page: 1,
    page_size: 15,
  }

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(usersApi.searchUsers).mockResolvedValue(mockListResponse)
  })

  it('renders directory heading and jurisdiction banner', async () => {
    render(
      <MemoryRouter>
        <UsersView />
      </MemoryRouter>
    )

    expect(await screen.findByText('Directorio de Usuarios')).toBeInTheDocument()
    expect(screen.getByText('Jurisdicción: ALEGRIA DE APRENDER')).toBeInTheDocument()
    expect(screen.getByText('Total de usuarios registrados: 5')).toBeInTheDocument()
  })

  it('renders all canonical role badges with their formatted names', async () => {
    render(
      <MemoryRouter>
        <UsersView />
      </MemoryRouter>
    )

    // Wait for users table to populate
    expect(await screen.findByText('Mary Garcia')).toBeInTheDocument()

    // Assert role badges
    expect(screen.getByText('Rector / Director')).toBeInTheDocument()
    expect(screen.getByText('Docente')).toBeInTheDocument()
    expect(screen.getByText('Acudiente / Tutor')).toBeInTheDocument()
    expect(screen.getByText('Estudiante')).toBeInTheDocument()
  })

  it('renders "Sin roles" when a user genuinely has an empty roles array', async () => {
    render(
      <MemoryRouter>
        <UsersView />
      </MemoryRouter>
    )

    expect(await screen.findByText('Usuario Sin Asignar')).toBeInTheDocument()
    expect(screen.getByText('Sin roles')).toBeInTheDocument()
  })

  it('displays correct assigned roles in user details modal when clicking "Ver Ficha"', async () => {
    render(
      <MemoryRouter>
        <UsersView />
      </MemoryRouter>
    )

    // Wait for table to load
    expect(await screen.findByText('Mauro Diaz')).toBeInTheDocument()

    // Click "Ver Ficha" for Mauro Diaz
    const btnView = document.getElementById('btn-view-user-u-2')!
    expect(btnView).toBeInTheDocument()
    fireEvent.click(btnView)

    // Modal should open
    expect(await screen.findByText('Ficha de Usuario: Mauro Diaz')).toBeInTheDocument()
    expect(screen.getByText('ROLES ATÓMICOS ASIGNADOS')).toBeInTheDocument()

    // Inside modal, 'Docente' badge should be visible
    const badges = screen.getAllByText('Docente')
    expect(badges.length).toBeGreaterThanOrEqual(2) // One in table row, one in modal
  })
})
