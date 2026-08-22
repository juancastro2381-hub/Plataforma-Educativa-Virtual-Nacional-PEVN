/**
 * PEVN Frontend — Error Boundary Component
 *
 * Catches JavaScript errors anywhere in the component tree,
 * logs the error, and renders a fallback UI instead of crashing.
 *
 * Accessibility: Error state is announced to screen readers.
 * Security: Error details are displayed only in development.
 *
 * This must be a class component — React does not support
 * error boundaries as function components.
 */

import { Component } from 'react'
import type { ErrorInfo, ReactNode } from 'react'
import config from '@config/index'

interface ErrorBoundaryProps {
  children?: ReactNode
  /** Optional custom fallback UI */
  fallback?: ReactNode
}

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    // Log the error in development
    // In production, this would send to an error tracking service (e.g., Sentry)
    if (config.isDevelopment) {
      console.error('[ErrorBoundary] Uncaught error:', error, info)
    } else {
      // TODO Phase 4+: Send to error tracking service
      // errorTrackingService.captureException(error, { extra: info })
    }
  }

  handleReset = (): void => {
    this.setState({ hasError: false, error: null })
  }

  render(): ReactNode {
    if (!this.state.hasError) {
      return this.props.children
    }

    if (this.props.fallback) {
      return this.props.fallback
    }

    return (
      <div
        role="alert"
        aria-live="assertive"
        className="min-h-screen bg-pevn-white flex items-center justify-center p-6"
      >
        <div className="max-w-md w-full text-center">
          {/* Icon */}
          <div
            className="w-20 h-20 bg-pevn-red-50 rounded-full flex items-center justify-center mx-auto mb-6"
            aria-hidden="true"
          >
            <svg
              className="w-10 h-10 text-pevn-red"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"
              />
            </svg>
          </div>

          {/* Title */}
          <h1 className="text-2xl font-bold text-pevn-blue mb-3">Ocurrió un error inesperado</h1>

          {/* Message */}
          <p className="text-gray-600 mb-6 leading-relaxed">
            La aplicación encontró un error. Por favor, intente recargar la página. Si el problema
            persiste, contacte al administrador del sistema.
          </p>

          {/* Development error details */}
          {config.isDevelopment && this.state.error && (
            <details className="mb-6 text-left bg-gray-100 rounded-lg p-4">
              <summary className="font-medium text-gray-700 cursor-pointer text-sm">
                Detalles del error (solo en desarrollo)
              </summary>
              <pre className="mt-3 text-xs text-red-700 overflow-auto whitespace-pre-wrap">
                {this.state.error.message}
              </pre>
            </details>
          )}

          {/* Actions */}
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <button
              onClick={this.handleReset}
              className="px-6 py-3 bg-pevn-blue text-white font-semibold rounded-lg hover:bg-pevn-blue-800 focus:outline-none focus:ring-2 focus:ring-pevn-blue focus:ring-offset-2 transition-colors min-h-touch"
              aria-label="Intentar de nuevo"
            >
              Intentar de nuevo
            </button>
            <button
              onClick={() => {
                window.location.reload()
              }}
              className="px-6 py-3 border-2 border-pevn-blue text-pevn-blue font-semibold rounded-lg hover:bg-pevn-blue-50 focus:outline-none focus:ring-2 focus:ring-pevn-blue focus:ring-offset-2 transition-colors min-h-touch"
              aria-label="Recargar la página"
            >
              Recargar página
            </button>
          </div>
        </div>
      </div>
    )
  }
}

export default ErrorBoundary
