/// <reference types="vite/client" />
/// <reference types="vite-plugin-pwa/client" />

/**
 * Type declarations for Vite environment variables.
 * All VITE_ prefixed variables must be declared here for TypeScript support.
 *
 * SECURITY: Never declare variables that contain secrets.
 * All VITE_ variables are bundled into the frontend and visible to users.
 */
interface ImportMetaEnv {
  /** Backend API base URL */
  readonly VITE_API_BASE_URL?: string
  /** Application version */
  readonly VITE_APP_VERSION?: string
  /** Application display name */
  readonly VITE_APP_NAME?: string
  /** Environment name */
  readonly VITE_APP_ENV?: string
  /** API request timeout in milliseconds */
  readonly VITE_API_TIMEOUT_MS?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
