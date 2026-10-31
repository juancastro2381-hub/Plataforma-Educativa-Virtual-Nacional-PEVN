/**
 * PEVN Frontend — Notification, Alert, and Confirmation Types
 *
 * Centralized contracts for institutional toast notifications,
 * modal alerts, and confirmation dialogs.
 */

import React from 'react'

export type NotificationType = 'success' | 'error' | 'warning' | 'info'

export interface Toast {
  id: string
  type: NotificationType
  title?: string
  message: string
  duration?: number // ms, default 5000; 0 for persistent
  timestamp: number
}

export type ConfirmSeverity = 'normal' | 'destructive' | 'warning' | 'info'

export interface ConfirmOptions {
  title: string
  message: string | React.ReactNode
  description?: string
  confirmText?: string
  cancelText?: string
  severity?: ConfirmSeverity
  onConfirm?: () => Promise<void> | void
}

export interface AlertOptions {
  title?: string
  message: string | React.ReactNode
  type?: NotificationType
  buttonText?: string
}

export interface NotificationContextValue {
  /** Emit a generic toast */
  notify: (toast: Omit<Toast, 'id' | 'timestamp'>) => string
  /** Emit a success toast */
  success: (message: string, title?: string, duration?: number) => string
  /** Emit an error toast (sanitizes sensitive data) */
  error: (message: string, title?: string, duration?: number) => string
  /** Emit a warning toast */
  warning: (message: string, title?: string, duration?: number) => string
  /** Emit an informational toast */
  info: (message: string, title?: string, duration?: number) => string
  /** Dismiss toast by ID */
  dismissToast: (id: string) => void
  /** Clear all toasts */
  clearToasts: () => void

  /** Open an asynchronous confirmation modal. Resolves to true if approved, false if cancelled. */
  confirm: (options: ConfirmOptions) => Promise<boolean>

  /** Open an institutional alert dialog requiring user acknowledgment */
  alert: (options: AlertOptions | string) => Promise<void>
}

