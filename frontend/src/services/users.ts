/**
 * PEVN Frontend — Users API Service
 *
 * Strongly-typed API client service for tenant-isolated user search and queries.
 */

import apiClient from '@/services/api/client'
import type { UserListResponse, UserResponse } from '@/types'

export interface UserSearchParams {
  search?: string
  is_active?: boolean
  institution_id?: string
  page?: number
  page_size?: number
}

export const usersApi = {
  /**
   * Search and list institutional users matching the search query.
   */
  async searchUsers(params?: UserSearchParams): Promise<UserListResponse> {
    const response = await apiClient.get<UserListResponse>('/api/v1/users', {
      params,
    })
    return response.data
  },

  /**
   * Retrieve single user details by ID.
   */
  async getUserById(userId: string): Promise<UserResponse> {
    const response = await apiClient.get<UserResponse>(`/api/v1/users/${userId}`)
    return response.data
  },
}
