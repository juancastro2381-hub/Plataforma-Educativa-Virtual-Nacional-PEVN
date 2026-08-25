/**
 * PEVN Frontend — RequirePermission Guard
 *
 * Checks fine-grained permissions before rendering protected children.
 */

import React from 'react'
import { useAuth } from '@/hooks/useAuth'
import { Button } from '@/components/ui/Button'
import { Link } from 'react-router-dom'

export interface RequirePermissionProps {
  permission: string | string[]
  children: React.ReactNode
  fallback?: React.ReactNode
}

export const RequirePermission: React.FC<RequirePermissionProps> = ({
  permission,
  children,
  fallback,
}) => {
  const { hasPermission, isAuthenticated } = useAuth()

  if (!isAuthenticated || !hasPermission(permission)) {
    if (fallback) {
      return <>{fallback}</>
    }

    const requiredText = Array.isArray(permission) ? permission.join(', ') : permission

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
            backgroundColor: '#FEF3C7',
            color: '#D97706',
            marginBottom: '1rem',
            fontSize: '1.5rem',
            fontWeight: 'bold',
          }}
        >
          !
        </div>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#0F172A', marginBottom: '0.5rem' }}>
          Permiso Requerido (403)
        </h2>
        <p style={{ color: '#64748B', fontSize: '0.95rem', marginBottom: '1.5rem', lineHeight: 1.5 }}>
          Se requiere el permiso de seguridad (<code>{requiredText}</code>) para ejecutar esta operación.
        </p>
        <Link to="/dashboard" style={{ textDecoration: 'none' }}>
          <Button variant="primary">Volver al Panel</Button>
        </Link>
      </div>
    )
  }

  return <>{children}</>
}

export default RequirePermission
