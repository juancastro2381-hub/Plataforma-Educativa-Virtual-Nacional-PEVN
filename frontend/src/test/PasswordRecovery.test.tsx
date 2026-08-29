/**
 * PEVN Frontend — Password Recovery Component Tests
 *
 * Tests ForgotPassword and ResetPassword components, form validations,
 * token verification, error handling, and success flows.
 */

import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { AuthProvider } from '@/context/AuthContext'
import { ForgotPassword } from '@/pages/auth/ForgotPassword'
import { ResetPassword } from '@/pages/auth/ResetPassword'
import { authApi } from '@/services/auth'

vi.mock('@/services/auth', () => ({
  authApi: {
    requestPasswordReset: vi.fn(),
    verifyPasswordResetToken: vi.fn(),
    confirmPasswordReset: vi.fn(),
    refresh: vi.fn().mockResolvedValue({
      access_token: 'mock-token',
      token_type: 'bearer',
      expires_in: 900,
      user: null,
    }),
  },
  default: {
    requestPasswordReset: vi.fn(),
    verifyPasswordResetToken: vi.fn(),
    confirmPasswordReset: vi.fn(),
    refresh: vi.fn().mockResolvedValue({
      access_token: 'mock-token',
      token_type: 'bearer',
      expires_in: 900,
      user: null,
    }),
  },
}))

describe('Password Recovery Components', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders ForgotPassword form and submits recovery request', async () => {
    vi.mocked(authApi.requestPasswordReset).mockResolvedValue(undefined)

    render(
      <MemoryRouter>
        <AuthProvider>
          <ForgotPassword />
        </AuthProvider>
      </MemoryRouter>
    )

    expect(screen.getByText(/Recuperación de Contraseña/i)).toBeInTheDocument()

    const emailInput = screen.getByLabelText(/Correo Electrónico/i)
    const submitBtn = screen.getByRole('button', { name: /Enviar Enlace/i })

    await userEvent.type(emailInput, 'rector@pevn.edu.co')
    await userEvent.click(submitBtn)

    await waitFor(() => {
      expect(authApi.requestPasswordReset).toHaveBeenCalledWith({
        email: 'rector@pevn.edu.co',
      })
      expect(screen.getByText(/Instrucciones Enviadas/i)).toBeInTheDocument()
      expect(
        screen.getByText(/Si la dirección de correo electrónico se encuentra registrada/i)
      ).toBeInTheDocument()
    })
  })

  it('renders ResetPassword form when token is valid and updates password', async () => {
    vi.mocked(authApi.verifyPasswordResetToken).mockResolvedValue({
      valid: true,
      message: 'Token válido',
    })
    vi.mocked(authApi.confirmPasswordReset).mockResolvedValue(undefined)

    render(
      <MemoryRouter initialEntries={['/auth/reset-password?token=valid_crypto_token_12345']}>
        <AuthProvider>
          <ResetPassword />
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(authApi.verifyPasswordResetToken).toHaveBeenCalledWith({
        token: 'valid_crypto_token_12345',
      })
      expect(screen.getByText(/Nueva Contraseña/i)).toBeInTheDocument()
    })

    const newPwdInput = screen.getByLabelText(/Nueva Contraseña/i)
    const confirmPwdInput = screen.getByLabelText(/Confirmar Contraseña/i)
    const submitBtn = screen.getByRole('button', { name: /Restablecer Contraseña/i })

    await userEvent.type(newPwdInput, 'NewSecurePassword123!')
    await userEvent.type(confirmPwdInput, 'NewSecurePassword123!')
    await userEvent.click(submitBtn)

    await waitFor(() => {
      expect(authApi.confirmPasswordReset).toHaveBeenCalledWith({
        token: 'valid_crypto_token_12345',
        new_password: 'NewSecurePassword123!',
      })
      expect(screen.getByText(/Contraseña Actualizada/i)).toBeInTheDocument()
    })
  })

  it('renders error state when reset token is invalid or expired', async () => {
    vi.mocked(authApi.verifyPasswordResetToken).mockRejectedValue(
      new Error('El token de restablecimiento es inválido o ha expirado.')
    )

    render(
      <MemoryRouter initialEntries={['/auth/reset-password?token=expired_token']}>
        <AuthProvider>
          <ResetPassword />
        </AuthProvider>
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText(/Enlace No Válido o Expirado/i)).toBeInTheDocument()
      expect(
        screen.getByRole('button', { name: /Solicitar un Nuevo Enlace/i })
      ).toBeInTheDocument()
    })
  })
})
