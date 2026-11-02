/**
 * PEVN Frontend — RequireAuth Guard
 *
 * Route wrapper that ensures the user is authenticated.
 * If not authenticated, redirects to /login while preserving the attempted location.
 */

import React from 'react'
import { Link, Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'

export interface RequireAuthProps {
  children: React.ReactNode
  roles?: string | string[]
  denyRoles?: string | string[]
  permissions?: string | string[]
  requireInstitutionContext?: boolean
}

export const RequireAuth: React.FC<RequireAuthProps> = ({
  children,
  roles,
  denyRoles,
  permissions,
  requireInstitutionContext = false,
}) => {
  const { isAuthenticated, isLoading, hasRole, hasPermission, user, activeInstitutionId } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return (
      <div
        style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '60vh',
        }}
        aria-label="Verificando sesión..."
      >
        <LoadingSpinner size="lg" label="Verificando sesión..." />
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (denyRoles && hasRole(denyRoles)) {
    return (
      <div style={{ maxWidth: '800px', margin: '3rem auto', padding: '0 1rem' }}>
        <div
          style={{
            backgroundColor: '#FFF1F2',
            border: '1px solid #FECDD3',
            borderRadius: '12px',
            padding: '2rem',
            textAlign: 'center',
          }}
          role="alert"
        >
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🚫</div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#9F1239', margin: '0 0 0.5rem 0' }}>
            Acceso Restringido (403)
          </h1>
          <p style={{ color: '#881337', fontSize: '0.95rem', lineHeight: '1.6', margin: '0 0 1.5rem 0' }}>
            Este módulo corresponde a operaciones educativas institucionales y no forma parte del alcance operativo territorial asignado a su rol. Diríjase a su panel de gestión territorial.
          </p>
          <Link
            to="/dashboard"
            style={{
              display: 'inline-block',
              backgroundColor: '#BE123C',
              color: '#FFFFFF',
              fontWeight: 700,
              fontSize: '0.875rem',
              padding: '0.625rem 1.25rem',
              borderRadius: '8px',
              textDecoration: 'none',
            }}
          >
            Volver al Panel Principal
          </Link>
        </div>
      </div>
    )
  }

  if (roles && !hasRole(roles)) {
    return <Navigate to="/dashboard" replace />
  }

  if (permissions && !hasPermission(permissions)) {
    return <Navigate to="/dashboard" replace />
  }

  if (requireInstitutionContext) {
    const hasContext = Boolean(user?.scope?.institution_id || activeInstitutionId)
    if (!hasContext) {
      if (hasPermission('institutions:read')) {
        const returnTo = encodeURIComponent(location.pathname + location.search)
        return <Navigate to={`/admin/institutions?contextRequired=true&returnTo=${returnTo}`} replace />
      }
      return <Navigate to="/dashboard" replace />
    }
  }

  return <>{children}</>
}

export default RequireAuth
