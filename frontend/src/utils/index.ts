/**
 * PEVN Frontend — Utility Functions
 *
 * Pure utility functions used across the application.
 * No side effects, no external dependencies.
 */

// ---------------------------------------------------------------------------
// Class name utilities
// ---------------------------------------------------------------------------

/**
 * Conditionally joins class names, filtering out falsy values.
 * Lightweight alternative to the 'clsx' package for basic use cases.
 *
 * @example
 * cn('base-class', isActive && 'active', undefined)
 * // => 'base-class active'
 */
export function cn(...classes: (string | false | null | undefined)[]): string {
  return classes.filter(Boolean).join(' ')
}

// ---------------------------------------------------------------------------
// Date utilities
// ---------------------------------------------------------------------------

/**
 * Format a date as a localized string for Colombian/Spanish context.
 */
export function formatDate(date: Date | string, options?: Intl.DateTimeFormatOptions): string {
  const d = typeof date === 'string' ? new Date(date) : date
  return new Intl.DateTimeFormat('es-CO', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    ...options,
  }).format(d)
}

/**
 * Format a date-time for display.
 */
export function formatDateTime(date: Date | string): string {
  return formatDate(date, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// ---------------------------------------------------------------------------
// String utilities
// ---------------------------------------------------------------------------

/**
 * Truncate a string to the given length, adding an ellipsis if needed.
 */
export function truncate(str: string, maxLength: number): string {
  if (str.length <= maxLength) return str
  return `${str.slice(0, maxLength - 3)}...`
}

/**
 * Convert a string to title case.
 */
export function toTitleCase(str: string): string {
  return str.replace(/\w\S*/g, (word) => {
    return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
  })
}

// ---------------------------------------------------------------------------
// Validation utilities
// ---------------------------------------------------------------------------

/**
 * Check if a string is a valid Colombian cédula format.
 * Phase 1: Basic format check only — not a definitive validation.
 */
export function isValidCedula(cedula: string): boolean {
  return /^\d{6,10}$/.test(cedula.trim())
}

// ---------------------------------------------------------------------------
// Accessibility utilities
// ---------------------------------------------------------------------------

/**
 * Generate a unique ID for DOM elements (for ARIA associations).
 * Uses crypto.randomUUID if available, falls back to timestamp.
 */
export function generateId(prefix = 'pevn'): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return `${prefix}-${crypto.randomUUID()}`
  }
  return `${prefix}-${Date.now().toString()}-${Math.random().toString(36).slice(2)}`
}

// ---------------------------------------------------------------------------
// Error utilities
// ---------------------------------------------------------------------------

/**
 * Extract a user-friendly error message from an unknown error value.
 * Used in catch blocks where the error type is unknown.
 */
export function getErrorMessage(error: unknown): string {
  if (error instanceof Error) return error.message
  if (typeof error === 'string') return error
  return 'Ha ocurrido un error inesperado'
}
