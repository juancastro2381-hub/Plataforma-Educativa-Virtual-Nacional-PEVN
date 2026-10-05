/**
 * PEVN Frontend — RequireAuth Guard
 *
 * Route wrapper that ensures the user is authenticated.
 * If not authenticated, redirects to /login while preserving the attempted location.
 */

import React from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'

export interface RequireAuthProps {
  children: React.ReactNode
  roles?: string | string[]
  permissions?: string | string[]
  requireInstitutionContext?: boolean
}

export const RequireAuth: React.FC<RequireAuthProps> = ({
  children,
  roles,
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
    return <Navigate to="/login" state={{ from: location }} replace />
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
      return <Navigate to="/dashboard" replace />
    }
  }

  return <>{children}</>
}

export default RequireAuth
