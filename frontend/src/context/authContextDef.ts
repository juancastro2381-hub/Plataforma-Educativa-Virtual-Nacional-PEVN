import { createContext } from 'react'
import type {
  ChangePasswordRequest,
  LoginRequest,
  User,
} from '@/types'

export interface AuthContextValue {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  activeInstitutionId: string | null
  activeInstitutionName: string | null
  setActiveInstitutionContext: (id: string | null, name?: string | null) => void
  login: (credentials: LoginRequest) => Promise<void>
  logout: () => Promise<void>
  changePassword: (data: ChangePasswordRequest) => Promise<void>
  refreshUser: () => Promise<void>
  hasRole: (role: string | string[]) => boolean
  hasPermission: (permission: string | string[]) => boolean
  isInScope: (targetInstitutionId?: string | null) => boolean
}

export const AuthContext = createContext<AuthContextValue | undefined>(undefined)

