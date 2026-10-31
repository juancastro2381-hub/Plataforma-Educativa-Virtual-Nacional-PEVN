/**
 * PEVN Design System — ToastNotification Component
 *
 * Accessible, responsive notification toast supporting success, error,
 * warning, and info visual treatments with timer pause-on-hover.
 */

import React, { useEffect, useRef, useState } from 'react'
import type { Toast, NotificationType } from '@/types/notification'

interface ToastNotificationProps {
  toast: Toast
  onDismiss: (id: string) => void
}

const variantStyles: Record<
  NotificationType,
  {
    bg: string
    border: string
    titleColor: string
    textColor: string
    badgeBg: string
    iconColor: string
    icon: React.ReactNode
    ariaRole: 'status' | 'alert'
    ariaLive: 'polite' | 'assertive'
  }
> = {
  success: {
    bg: '#F0FDF4',
    border: '#86EFAC',
    titleColor: '#166534',
    textColor: '#15803D',
    badgeBg: '#DCFCE7',
    iconColor: '#16A34A',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
      </svg>
    ),
    ariaRole: 'status',
    ariaLive: 'polite',
  },
  error: {
    bg: '#FEF2F2',
    border: '#FCA5A5',
    titleColor: '#991B1B',
    textColor: '#B91C1C',
    badgeBg: '#FEE2E2',
    iconColor: '#DC2626',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
      </svg>
    ),
    ariaRole: 'alert',
    ariaLive: 'assertive',
  },
  warning: {
    bg: '#FFFBEB',
    border: '#FDE68A',
    titleColor: '#92400E',
    textColor: '#B45309',
    badgeBg: '#FEF3C7',
    iconColor: '#D97706',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
        />
      </svg>
    ),
    ariaRole: 'status',
    ariaLive: 'polite',
  },
  info: {
    bg: '#EFF6FF',
    border: '#BFDBFE',
    titleColor: '#1E40AF',
    textColor: '#1D4ED8',
    badgeBg: '#DBEAFE',
    iconColor: '#2563EB',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
    ),
    ariaRole: 'status',
    ariaLive: 'polite',
  },
}

/** Sanitize sensitive error information from displaying to end users */
export function sanitizeMessage(msg: string): string {
  if (!msg) return ''
  // Strip Bearer tokens
  let clean = msg.replace(/Bearer\s+[A-Za-z0-9-_=.]+/gi, 'Bearer [REDACTED]')
  // Strip JWTs
  clean = clean.replace(/eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*/g, '[TOKEN]')
  // Strip raw SQL snippets
  clean = clean.replace(/SELECT\s+.*?\s+FROM\s+\w+/gi, '[CONSULTA DB]')
  // Strip passwords in URLs or JSON
  clean = clean.replace(/password[:=][^\s&"']+/gi, 'password=[REDACTED]')
  return clean
}

export const ToastNotification: React.FC<ToastNotificationProps> = ({ toast, onDismiss }) => {
  const cfg = variantStyles[toast.type]
  const [isPaused, setIsPaused] = useState(false)
  const remainingTimeRef = useRef(toast.duration ?? 5000)
  const startTimeRef = useRef<number>(Date.now())
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (!toast.duration || toast.duration <= 0) return

    if (!isPaused) {
      startTimeRef.current = Date.now()
      timerRef.current = setTimeout(() => {
        onDismiss(toast.id)
      }, remainingTimeRef.current)
    }

    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current)
        timerRef.current = null
      }
    }
  }, [toast.id, toast.duration, isPaused, onDismiss])

  const handleMouseEnter = () => {
    if (!toast.duration || toast.duration <= 0) return
    setIsPaused(true)
    const elapsed = Date.now() - startTimeRef.current
    remainingTimeRef.current = Math.max(500, remainingTimeRef.current - elapsed)
  }

  const handleMouseLeave = () => {
    if (!toast.duration || toast.duration <= 0) return
    setIsPaused(false)
  }

  const displayMessage = sanitizeMessage(toast.message)

  return (
    <div
      role={cfg.ariaRole}
      aria-live={cfg.ariaLive}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      onFocus={handleMouseEnter}
      onBlur={handleMouseLeave}
      id={`toast-${toast.id}`}
      style={{
        backgroundColor: cfg.bg,
        border: `1.5px solid ${cfg.border}`,
        borderRadius: '12px',
        padding: '0.875rem 1rem',
        boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1)',
        display: 'flex',
        alignItems: 'flex-start',
        gap: '0.75rem',
        maxWidth: '440px',
        width: '100%',
        pointerEvents: 'auto',
        transition: 'all 200ms ease-in-out',
      }}
    >
      {/* Icon Badge */}
      <div
        style={{
          backgroundColor: cfg.badgeBg,
          color: cfg.iconColor,
          borderRadius: '8px',
          padding: '0.35rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
        }}
      >
        {cfg.icon}
      </div>

      {/* Message Content */}
      <div style={{ flex: 1, minWidth: 0, paddingTop: '0.1rem' }}>
        {toast.title && (
          <h4
            style={{
              fontSize: '0.875rem',
              fontWeight: 700,
              color: cfg.titleColor,
              margin: '0 0 0.15rem 0',
              lineHeight: 1.25,
            }}
          >
            {toast.title}
          </h4>
        )}
        <p
          style={{
            fontSize: '0.8125rem',
            color: cfg.textColor,
            margin: 0,
            lineHeight: 1.4,
            wordBreak: 'break-word',
          }}
        >
          {displayMessage}
        </p>
      </div>

      {/* Close Button */}
      <button
        type="button"
        onClick={() => onDismiss(toast.id)}
        aria-label="Cerrar notificación"
        style={{
          background: 'transparent',
          border: 'none',
          cursor: 'pointer',
          padding: '0.25rem',
          borderRadius: '6px',
          color: cfg.titleColor,
          opacity: 0.7,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
          transition: 'opacity 150ms',
        }}
        onMouseEnter={(e) => (e.currentTarget.style.opacity = '1')}
        onMouseLeave={(e) => (e.currentTarget.style.opacity = '0.7')}
      >
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  )
}

