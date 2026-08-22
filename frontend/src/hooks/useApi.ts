/**
 * PEVN Frontend — useApi Hook
 *
 * Generic hook for managing async API call state.
 * Provides loading, error, and data state management.
 *
 * Features:
 *   - Tracks loading, success, and error states
 *   - Handles component unmount gracefully
 *   - Returns strongly-typed data and errors
 *
 * Usage:
 *   const { state, data, error, execute } = useApi(checkHealth)
 *   await execute()
 */

import { useCallback, useEffect, useState } from 'react'
import type { DependencyList } from 'react'
import type { ApiResult, AsyncState } from '@/types'

// ---------------------------------------------------------------------------
// Hook definition
// ---------------------------------------------------------------------------

interface UseApiReturn<T> extends AsyncState<T> {
  /** Execute the API call */
  execute: () => Promise<void>
  /** Reset state to idle */
  reset: () => void
  /** Whether the request is in flight */
  isLoading: boolean
  /** Whether the last request succeeded */
  isSuccess: boolean
  /** Whether the last request failed */
  isError: boolean
}

/**
 * Hook for managing a single API call's lifecycle state.
 *
 * @param apiFn - Async function that returns ApiResult<T>
 * @returns State object with execute() and reset() controls
 */
export function useApi<T>(apiFn: () => Promise<ApiResult<T>>): UseApiReturn<T> {
  const [asyncState, setAsyncState] = useState<AsyncState<T>>({
    state: 'idle',
    data: null,
    error: null,
  })

  const execute = useCallback(async () => {
    setAsyncState({ state: 'loading', data: null, error: null })

    const result = await apiFn()

    if (result.success) {
      setAsyncState({ state: 'success', data: result.data, error: null })
    } else {
      setAsyncState({ state: 'error', data: null, error: result.error })
    }
  }, [apiFn])

  const reset = useCallback(() => {
    setAsyncState({ state: 'idle', data: null, error: null })
  }, [])

  return {
    ...asyncState,
    execute,
    reset,
    isLoading: asyncState.state === 'loading',
    isSuccess: asyncState.state === 'success',
    isError: asyncState.state === 'error',
  }
}

// ---------------------------------------------------------------------------
// useAsyncEffect — run an async function on mount
// ---------------------------------------------------------------------------

/**
 * Run an async API call on component mount.
 *
 * @example
 * useAsyncEffect(async () => {
 *   const result = await checkHealth()
 *   if (result.success) setHealth(result.data)
 * }, [])
 */
export function useAsyncEffect(asyncFn: () => Promise<void>, deps: DependencyList): void {
  useEffect(() => {
    let cancelled = false

    void asyncFn().catch((err: unknown) => {
      if (!cancelled) {
        console.error('useAsyncEffect error:', err)
      }
    })

    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)
}
