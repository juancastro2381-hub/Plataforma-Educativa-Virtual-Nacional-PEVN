/**
 * PEVN Frontend — RequireRole Guard
 *
 * Route / component wrapper that requires one or more specific roles.
 * Displays a government-grade 403 Forbidden message if user lacks permissions.
 */

import React from 'react'
import { useAuth } from '@/hooks/useAuth'
import { Button } from '@/components/ui/Button'
import { Link } from 'react-router-dom'

export interface RequireRoleProps {
  roles: string | string[]
  children: React.ReactNode
  fallback?: React.ReactNode
}

export const RequireRole: React.FC<RequireRoleProps> = ({
  roles,
  children,
  fallback,
}) => {
  const { hasRole, isAuthenticated } = useAuth()

  if (!isAuthenticated || !hasRole(roles)) {
    if (fallback) {
      return <>{fallback}</>
    }

    const requiredText = Array.isArray(roles) ? roles.join(', ') : roles

    return (
      <div
        style={{
          maxWidth: '560px',
          margin: '3rem auto',
          padding: '2.5rem',
          backgroundColor: 'var(--color-bg-card, #FFFFFF)',
          borderRadius: 'var(--border-radius-lg, 12px)',
          border: '1px solid var(--color-border, #E2E8F0)',
          boxShadow: 'var(--shadow-md, 0 4px 6px -1px rgba(0,0,0,0.1))',
          textAlign: 'center',
        }}
        role="alert"
        aria-live="polite"
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '48px',
            height: '48px',
            borderRadius: '50%',
            backgroundColor: '#FEE2E2',
            color: '#DC2626',
            marginBottom: '1rem',
            fontSize: '1.5rem',
            fontWeight: 'bold',
          }}
        >
          !
        </div>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#0F172A', marginBottom: '0.5rem' }}>
          Acceso Restringido (403)
        </h2>
        <p style={{ color: '#64748B', fontSize: '0.95rem', marginBottom: '1.5rem', lineHeight: 1.5 }}>
          No cuenta con los roles requeridos (<code>{requiredText}</code>) para acceder a este módulo institucional.
        </p>
        <Link to="/dashboard" style={{ textDecoration: 'none' }}>
          <Button variant="primary">Volver al Panel Principal</Button>
        </Link>
      </div>
    )
  }

  return <>{children}</>
}

export default RequireRole
