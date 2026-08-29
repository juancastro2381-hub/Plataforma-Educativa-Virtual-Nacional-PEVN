/**
 * PEVN Frontend — Single-Flight Token Refresh Coordinator Tests
 *
 * Validates:
 *   - Scenario A: Unauthenticated cold-start 401 error normalization
 *   - Scenario C: Exactly one refresh request during concurrent execution
 *   - Scenario D: Concurrent callers await the shared Promise and receive the same token
 *   - Promise cleanup on both success and error
 */

import { describe, expect, it, vi, beforeEach } from 'vitest'
import {
  requestTokenRefresh,
  setAccessToken,
  getAccessToken,
  setOnAuthFailure,
  rawAuthClient,
} from '@/services/api/client'

describe('Single-Flight Refresh Coordinator', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    setAccessToken(null)
    setOnAuthFailure(null)
  })

  it('Scenario D: Coordinates concurrent refresh calls into exactly ONE in-flight HTTP request', async () => {
    let callCount = 0
    const mockPost = vi.spyOn(rawAuthClient, 'post').mockImplementation(async () => {
      callCount++
      // Simulate network delay
      await new Promise((resolve) => setTimeout(resolve, 50))
      return {
        data: {
          access_token: 'fresh-jwt-token-123',
          token_type: 'bearer',
          expires_in: 900,
        },
      } as any
    })

    // Simulate 5 simultaneous callers hitting refresh
    const [t1, t2, t3, t4, t5] = await Promise.all([
      requestTokenRefresh(),
      requestTokenRefresh(),
      requestTokenRefresh(),
      requestTokenRefresh(),
      requestTokenRefresh(),
    ])

    // Invariant: Exactly 1 HTTP POST to /auth/refresh
    expect(callCount).toBe(1)
    expect(mockPost).toHaveBeenCalledTimes(1)

    // All callers receive the exact same new token
    expect(t1).toBe('fresh-jwt-token-123')
    expect(t2).toBe('fresh-jwt-token-123')
    expect(t3).toBe('fresh-jwt-token-123')
    expect(t4).toBe('fresh-jwt-token-123')
    expect(t5).toBe('fresh-jwt-token-123')

    // In-memory token is atomicity updated
    expect(getAccessToken()).toBe('fresh-jwt-token-123')
  })

  it('Scenario A: Handles cold-start 401 failure, invokes auth failure callback, and resets promise', async () => {
    const authFailureSpy = vi.fn()
    setOnAuthFailure(authFailureSpy)

    vi.spyOn(rawAuthClient, 'post').mockRejectedValueOnce({
      isAxiosError: true,
      response: {
        status: 401,
        data: {
          error: {
            code: 'AUTHENTICATION_REQUIRED',
            message: 'Refresh token ausente en la solicitud.',
            correlation_id: 'corr-001',
          },
        },
      },
    })

    await expect(requestTokenRefresh()).rejects.toThrow()

    expect(authFailureSpy).toHaveBeenCalledTimes(1)
    expect(getAccessToken()).toBeNull()

    // Verify promise was cleared: subsequent call can execute without being stuck
    vi.spyOn(rawAuthClient, 'post').mockResolvedValueOnce({
      data: {
        access_token: 'retry-token-456',
        token_type: 'bearer',
        expires_in: 900,
      },
    } as any)

    const retryToken = await requestTokenRefresh()
    expect(retryToken).toBe('retry-token-456')
    expect(getAccessToken()).toBe('retry-token-456')
  })
})
