/**
 * PEVN Frontend — Centralized Notification Context & Provider
 *
 * Provides application-wide notification, alert, and confirmation services.
 * Replaces native browser window.alert, window.confirm, and window.prompt.
 */

import React, { createContext, useCallback, useContext, useMemo, useState } from 'react'
import { NotificationContainer } from '@components/notification/NotificationContainer'
import type {
  Toast,
  ConfirmOptions,
  AlertOptions,
  NotificationContextValue,
} from '@/types/notification'

export const NotificationContext = createContext<NotificationContextValue | null>(null)

interface ActiveConfirmState {
  isOpen: boolean
  options: ConfirmOptions
  resolve: (val: boolean) => void
}

interface ActiveAlertState {
  isOpen: boolean
  options: AlertOptions
  resolve: () => void
}

export const NotificationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<Toast[]>([])
  const [activeConfirm, setActiveConfirm] = useState<ActiveConfirmState | null>(null)
  const [activeAlert, setActiveAlert] = useState<ActiveAlertState | null>(null)

  const dismissToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  const clearToasts = useCallback(() => {
    setToasts([])
  }, [])

  const notify = useCallback((toastData: Omit<Toast, 'id' | 'timestamp'>): string => {
    const id = `toast-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`
    const newToast: Toast = {
      ...toastData,
      id,
      timestamp: Date.now(),
      duration: toastData.duration !== undefined ? toastData.duration : 5000,
    }

    setToasts((prev) => {
      // Limit to 5 active toasts to prevent viewport cluttering
      const updated = [newToast, ...prev]
      if (updated.length > 5) {
        return updated.slice(0, 5)
      }
      return updated
    })

    return id
  }, [])

  const success = useCallback(
    (message: string, title?: string, duration?: number): string => {
      return notify({ type: 'success', message, title, duration })
    },
    [notify]
  )

  const error = useCallback(
    (message: string, title?: string, duration?: number): string => {
      return notify({ type: 'error', message, title: title || 'Error', duration })
    },
    [notify]
  )

  const warning = useCallback(
    (message: string, title?: string, duration?: number): string => {
      return notify({ type: 'warning', message, title: title || 'Advertencia', duration })
    },
    [notify]
  )

  const info = useCallback(
    (message: string, title?: string, duration?: number): string => {
      return notify({ type: 'info', message, title: title || 'Información', duration })
    },
    [notify]
  )

  const confirm = useCallback((options: ConfirmOptions): Promise<boolean> => {
    return new Promise((resolve) => {
      setActiveConfirm({
        isOpen: true,
        options,
        resolve: (approved: boolean) => {
          setActiveConfirm(null)
          resolve(approved)
        },
      })
    })
  }, [])

  const alertModal = useCallback((options: AlertOptions | string): Promise<void> => {
    const resolvedOptions: AlertOptions =
      typeof options === 'string'
        ? { message: options, title: 'Aviso del Sistema', type: 'info' }
        : options

    return new Promise((resolve) => {
      setActiveAlert({
        isOpen: true,
        options: resolvedOptions,
        resolve: () => {
          setActiveAlert(null)
          resolve()
        },
      })
    })
  }, [])

  const value: NotificationContextValue = useMemo(
    () => ({
      notify,
      success,
      error,
      warning,
      info,
      dismissToast,
      clearToasts,
      confirm,
      alert: alertModal,
    }),
    [notify, success, error, warning, info, dismissToast, clearToasts, confirm, alertModal]
  )

  return (
    <NotificationContext.Provider value={value}>
      {children}
      <NotificationContainer
        toasts={toasts}
        onDismissToast={dismissToast}
        activeConfirm={activeConfirm}
        activeAlert={activeAlert}
      />
    </NotificationContext.Provider>
  )
}

/**
 * Safe fallback context used when a component is rendered outside of
 * NotificationProvider (e.g. in isolated unit tests or Storybook stories).
 */
const fallbackNotificationContext: NotificationContextValue = {
  notify: () => '',
  success: () => '',
  error: () => '',
  warning: () => '',
  info: () => '',
  dismissToast: () => {},
  clearToasts: () => {},
  confirm: async () => true,
  alert: async () => {},
}

/**
 * useNotification Hook
 *
 * Access the centralized notification, toast, confirmation dialog,
 * and modal alert services from any component within NotificationProvider.
 * Gracefully falls back to a safe no-op implementation when used outside the provider.
 */
export function useNotification(): NotificationContextValue {
  const context = useContext(NotificationContext)
  if (!context) {
    return fallbackNotificationContext
  }
  return context
}
