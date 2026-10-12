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
import { institutionApi } from '@/services/institution'
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
  const [activeInstitutionId, setActiveInstitutionIdState] = useState<string | null>(() => {
    try {
      return localStorage.getItem('pevn_active_institution_id') || null
    } catch {
      return null
    }
  })
  const [activeInstitutionName, setActiveInstitutionNameState] = useState<string | null>(() => {
    try {
      return localStorage.getItem('pevn_active_institution_name') || null
    } catch {
      return null
    }
  })

  const setActiveInstitutionContext = useCallback((id: string | null, name?: string | null) => {
    try {
      if (id) {
        localStorage.setItem('pevn_active_institution_id', id)
        if (name) {
          localStorage.setItem('pevn_active_institution_name', name)
        } else {
          localStorage.removeItem('pevn_active_institution_name')
        }
      } else {
        localStorage.removeItem('pevn_active_institution_id')
        localStorage.removeItem('pevn_active_institution_name')
      }
    } catch {
      // Non-blocking localStorage access error (e.g. incognito)
    }
    setActiveInstitutionIdState(id)
    setActiveInstitutionNameState(name || null)
  }, [])

  const syncInstitutionalContext = useCallback(async (u: User) => {
    const instId = u.institution_id || u.scope?.institution_id
    if (!instId) {
      // Clear any prior active context for global or unassigned accounts
      setActiveInstitutionContext(null)
      return
    }

    let instName = ''
    try {
      instName = localStorage.getItem('pevn_active_institution_name') || ''
    } catch {
      instName = ''
    }
    setActiveInstitutionContext(instId, instName || undefined)
    if (!instName) {
      try {
        const instData = await institutionApi.getMyInstitution()
        if (instData?.name) {
          setActiveInstitutionContext(instId, instData.name)
        }
      } catch {
        // Non-blocking fallback
      }
    }
  }, [setActiveInstitutionContext])

  // Register callback for when token refresh fails in API interceptor
  useEffect(() => {
    setOnAuthFailure(() => {
      setUser(null)
      setActiveInstitutionContext(null)
    })
    return () => {
      setOnAuthFailure(null)
    }
  }, [setActiveInstitutionContext])

  // Silent session restore on app load (Single-Flight refresh + Canonical Profile)
  useEffect(() => {
    let isMounted = true

    const initAuth = async () => {
      try {
        await authApi.refresh()
        const userProfile = await authApi.getMyProfile()
        if (isMounted) {
          setUser(userProfile)
          void syncInstitutionalContext(userProfile)
        }
      } catch {
        if (isMounted) {
          setUser(null)
          setActiveInstitutionContext(null)
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
  }, [setActiveInstitutionContext, syncInstitutionalContext])

  const login = useCallback(async (credentials: LoginRequest) => {
    setIsLoading(true)
    try {
      // Reset institutional context upon explicit login before binding new user
      setActiveInstitutionContext(null)
      const data = await authApi.login(credentials)
      setUser(data.user)
      void syncInstitutionalContext(data.user)
    } finally {
      setIsLoading(false)
    }
  }, [setActiveInstitutionContext, syncInstitutionalContext])

  const logout = useCallback(async () => {
    setIsLoading(true)
    try {
      await authApi.logout()
    } finally {
      setUser(null)
      setActiveInstitutionContext(null)
      setIsLoading(false)
    }
  }, [setActiveInstitutionContext])

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
      void syncInstitutionalContext(profile)
    } catch {
      setUser(null)
    }
  }, [syncInstitutionalContext])

  const hasRole = useCallback(
    (roles: string | string[]): boolean => {
      if (!user) return false

      const checkList = Array.isArray(roles) ? roles : [roles]
      const userRoles = user.roles.map((r) => r.toLowerCase())

      // Canonical role equivalence mapping:
      // rector <-> institution_admin
      // coordinator <-> academic_coordinator
      // superadmin <-> super_admin
      const effectiveUserRoles = new Set<string>(userRoles)
      if (userRoles.includes('rector') || userRoles.includes('institution_admin')) {
        effectiveUserRoles.add('rector')
        effectiveUserRoles.add('institution_admin')
      }
      if (userRoles.includes('coordinator') || userRoles.includes('academic_coordinator')) {
        effectiveUserRoles.add('coordinator')
        effectiveUserRoles.add('academic_coordinator')
      }
      if (userRoles.includes('superadmin') || userRoles.includes('super_admin')) {
        effectiveUserRoles.add('superadmin')
        effectiveUserRoles.add('super_admin')
      }

      return checkList.some((r) => effectiveUserRoles.has(r.toLowerCase()))
    },
    [user]
  )

  const hasPermission = useCallback(
    (permissions: string | string[]): boolean => {
      if (!user) return false
      // SuperAdmin or explicit wildcard bypasses permission checks
      if (
        user.roles.includes('superadmin') ||
        user.roles.includes('super_admin') ||
        user.permissions.includes('*')
      ) {
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
      if (
        user.roles.includes('superadmin') ||
        user.roles.includes('super_admin') ||
        user.scope.is_national
      ) {
        // If an explicit active institution context is selected, verify against it when requested
        if (targetInstitutionId && activeInstitutionId) {
          return targetInstitutionId === activeInstitutionId
        }
        return true
      }
      if (!targetInstitutionId) return true
      return (user.scope.institution_id || activeInstitutionId) === targetInstitutionId
    },
    [user, activeInstitutionId]
  )

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isAuthenticated: Boolean(user),
      isLoading,
      activeInstitutionId,
      activeInstitutionName,
      setActiveInstitutionContext,
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
      activeInstitutionId,
      activeInstitutionName,
      setActiveInstitutionContext,
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
