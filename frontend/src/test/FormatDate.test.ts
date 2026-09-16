/**
 * PEVN Frontend — FormatDate Utility Unit Tests (H2-CORRECCIÓN)
 *
 * Validates:
 *   - CASO 1: YYYY-MM-DD calendar date ("2026-09-12") renders as "12 de septiembre de 2026"
 *             and NEVER regresses to "11 de septiembre de 2026".
 *   - CASO 2: Beginning of year ("2026-01-01") -> "1 de enero de 2026".
 *   - CASO 3: End of year ("2026-12-31") -> "31 de diciembre de 2026".
 *   - CASO 4: UTC ISO Timestamp ("2026-09-12T18:30:00Z") preserves timestamp/instant semantics.
 *   - CASO 5: Date object instance preserves existing behavior.
 *   - CASO 6: null -> ''.
 *   - CASO 7: undefined -> ''.
 *   - Explicit America/Bogota (UTC-5) timezone verification ensuring calendar dates do not shift.
 */

import { describe, expect, it } from 'vitest'
import { formatDate, formatDateTime } from '@/utils'

describe('formatDate Utility (H2 Controlled Date Shift Correction)', () => {
  // -------------------------------------------------------------------------
  // Core Requirements (Section 4 & 5)
  // -------------------------------------------------------------------------

  it('CASO 1: Formats date-only string YYYY-MM-DD as local calendar date without -1 day shift', () => {
    const input = '2026-09-12'
    const result = formatDate(input)

    // Must match exact expected calendar date
    expect(result).toBe('12 de septiembre de 2026')

    // Must NEVER regress to the previous day (the bug diagnosed in H2)
    expect(result).not.toContain('11 de septiembre')
  })

  it('CASO 2: Formats beginning of year "2026-01-01" accurately', () => {
    const input = '2026-01-01'
    const result = formatDate(input)

    expect(result).toBe('1 de enero de 2026')
    expect(result).not.toContain('31 de diciembre de 2025')
  })

  it('CASO 3: Formats end of year "2026-12-31" accurately', () => {
    const input = '2026-12-31'
    const result = formatDate(input)

    expect(result).toBe('31 de diciembre de 2026')
    expect(result).not.toContain('30 de diciembre')
  })

  it('CASO 4: Preserves timestamp/instant semantics for full ISO strings with time/timezone', () => {
    const timestamp = '2026-09-12T18:30:00Z'
    const formatted = formatDate(timestamp)

    // Should produce a formatted date without throwing or truncating
    expect(formatted).toBeTruthy()
    expect(typeof formatted).toBe('string')

    // formatDateTime should include both date and time representation
    const detailed = formatDateTime(timestamp)
    expect(detailed).toBeTruthy()
    expect(detailed).toContain('2026')
  })

  it('CASO 5: Preserves behavior for native Date object inputs', () => {
    const dateObj = new Date(2026, 8, 12) // September 12, 2026 in local time
    const result = formatDate(dateObj)

    expect(result).toBe('12 de septiembre de 2026')
  })

  it('CASO 6: Returns empty string for null input', () => {
    expect(formatDate(null)).toBe('')
    expect(formatDateTime(null)).toBe('')
  })

  it('CASO 7: Returns empty string for undefined input', () => {
    expect(formatDate(undefined)).toBe('')
    expect(formatDateTime(undefined)).toBe('')
  })

  // -------------------------------------------------------------------------
  // Timezone & Colombian Context Validation (Section 5)
  // -------------------------------------------------------------------------

  it('Demonstrates prevention of the UTC-5 America/Bogota regression', () => {
    const attendanceDate = '2026-09-12'

    // The legacy behavior: new Date("2026-09-12") parsed as UTC midnight
    const legacyUtcDate = new Date(attendanceDate)
    const legacyFormatted = new Intl.DateTimeFormat('es-CO', {
      timeZone: 'America/Bogota',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    }).format(legacyUtcDate)

    // Demonstrating that legacy parsing rolled back to 11 de septiembre in America/Bogota
    expect(legacyFormatted).toBe('11 de septiembre de 2026')

    // The corrected formatDate function produces the true calendar date
    const correctedResult = formatDate(attendanceDate)
    expect(correctedResult).toBe('12 de septiembre de 2026')
    expect(correctedResult).not.toBe(legacyFormatted)
  })

  it('Accepts additional Intl.DateTimeFormatOptions without losing calendar date fidelity', () => {
    const input = '2026-09-12'
    const shortResult = formatDate(input, { month: 'short' })

    // e.g. "12 de sept de 2026" or "12 sept 2026"
    expect(shortResult).toContain('12')
    expect(shortResult).toContain('2026')
  })
})
