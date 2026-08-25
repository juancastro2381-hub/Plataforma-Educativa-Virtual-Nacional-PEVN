/**
 * PEVN Frontend — Empty State Component
 *
 * Visual placeholder displayed when data collections are empty or filters yield 0 results.
 */

import React from 'react'
import { Button } from './Button'

export interface EmptyStateProps {
  icon?: string
  title: string
  description: string
  actionLabel?: string
  onAction?: () => void
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon = '📋',
  title,
  description,
  actionLabel,
  onAction,
}) => {
  return (
    <div
      style={{
        padding: '3rem 1.5rem',
        textAlign: 'center',
        backgroundColor: '#F8FAFC',
        borderRadius: '12px',
        border: '1px dashed #CBD5E1',
        margin: '1rem 0',
      }}
    >
      <div
        style={{
          fontSize: '2.5rem',
          marginBottom: '0.75rem',
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
          margin: '0 0 1.25rem 0',
          fontSize: '0.875rem',
          color: '#64748B',
          maxWidth: '420px',
          marginLeft: 'auto',
          marginRight: 'auto',
          lineHeight: 1.5,
        }}
      >
        {description}
      </p>
      {actionLabel && onAction && (
        <Button variant="primary" size="sm" onClick={onAction}>
          {actionLabel}
        </Button>
      )}
    </div>
  )
}

export default EmptyState
