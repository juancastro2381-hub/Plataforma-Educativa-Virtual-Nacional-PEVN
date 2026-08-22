/**
 * PEVN Frontend — Application Configuration
 *
 * Centralized access to environment-based configuration.
 * All values come from VITE_ environment variables.
 *
 * SECURITY: This module must NEVER contain secrets, passwords, tokens,
 * or API keys. All values are bundled into the client-side JavaScript
 * and are visible to any user who inspects the browser.
 */

const config = {
  /** Backend API base URL */
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000',

  /** API v1 endpoint prefix */
  apiV1Prefix: '/api/v1',

  /** Application version */
  version: import.meta.env.VITE_APP_VERSION ?? '0.1.0',

  /** Application display name */
  appName: import.meta.env.VITE_APP_NAME ?? 'Plataforma Educativa Virtual Nacional',

  /** Short application name */
  appShortName: 'PEVN',

  /** Current environment */
  environment: import.meta.env.VITE_APP_ENV ?? 'development',

  /** API request timeout in milliseconds */
  apiTimeoutMs: parseInt(import.meta.env.VITE_API_TIMEOUT_MS ?? '30000', 10),

  /** Whether running in development mode */
  isDevelopment: import.meta.env.DEV,

  /** Whether running in production mode */
  isProduction: import.meta.env.PROD,
} as const

export default config

/** Full API v1 base URL (convenience accessor) */
export const API_V1_URL = `${config.apiBaseUrl}${config.apiV1Prefix}`
