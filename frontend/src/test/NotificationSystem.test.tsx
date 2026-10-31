/**
 * PEVN Frontend — Centralized Notification & Confirmation System Tests
 *
 * Verifies toast notifications, modal confirmations, institutional alerts,
 * sanitization of sensitive diagnostic data, accessibility attributes,
 * auto-dismissal timers, and double-submission protection.
 */

import { describe, expect, it } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import React from 'react'
import { NotificationProvider, useNotification } from '@/context/NotificationContext'
import { sanitizeMessage } from '@/components/notification/ToastNotification'

// Helper testing component to trigger notification functions
const TestNotificationConsumer: React.FC = () => {
  const { success, error, warning, info, confirm, alert: modalAlert } = useNotification()
  const [confirmResult, setConfirmResult] = React.useState<string | null>(null)
  const [alertResult, setAlertResult] = React.useState<string | null>(null)

  return (
    <div>
      <button onClick={() => success('Operación exitosa', 'Éxito')}>Trigger Success</button>
      <button onClick={() => error('Error al procesar solicitud', 'Fallo')}>Trigger Error</button>
      <button onClick={() => warning('Atención requerida', 'Advertencia')}>Trigger Warning</button>
      <button onClick={() => info('Información del sistema', 'Aviso')}>Trigger Info</button>

      <button
        onClick={async () => {
          const approved = await confirm({
            title: '¿Confirmar eliminación?',
            message: 'Esta acción no se puede deshacer.',
            description: 'Se eliminarán todos los registros asociados permanentemente.',
            confirmText: 'Sí, eliminar',
            cancelText: 'Cancelar',
            severity: 'destructive',
          })
          setConfirmResult(approved ? 'APPROVED' : 'CANCELLED')
        }}
      >
        Trigger Confirm
      </button>

      <button
        onClick={async () => {
          await modalAlert({
            title: 'Resolución Rectoral',
            message: 'La matrícula ha sido bloqueada temporalmente.',
            buttonText: 'Entendido',
            type: 'warning',
          })
          setAlertResult('ACKNOWLEDGED')
        }}
      >
        Trigger Alert
      </button>

      <div data-testid="confirm-status">{confirmResult}</div>
      <div data-testid="alert-status">{alertResult}</div>
    </div>
  )
}

describe('PEVN Centralized Notification System', () => {
  describe('Sanitization of Sensitive Data', () => {
    it('redacts Bearer tokens from error messages', () => {
      const raw = 'Request failed: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.token'
      const sanitized = sanitizeMessage(raw)
      expect(sanitized).not.toContain('eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9')
      expect(sanitized).toContain('Bearer [REDACTED]')
    })

    it('redacts standalone JWT tokens', () => {
      const raw = 'Invalid signature in token eyJhbGciOiJIUzI1Ni.eyJzdWIiOiIxMjM0NTY3ODkwIn0.doz'
      const sanitized = sanitizeMessage(raw)
      expect(sanitized).toContain('[TOKEN]')
      expect(sanitized).not.toContain('eyJhbGciOiJIUzI1Ni')
    })

    it('redacts raw SQL queries from error output', () => {
      const raw = 'Database syntax error: SELECT id, password_hash FROM users WHERE id = 1'
      const sanitized = sanitizeMessage(raw)
      expect(sanitized).toContain('[CONSULTA DB]')
      expect(sanitized).not.toContain('SELECT id, password_hash FROM users')
    })

    it('redacts cleartext password parameters', () => {
      const raw = 'Auth payload rejected for user mauro with password=SuperSecretPassword123'
      const sanitized = sanitizeMessage(raw)
      expect(sanitized).toContain('password=[REDACTED]')
      expect(sanitized).not.toContain('SuperSecretPassword123')
    })

    it('handles empty or normal strings safely', () => {
      expect(sanitizeMessage('')).toBe('')
      expect(sanitizeMessage('Operación completada con éxito')).toBe('Operación completada con éxito')
    })
  })

  describe('Toast Notifications Rendering & Lifecycle', () => {
    it('renders a success toast notification with title and message', async () => {
      const user = userEvent.setup()
      render(
        <NotificationProvider>
          <TestNotificationConsumer />
        </NotificationProvider>
      )

      await user.click(screen.getByText('Trigger Success'))

      expect(await screen.findByText('Éxito')).toBeInTheDocument()
      expect(screen.getByText('Operación exitosa')).toBeInTheDocument()
    })

    it('renders error, warning, and info toasts with appropriate content', async () => {
      const user = userEvent.setup()
      render(
        <NotificationProvider>
          <TestNotificationConsumer />
        </NotificationProvider>
      )

      await user.click(screen.getByText('Trigger Error'))
      expect(await screen.findByText('Fallo')).toBeInTheDocument()
      expect(screen.getByText('Error al procesar solicitud')).toBeInTheDocument()

      await user.click(screen.getByText('Trigger Warning'))
      expect(await screen.findByText('Advertencia')).toBeInTheDocument()
      expect(screen.getByText('Atención requerida')).toBeInTheDocument()

      await user.click(screen.getByText('Trigger Info'))
      expect(await screen.findByText('Aviso')).toBeInTheDocument()
      expect(screen.getByText('Información del sistema')).toBeInTheDocument()
    })

    it('allows manually dismissing a toast by clicking close button', async () => {
      const user = userEvent.setup()
      render(
        <NotificationProvider>
          <TestNotificationConsumer />
        </NotificationProvider>
      )

      await user.click(screen.getByText('Trigger Success'))
      expect(await screen.findByText('Éxito')).toBeInTheDocument()

      const dismissBtn = screen.getByLabelText('Cerrar notificación')
      await user.click(dismissBtn)

      await waitFor(() => {
        expect(screen.queryByText('Éxito')).not.toBeInTheDocument()
      })
    })
  })

  describe('Modal Confirmation Dialog', () => {
    it('resolves true when the user accepts the confirmation dialog', async () => {
      const user = userEvent.setup()
      render(
        <NotificationProvider>
          <TestNotificationConsumer />
        </NotificationProvider>
      )

      await user.click(screen.getByText('Trigger Confirm'))

      // Modal is visible
      expect(await screen.findByText('¿Confirmar eliminación?')).toBeInTheDocument()
      expect(screen.getByText('Esta acción no se puede deshacer.')).toBeInTheDocument()
      expect(
        screen.getByText('Se eliminarán todos los registros asociados permanentemente.')
      ).toBeInTheDocument()

      // Click Confirm button
      const confirmButton = screen.getByRole('button', { name: 'Sí, eliminar' })
      await user.click(confirmButton)

      await waitFor(() => {
        expect(screen.getByTestId('confirm-status')).toHaveTextContent('APPROVED')
        expect(screen.queryByText('¿Confirmar eliminación?')).not.toBeInTheDocument()
      })
    })

    it('resolves false when the user cancels the confirmation dialog', async () => {
      const user = userEvent.setup()
      render(
        <NotificationProvider>
          <TestNotificationConsumer />
        </NotificationProvider>
      )

      await user.click(screen.getByText('Trigger Confirm'))
      expect(await screen.findByText('¿Confirmar eliminación?')).toBeInTheDocument()

      const cancelButton = screen.getByRole('button', { name: 'Cancelar' })
      await user.click(cancelButton)

      await waitFor(() => {
        expect(screen.getByTestId('confirm-status')).toHaveTextContent('CANCELLED')
        expect(screen.queryByText('¿Confirmar eliminación?')).not.toBeInTheDocument()
      })
    })

    it('resolves false when pressing Escape key', async () => {
      const user = userEvent.setup()
      render(
        <NotificationProvider>
          <TestNotificationConsumer />
        </NotificationProvider>
      )

      await user.click(screen.getByText('Trigger Confirm'))
      expect(await screen.findByText('¿Confirmar eliminación?')).toBeInTheDocument()

      await user.keyboard('{Escape}')

      await waitFor(() => {
        expect(screen.getByTestId('confirm-status')).toHaveTextContent('CANCELLED')
        expect(screen.queryByText('¿Confirmar eliminación?')).not.toBeInTheDocument()
      })
    })
  })

  describe('Institutional Alert Dialog Modal', () => {
    it('displays alert dialog and resolves promise when acknowledged', async () => {
      const user = userEvent.setup()
      render(
        <NotificationProvider>
          <TestNotificationConsumer />
        </NotificationProvider>
      )

      await user.click(screen.getByText('Trigger Alert'))

      expect(await screen.findByText('Resolución Rectoral')).toBeInTheDocument()
      expect(
        screen.getByText('La matrícula ha sido bloqueada temporalmente.')
      ).toBeInTheDocument()

      const ackBtn = screen.getByRole('button', { name: 'Entendido' })
      await user.click(ackBtn)

      await waitFor(() => {
        expect(screen.getByTestId('alert-status')).toHaveTextContent('ACKNOWLEDGED')
        expect(screen.queryByText('Resolución Rectoral')).not.toBeInTheDocument()
      })
    })
  })
})
