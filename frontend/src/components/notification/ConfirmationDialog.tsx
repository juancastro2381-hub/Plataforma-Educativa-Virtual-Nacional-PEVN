/**
 * PEVN Design System — ConfirmationDialog Component
 *
 * Professional, accessible modal confirmation dialog for sensitive or
 * destructive user operations. Prevents double-submission and supports
 * contextual consequences, loading indicators, and keyboard controls.
 */

import React, { useEffect, useRef, useState } from 'react'
import { Button } from '@components/ui/Button'
import type { ConfirmOptions } from '@/types/notification'

interface ConfirmationDialogProps {
  isOpen: boolean
  options: ConfirmOptions
  onConfirm: () => Promise<void> | void
  onCancel: () => void
}

export const ConfirmationDialog: React.FC<ConfirmationDialogProps> = ({
  isOpen,
  options,
  onConfirm,
  onCancel,
}) => {
  const [isLoading, setIsLoading] = useState(false)
  const confirmBtnRef = useRef<HTMLButtonElement | null>(null)
  const cancelBtnRef = useRef<HTMLButtonElement | null>(null)

  const isDestructive = options.severity === 'destructive'
  const isWarning = options.severity === 'warning'

  useEffect(() => {
    if (!isOpen) return

    setIsLoading(false)
    // Focus cancel button by default for destructive actions (safety first), otherwise confirm button
    const timer = setTimeout(() => {
      if (isDestructive && cancelBtnRef.current) {
        cancelBtnRef.current.focus()
      } else if (confirmBtnRef.current) {
        confirmBtnRef.current.focus()
      }
    }, 50)

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !isLoading) {
        onCancel()
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    document.body.style.overflow = 'hidden'

    return () => {
      clearTimeout(timer)
      document.removeEventListener('keydown', handleKeyDown)
      document.body.style.overflow = 'unset'
    }
  }, [isOpen, isDestructive, isLoading, onCancel])

  if (!isOpen) return null

  const handleConfirmClick = async () => {
    if (isLoading) return
    try {
      setIsLoading(true)
      if (options.onConfirm) {
        await options.onConfirm()
      }
      await onConfirm()
    } catch {
      // Re-enable if external action fails
      setIsLoading(false)
    }
  }

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget && !isLoading) {
      onCancel()
    }
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-dialog-title"
      aria-describedby="confirm-dialog-message"
      onClick={handleBackdropClick}
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
          maxWidth: '520px',
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
        {/* Header with Icon */}
        <div
          style={{
            padding: '1.5rem 1.5rem 1rem 1.5rem',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '1rem',
          }}
        >
          {/* Severity Icon Badge */}
          <div
            style={{
              backgroundColor: isDestructive
                ? '#FEE2E2'
                : isWarning
                  ? '#FEF3C7'
                  : '#DBEAFE',
              color: isDestructive
                ? '#DC2626'
                : isWarning
                  ? '#D97706'
                  : '#2563EB',
              borderRadius: '12px',
              padding: '0.65rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            {isDestructive ? (
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                />
              </svg>
            ) : isWarning ? (
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
            ) : (
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            )}
          </div>

          <div style={{ flex: 1, minWidth: 0 }}>
            <h3
              id="confirm-dialog-title"
              style={{
                fontSize: '1.125rem',
                fontWeight: 800,
                color: '#0F172A',
                margin: '0 0 0.35rem 0',
                lineHeight: 1.3,
              }}
            >
              {options.title}
            </h3>
            <div
              id="confirm-dialog-message"
              style={{
                fontSize: '0.875rem',
                color: '#475569',
                lineHeight: 1.5,
              }}
            >
              {options.message}
            </div>
            {options.description && (
              <p
                style={{
                  fontSize: '0.8125rem',
                  color: isDestructive ? '#991B1B' : '#64748B',
                  backgroundColor: isDestructive ? '#FEF2F2' : '#F8FAFC',
                  border: isDestructive ? '1px solid #FCA5A5' : '1px solid #E2E8F0',
                  borderRadius: '8px',
                  padding: '0.5rem 0.75rem',
                  marginTop: '0.65rem',
                  marginBottom: 0,
                  lineHeight: 1.4,
                }}
              >
                {options.description}
              </p>
            )}
          </div>
        </div>

        {/* Footer Actions */}
        <div
          style={{
            padding: '1rem 1.5rem',
            backgroundColor: '#F8FAFC',
            borderTop: '1px solid #E2E8F0',
            display: 'flex',
            justifyContent: 'flex-end',
            gap: '0.75rem',
            alignItems: 'center',
          }}
        >
          <Button
            ref={cancelBtnRef}
            type="button"
            variant="secondary"
            size="sm"
            onClick={onCancel}
            disabled={isLoading}
            id="btn-confirm-dialog-cancel"
          >
            {options.cancelText || 'Cancelar'}
          </Button>

          <Button
            ref={confirmBtnRef}
            type="button"
            variant={isDestructive ? 'danger' : 'primary'}
            size="sm"
            onClick={() => void handleConfirmClick()}
            isLoading={isLoading}
            id="btn-confirm-dialog-confirm"
          >
            {options.confirmText || 'Confirmar'}
          </Button>
        </div>
      </div>
    </div>
  )
}
