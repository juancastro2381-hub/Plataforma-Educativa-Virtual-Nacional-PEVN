/**
 * PEVN Frontend — Guardian Empty State Component
 *
 * Friendly, styled empty states for guardian subviews.
 */

import React from 'react'

interface Props {
  icon: string
  title: string
  description: string
  actionLabel?: string
  onAction?: () => void
}

export const GuardianEmptyState: React.FC<Props> = ({
  icon,
  title,
  description,
  actionLabel,
  onAction,
}) => {
  return (
    <div
      style={{
        padding: '3.5rem 1.5rem',
        textAlign: 'center',
        backgroundColor: '#FFFFFF',
        borderRadius: '16px',
        border: '2px dashed #CBD5E1',
        margin: '1rem 0',
      }}
    >
      <div style={{ fontSize: '3rem', marginBottom: '0.75rem' }}>{icon}</div>
      <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1.25rem', fontWeight: 800, color: '#0F172A' }}>
        {title}
      </h3>
      <p
        style={{
          margin: '0 auto 1.5rem auto',
          maxWidth: '480px',
          fontSize: '0.875rem',
          color: '#64748B',
          lineHeight: 1.6,
        }}
      >
        {description}
      </p>

      {actionLabel && onAction && (
        <button
          type="button"
          onClick={onAction}
          style={{
            padding: '0.625rem 1.25rem',
            borderRadius: '8px',
            backgroundColor: '#0F172A',
            color: '#FFFFFF',
            border: 'none',
            fontSize: '0.875rem',
            fontWeight: 700,
            cursor: 'pointer',
            transition: 'background-color 150ms ease',
          }}
        >
          {actionLabel}
        </button>
      )}
    </div>
  )
}
