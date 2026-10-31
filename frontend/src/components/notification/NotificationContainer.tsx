/**
 * PEVN Design System — NotificationContainer Component
 *
 * Fixed view container that renders the active toasts stack,
 * confirmation modal dialog, and alert modal dialog with proper
 * accessibility live regions and portal-like layering.
 */

import React from 'react'
import { ToastNotification } from './ToastNotification'
import { ConfirmationDialog } from './ConfirmationDialog'
import { AlertDialogModal } from './AlertDialogModal'
import type { Toast, ConfirmOptions, AlertOptions } from '@/types/notification'

interface NotificationContainerProps {
  toasts: Toast[]
  onDismissToast: (id: string) => void
  activeConfirm: {
    isOpen: boolean
    options: ConfirmOptions
    resolve: (val: boolean) => void
  } | null
  activeAlert: {
    isOpen: boolean
    options: AlertOptions
    resolve: () => void
  } | null
}

export const NotificationContainer: React.FC<NotificationContainerProps> = ({
  toasts,
  onDismissToast,
  activeConfirm,
  activeAlert,
}) => {
  return (
    <>
      {/* Toasts Stack (Fixed Top-Right) */}
      <div
        id="pevn-notifications-container"
        style={{
          position: 'fixed',
          top: '1.25rem',
          right: '1.25rem',
          zIndex: 99990,
          display: 'flex',
          flexDirection: 'column',
          gap: '0.75rem',
          pointerEvents: 'none',
          maxWidth: 'calc(100vw - 2.5rem)',
        }}
        aria-live="polite"
      >
        {toasts.map((toast) => (
          <ToastNotification
            key={toast.id}
            toast={toast}
            onDismiss={onDismissToast}
          />
        ))}
      </div>

      {/* Confirmation Modal */}
      {activeConfirm && (
        <ConfirmationDialog
          isOpen={activeConfirm.isOpen}
          options={activeConfirm.options}
          onConfirm={() => activeConfirm.resolve(true)}
          onCancel={() => activeConfirm.resolve(false)}
        />
      )}

      {/* Alert Modal */}
      {activeAlert && (
        <AlertDialogModal
          isOpen={activeAlert.isOpen}
          options={activeAlert.options}
          onAcknowledge={() => activeAlert.resolve()}
        />
      )}
    </>
  )
}

