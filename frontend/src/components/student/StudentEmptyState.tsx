/**
 * PEVN Frontend — Student Portal Empty State Component
 *
 * Provides a clean and friendly empty state message with icon and action.
 */

import React from 'react'

interface StudentEmptyStateProps {
  icon?: string
  title: string
  description: string
  actionLabel?: string
  onAction?: () => void
}

export const StudentEmptyState: React.FC<StudentEmptyStateProps> = ({
  icon = '📂',
  title,
  description,
  actionLabel,
  onAction,
}) => {
  return (
    <div
      style={{
        backgroundColor: '#FFFFFF',
        borderRadius: '12px',
        border: '1px dashed #CBD5E1',
        padding: '3rem 1.5rem',
        textAlign: 'center',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        margin: '1rem 0',
      }}
    >
      <div
        style={{
          fontSize: '2.5rem',
          marginBottom: '0.75rem',
          backgroundColor: '#F8FAFC',
          width: '64px',
          height: '64px',
          borderRadius: '50%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          border: '1px solid #E2E8F0',
        }}
      >
        {icon}
      </div>

      <h3
        style={{
          margin: '0 0 0.5rem 0',
          fontSize: '1.125rem',
          fontWeight: 700,
          color: '#1E293B',
        }}
      >
        {title}
      </h3>

      <p
        style={{
          margin: 0,
          fontSize: '0.875rem',
          color: '#64748B',
          maxWidth: '420px',
          lineHeight: 1.5,
        }}
      >
        {description}
      </p>

      {actionLabel && onAction && (
        <button
          onClick={onAction}
          style={{
            marginTop: '1.25rem',
            backgroundColor: '#1E40AF',
            color: '#FFFFFF',
            border: 'none',
            padding: '0.6rem 1.25rem',
            borderRadius: '8px',
            fontSize: '0.875rem',
            fontWeight: 600,
            cursor: 'pointer',
            transition: 'background-color 0.15s ease',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = '#1D4ED8'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = '#1E40AF'
          }}
        >
          {actionLabel}
        </button>
      )}
    </div>
  )
}
