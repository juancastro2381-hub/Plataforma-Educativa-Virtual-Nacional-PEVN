/**
 * PEVN Frontend — Test Setup
 *
 * Configures the test environment for Vitest + React Testing Library.
 */

import '@testing-library/jest-dom'
import { afterAll, beforeAll } from 'vitest'

// Mock import.meta.env for tests
Object.defineProperty(import.meta, 'env', {
  value: {
    VITE_API_BASE_URL: 'http://localhost:8000',
    VITE_APP_VERSION: '0.1.0',
    VITE_APP_NAME: 'Plataforma Educativa Virtual Nacional',
    VITE_APP_ENV: 'test',
    VITE_API_TIMEOUT_MS: '30000',
    DEV: false,
    PROD: false,
    MODE: 'test',
  },
  writable: true,
})

// Suppress console.error in tests unless explicitly needed
const originalConsoleError = console.error
beforeAll(() => {
  console.error = (...args: unknown[]) => {
    // Allow actual test failures to still be reported
    if (
      typeof args[0] === 'string' &&
      (args[0].includes('Warning: ReactDOM.render') || args[0].includes('Warning: An update'))
    ) {
      return
    }
    originalConsoleError(...args)
  }
})

afterAll(() => {
  console.error = originalConsoleError
})
