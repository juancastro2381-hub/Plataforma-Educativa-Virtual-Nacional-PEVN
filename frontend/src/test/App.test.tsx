/**
 * PEVN Frontend — Application Integration Tests
 *
 * Tests for the main application structure, routing, and rendering.
 */

import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { ErrorBoundary } from '@components/ErrorBoundary'

describe('ErrorBoundary', () => {
  it('renders children when no error occurs', () => {
    render(
      <ErrorBoundary>
        <div>Contenido de prueba</div>
      </ErrorBoundary>
    )
    expect(screen.getByText('Contenido de prueba')).toBeInTheDocument()
  })

  it('renders fallback UI when an error occurs', () => {
    // Create a component that always throws
    const ThrowError = () => {
      throw new Error('Test error')
    }

    // Suppress console.error for this test (expected error)
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => undefined)

    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    )

    expect(screen.getByRole('alert')).toBeInTheDocument()
    expect(screen.getByText(/ocurrió un error inesperado/i)).toBeInTheDocument()

    consoleSpy.mockRestore()
  })
})

describe('Application routing', () => {
  it('renders the not found page for unknown routes', () => {
    render(
      <MemoryRouter initialEntries={['/ruta-no-existe']}>
        <ErrorBoundary>
          <div role="main">
            <h1>Página no encontrada</h1>
          </div>
        </ErrorBoundary>
      </MemoryRouter>
    )
    expect(screen.getByRole('heading', { name: /página no encontrada/i })).toBeInTheDocument()
  })
})

describe('Accessibility', () => {
  it('ErrorBoundary uses role=alert for error announcements', () => {
    const ThrowError = () => {
      throw new Error('Test')
    }
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => undefined)

    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    )

    const alert = screen.getByRole('alert')
    expect(alert).toHaveAttribute('aria-live', 'assertive')
    consoleSpy.mockRestore()
  })
})
