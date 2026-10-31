/**
 * PEVN Design System — AlertDialogModal Component
 *
 * Modal alert dialog for critical institutional notifications requiring
 * explicit user acknowledgment.
 */

import React, { useEffect, useRef } from 'react'
import { Button } from '@components/ui/Button'
import type { AlertOptions } from '@/types/notification'

interface AlertDialogModalProps {
  isOpen: boolean
  options: AlertOptions
  onAcknowledge: () => void
}

export const AlertDialogModal: React.FC<AlertDialogModalProps> = ({
  isOpen,
  options,
  onAcknowledge,
}) => {
  const btnRef = useRef<HTMLButtonElement | null>(null)

  useEffect(() => {
    if (!isOpen) return

    const timer = setTimeout(() => {
      btnRef.current?.focus()
    }, 50)

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' || e.key === 'Enter') {
        onAcknowledge()
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    document.body.style.overflow = 'hidden'

    return () => {
      clearTimeout(timer)
      document.removeEventListener('keydown', handleKeyDown)
      document.body.style.overflow = 'unset'
    }
  }, [isOpen, onAcknowledge])

  if (!isOpen) return null

  const isError = options.type === 'error'
  const isWarning = options.type === 'warning'
  const isSuccess = options.type === 'success'

  return (
    <div
      role="alertdialog"
      aria-modal="true"
      aria-labelledby="alert-dialog-title"
      aria-describedby="alert-dialog-message"
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(15, 23, 42, 0.7)',
        backdropFilter: 'blur(4px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 99999,
        padding: '1rem',
      }}
    >
      <div
        style={{
          backgroundColor: '#FFFFFF',
          borderRadius: '16px',
          maxWidth: '480px',
          width: '100%',
          boxShadow: '0 25px 50px -12px rgba(15, 23, 42, 0.35)',
          border: '1px solid #E2E8F0',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          animation: 'fadeIn 150ms ease-out',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div
          style={{
            padding: '1.5rem',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '1rem',
          }}
        >
          {/* Icon Badge */}
          <div
            style={{
              backgroundColor: isError
                ? '#FEE2E2'
                : isWarning
                  ? '#FEF3C7'
                  : isSuccess
                    ? '#DCFCE7'
                    : '#DBEAFE',
              color: isError
                ? '#DC2626'
                : isWarning
                  ? '#D97706'
                  : isSuccess
                    ? '#16A34A'
                    : '#2563EB',
              borderRadius: '12px',
              padding: '0.65rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            {isError ? (
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            ) : isWarning ? (
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
            ) : isSuccess ? (
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            ) : (
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            )}
          </div>

          <div style={{ flex: 1, minWidth: 0 }}>
            <h3
              id="alert-dialog-title"
              style={{
                fontSize: '1.125rem',
                fontWeight: 800,
                color: '#0F172A',
                margin: '0 0 0.35rem 0',
                lineHeight: 1.3,
              }}
            >
              {options.title || 'Aviso del Sistema'}
            </h3>
            <div
              id="alert-dialog-message"
              style={{
                fontSize: '0.875rem',
                color: '#475569',
                lineHeight: 1.5,
              }}
            >
              {options.message}
            </div>
          </div>
        </div>

        <div
          style={{
            padding: '0.875rem 1.5rem',
            backgroundColor: '#F8FAFC',
            borderTop: '1px solid #E2E8F0',
            display: 'flex',
            justifyContent: 'flex-end',
          }}
        >
          <Button
            ref={btnRef}
            type="button"
            variant="primary"
            size="sm"
            onClick={onAcknowledge}
            id="btn-alert-dialog-ok"
          >
            {options.buttonText || 'Entendido'}
          </Button>
        </div>
      </div>
    </div>
  )
}
