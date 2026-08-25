/**
 * PEVN Frontend — Status Badge Component
 *
 * Visual status pill supporting academic lifecycle states.
 */

import React from 'react'

export type BadgeVariant =
  | 'success'
  | 'warning'
  | 'danger'
  | 'info'
  | 'neutral'
  | 'primary'

export interface BadgeProps {
  children: React.ReactNode
  variant?: BadgeVariant
  size?: 'sm' | 'md'
  className?: string
}

const variantStyles: Record<BadgeVariant, { bg: string; color: string; border: string }> = {
  success: {
    bg: '#ECFDF5',
    color: '#065F46',
    border: '#A7F3D0',
  },
  warning: {
    bg: '#FFFBEB',
    color: '#92400E',
    border: '#FDE68A',
  },
  danger: {
    bg: '#FEF2F2',
    color: '#991B1B',
    border: '#FECACA',
  },
  info: {
    bg: '#EFF6FF',
    color: '#1E40AF',
    border: '#BFDBFE',
  },
  neutral: {
    bg: '#F1F5F9',
    color: '#475569',
    border: '#E2E8F0',
  },
  primary: {
    bg: '#EEF2FF',
    color: '#3730A3',
    border: '#C7D2FE',
  },
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'neutral',
  size = 'md',
}) => {
  const style = variantStyles[variant]
  const isSm = size === 'sm'

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.35rem',
        padding: isSm ? '0.15rem 0.5rem' : '0.25rem 0.75rem',
        fontSize: isSm ? '0.75rem' : '0.8125rem',
        fontWeight: 600,
        borderRadius: '9999px',
        backgroundColor: style.bg,
        color: style.color,
        border: `1px solid ${style.border}`,
        lineHeight: 1.25,
        whiteSpace: 'nowrap',
      }}
    >
      {children}
    </span>
  )
}

export default Badge
