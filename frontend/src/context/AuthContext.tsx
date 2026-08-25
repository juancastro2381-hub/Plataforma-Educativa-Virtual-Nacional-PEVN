/**
 * PEVN Frontend — Authentication Context Provider
 *
 * Provides reactive authentication state across the entire React component tree.
 * Enforces in-memory token lifecycle, silent background session recovery,
 * and client-side RBAC / scope helper utilities.
 */

import React, {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from 'react'
import authApi from '@/services/auth'
import { setOnAuthFailure } from '@/services/api/client'
import { AuthContext, type AuthContextValue } from '@/context/authContextDef'
import type {
  ChangePasswordRequest,
  LoginRequest,
  User,
} from '@/types'

export interface AuthProviderProps {
  children: React.ReactNode
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(true)

  // Register callback for when token refresh fails in API interceptor
  useEffect(() => {
    setOnAuthFailure(() => {
      setUser(null)
    })
    return () => {
      setOnAuthFailure(null)
    }
  }, [])

  // Silent session restore on app load
  useEffect(() => {
    let isMounted = true

    const initAuth = async () => {
      try {
        const data = await authApi.refresh()
        if (isMounted) {
          setUser(data.user)
        }
      } catch {
        if (isMounted) {
          setUser(null)
        }
      } finally {
        if (isMounted) {
          setIsLoading(false)
        }
      }
    }

    void initAuth()

    return () => {
      isMounted = false
    }
  }, [])

  const login = useCallback(async (credentials: LoginRequest) => {
    setIsLoading(true)
    try {
      const data = await authApi.login(credentials)
      setUser(data.user)
    } finally {
      setIsLoading(false)
    }
  }, [])

  const logout = useCallback(async () => {
    setIsLoading(true)
    try {
      await authApi.logout()
    } finally {
      setUser(null)
      setIsLoading(false)
    }
  }, [])

  const changePassword = useCallback(
    async (data: ChangePasswordRequest) => {
      await authApi.changePassword(data)
      if (user) {
        setUser({ ...user, must_change_password: false })
      }
    },
    [user]
  )

  const refreshUser = useCallback(async () => {
    try {
      const profile = await authApi.getMyProfile()
      setUser(profile)
    } catch {
      setUser(null)
    }
  }, [])

  const hasRole = useCallback(
    (roles: string | string[]): boolean => {
      if (!user) return false
      // SuperAdmin bypasses all role checks
      if (user.roles.includes('superadmin')) return true

      const checkList = Array.isArray(roles) ? roles : [roles]
      return checkList.some((r) => user.roles.includes(r.toLowerCase()))
    },
    [user]
  )

  const hasPermission = useCallback(
    (permissions: string | string[]): boolean => {
      if (!user) return false
      // SuperAdmin bypasses all permission checks
      if (user.roles.includes('superadmin') || user.permissions.includes('*')) {
        return true
      }

      const checkList = Array.isArray(permissions) ? permissions : [permissions]
      return checkList.some((p) => {
        const [reqResource, reqAction] = p.split(':')
        return (
          user.permissions.includes(p) ||
          user.permissions.includes(`${reqResource}:*`) ||
          user.permissions.includes(`*:${reqAction}`)
        )
      })
    },
    [user]
  )

  const isInScope = useCallback(
    (targetInstitutionId?: string | null): boolean => {
      if (!user) return false
      if (user.roles.includes('superadmin') || user.scope.is_national) {
        return true
      }
      if (!targetInstitutionId) return true
      return user.scope.institution_id === targetInstitutionId
    },
    [user]
  )

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isAuthenticated: Boolean(user),
      isLoading,
      login,
      logout,
      changePassword,
      refreshUser,
      hasRole,
      hasPermission,
      isInScope,
    }),
    [
      user,
      isLoading,
      login,
      logout,
      changePassword,
      refreshUser,
      hasRole,
      hasPermission,
      isInScope,
    ]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export default AuthProvider
