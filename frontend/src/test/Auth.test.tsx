/**
 * PEVN Frontend — Authentication & Authorization Unit / Component Tests
 */

import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AuthProvider } from '@/context/AuthContext'
import { RequireAuth } from '@/components/auth/RequireAuth'
import { RequireRole } from '@/components/auth/RequireRole'
import { RequirePermission } from '@/components/auth/RequirePermission'
import { Login } from '@/pages/Login'
import { setAccessToken, getAccessToken } from '@/services/api/client'
import type {
  ChangePasswordRequest,
  LoginRequest,
  LoginResponse,
  User,
} from '@/types'

const mockLoginFn = vi.fn<(req: LoginRequest) => Promise<LoginResponse>>()
const mockRefreshFn = vi.fn<() => Promise<string>>()
const mockLogoutFn = vi.fn<() => Promise<void>>()
const mockGetMyProfileFn = vi.fn<() => Promise<User>>()
const mockChangePasswordFn = vi.fn<(req: ChangePasswordRequest) => Promise<void>>()

// Mock auth service
vi.mock('@/services/auth', () => {
  const api = {
    login: (req: LoginRequest): Promise<LoginResponse> => mockLoginFn(req),
    refresh: (): Promise<string> => mockRefreshFn(),
    logout: (): Promise<void> => mockLogoutFn(),
    getMyProfile: (): Promise<User> => mockGetMyProfileFn(),
    changePassword: (req: ChangePasswordRequest): Promise<void> => mockChangePasswordFn(req),
  }
  return {
    authApi: api,
    default: api,
  }
})

const mockTeacherUser: User = {
  id: 'u-12345',
  email: 'profesor@pevn.edu.co',
  username: 'profesor1',
  first_name: 'Carlos',
  last_name: 'Gómez',
  full_name: 'Carlos Gómez',
  document_type: 'CC',
  document_number: '12345678',
  institution_id: 'inst-001',
  is_active: true,
  is_verified: true,
  must_change_password: false,
  roles: ['teacher'],
  permissions: ['grades:read', 'grades:write', 'attendance:write'],
  scope: {
    country_code: 'CO',
    department_id: 'DEP-11',
    municipality_id: 'MUN-11001',
    institution_id: 'inst-001',
    campus_id: null,
    is_national: false,
    is_institution: true,
  },
}

describe('In-Memory Token Security', () => {
  beforeEach(() => {
    setAccessToken(null)
  })

  it('stores and retrieves access token strictly in memory', () => {
    expect(getAccessToken()).toBeNull()
    setAccessToken('mock-jwt-token-xyz')
    expect(getAccessToken()).toBe('mock-jwt-token-xyz')
    setAccessToken(null)
    expect(getAccessToken()).toBeNull()
  })
})

describe('Login Page', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockRefreshFn.mockRejectedValue(new Error('No session'))
  })

  it('renders login form elements with accessible labels', async () => {
    render(
      <MemoryRouter initialEntries={['/login']}>
        <AuthProvider>
          <Login />
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /inicio de sesión/i })).toBeInTheDocument()
    })

    expect(screen.getByLabelText(/usuario o correo institucional/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/^contraseña$/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /iniciar sesión/i })).toBeInTheDocument()
  })

  it('displays validation error if submitted empty', async () => {
    const user = userEvent.setup()

    render(
      <MemoryRouter initialEntries={['/login']}>
        <AuthProvider>
          <Login />
        </AuthProvider>
      </MemoryRouter>
    )

    const submitBtn = screen.getByRole('button', { name: /iniciar sesión/i })
    await user.click(submitBtn)

    expect(screen.getByRole('alert')).toHaveTextContent(/por favor ingrese su usuario/i)
  })
})

describe('Route Guards', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('RequireAuth redirects unauthenticated user to /login', async () => {
    mockRefreshFn.mockRejectedValue(new Error('Unauthenticated'))

    render(
      <MemoryRouter initialEntries={['/protected']}>
        <AuthProvider>
          <Routes>
            <Route
              path="/protected"
              element={
                <RequireAuth>
                  <div>Secret Dashboard</div>
                </RequireAuth>
              }
            />
            <Route path="/login" element={<div>Página de Login</div>} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Página de Login')).toBeInTheDocument()
    })
    expect(screen.queryByText('Secret Dashboard')).not.toBeInTheDocument()
  })

  it('RequireRole blocks access when user lacks role', async () => {
    mockRefreshFn.mockResolvedValue('valid-token')
    mockGetMyProfileFn.mockResolvedValue(mockTeacherUser)

    render(
      <MemoryRouter initialEntries={['/admin-only']}>
        <AuthProvider>
          <Routes>
            <Route
              path="/admin-only"
              element={
                <RequireRole roles="superadmin">
                  <div>Superadmin Area</div>
                </RequireRole>
              }
            />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/acceso restringido \(403\)/i)).toBeInTheDocument()
    })
    expect(screen.queryByText('Superadmin Area')).not.toBeInTheDocument()
  })

  it('RequirePermission grants access when user has permission', async () => {
    mockRefreshFn.mockResolvedValue('valid-token')
    mockGetMyProfileFn.mockResolvedValue(mockTeacherUser)

    render(
      <MemoryRouter initialEntries={['/grades']}>
        <AuthProvider>
          <Routes>
            <Route
              path="/grades"
              element={
                <RequirePermission permission="grades:write">
                  <div>Calificaciones Editor</div>
                </RequirePermission>
              }
            />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Calificaciones Editor')).toBeInTheDocument()
    })
  })
})
