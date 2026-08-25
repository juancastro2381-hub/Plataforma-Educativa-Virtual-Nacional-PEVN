/**
 * PEVN Frontend — Alert Component
 *
 * Displays error, warning, success, and info messages with correlation ID support.
 */

import React from 'react'
import type { ApiError } from '@/types'

export type AlertVariant = 'error' | 'warning' | 'success' | 'info'

export interface AlertProps {
  title?: string
  message?: string
  error?: ApiError | Error | null
  variant?: AlertVariant
  onClose?: () => void
  className?: string
  children?: React.ReactNode
}

const variantConfig: Record<
  AlertVariant,
  { bg: string; border: string; text: string; titleColor: string; icon: string }
> = {
  error: {
    bg: '#FEF2F2',
    border: '#FCA5A5',
    text: '#991B1B',
    titleColor: '#7F1D1D',
    icon: '✕',
  },
  warning: {
    bg: '#FFFBEB',
    border: '#FCD34D',
    text: '#92400E',
    titleColor: '#78350F',
    icon: '⚠',
  },
  success: {
    bg: '#ECFDF5',
    border: '#6EE7B7',
    text: '#065F46',
    titleColor: '#064E3B',
    icon: '✓',
  },
  info: {
    bg: '#EFF6FF',
    border: '#93C5FD',
    text: '#1E40AF',
    titleColor: '#1E3A8A',
    icon: 'ℹ',
  },
}

export const Alert: React.FC<AlertProps> = ({
  title,
  message,
  error,
  variant = 'error',
  onClose,
  children,
}) => {
  const effectiveVariant: AlertVariant = error ? 'error' : variant
  const cfg = variantConfig[effectiveVariant]

  let displayTitle = title
  let displayMessage = message
  let correlationId: string | undefined

  if (error) {
    if ('code' in error && 'message' in error) {
      displayTitle = displayTitle || `Error: ${error.code}`
      displayMessage = error.message
      correlationId = error.correlation_id && error.correlation_id !== '-' ? error.correlation_id : undefined
    } else if (error instanceof Error) {
      displayTitle = displayTitle || 'Error'
      displayMessage = error.message
    }
  }

  if (!displayMessage && !children && !displayTitle) {
    return null
  }

  return (
    <div
      role="alert"
      style={{
        backgroundColor: cfg.bg,
        border: `1px solid ${cfg.border}`,
        borderRadius: '10px',
        padding: '1rem 1.25rem',
        marginBottom: '1rem',
        display: 'flex',
        gap: '0.75rem',
        alignItems: 'flex-start',
        boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
      }}
    >
      <div
        style={{
          width: '24px',
          height: '24px',
          borderRadius: '50%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontWeight: 'bold',
          fontSize: '0.875rem',
          color: cfg.text,
          flexShrink: 0,
        }}
        aria-hidden="true"
      >
        {cfg.icon}
      </div>

      <div style={{ flex: 1 }}>
        {displayTitle && (
          <h4
            style={{
              margin: '0 0 0.25rem 0',
              fontSize: '0.9375rem',
              fontWeight: 700,
              color: cfg.titleColor,
            }}
          >
            {displayTitle}
          </h4>
        )}
        {displayMessage && (
          <div style={{ fontSize: '0.875rem', color: cfg.text, lineHeight: 1.45 }}>
            {displayMessage}
          </div>
        )}
        {children}
        {correlationId && (
          <div
            style={{
              marginTop: '0.5rem',
              fontSize: '0.75rem',
              color: '#64748B',
            }}
          >
            ID de Referencia / Soporte:{' '}
            <code
              style={{
                backgroundColor: 'rgba(0,0,0,0.05)',
                padding: '0.1rem 0.35rem',
                borderRadius: '4px',
                fontFamily: 'monospace',
              }}
            >
              {correlationId}
            </code>
          </div>
        )}
      </div>

      {onClose && (
        <button
          onClick={onClose}
          aria-label="Cerrar notificación"
          style={{
            background: 'none',
            border: 'none',
            color: cfg.text,
            cursor: 'pointer',
            fontSize: '1rem',
            padding: '0.25rem',
            lineHeight: 1,
            opacity: 0.7,
          }}
        >
          ✕
        </button>
      )}
    </div>
  )
}

export default Alert
