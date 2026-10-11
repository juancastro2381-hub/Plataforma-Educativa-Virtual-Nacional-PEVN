import { describe, it, expect, beforeEach } from 'vitest'
import { resolveInvitationUrl } from '../utils'

describe('NTA-10-R6: resolveInvitationUrl Architecture', () => {
  beforeEach(() => {
    // Ensure window.location.origin is stable
    Object.defineProperty(window, 'location', {
      value: {
        origin: 'http://localhost:3000',
      },
      writable: true,
    })
  })

  it('preserves an already-absolute backend URL with exactly one origin', () => {
    const backendUrl = 'http://localhost:3000/auth/accept-invitation?token=sec_token_12345'
    const resolved = resolveInvitationUrl(backendUrl, 'sec_token_12345')

    expect(resolved).toBe('http://localhost:3000/auth/accept-invitation?token=sec_token_12345')
    expect(resolved).not.toContain('http://localhost:3000http://localhost:3000')
  })

  it('preserves an already-absolute HTTPS staging/production URL without double-prefixing', () => {
    const prodUrl = 'https://pevn.mineducacion.gov.co/auth/accept-invitation?token=prod_token_999'
    const resolved = resolveInvitationUrl(prodUrl, 'prod_token_999')

    expect(resolved).toBe('https://pevn.mineducacion.gov.co/auth/accept-invitation?token=prod_token_999')
    expect(resolved).not.toContain('http://localhost:3000')
  })

  it('prepends window.location.origin once when backend provides a relative path', () => {
    const relativeUrl = '/auth/accept-invitation?token=rel_token_777'
    const resolved = resolveInvitationUrl(relativeUrl, 'rel_token_777')

    expect(resolved).toBe('http://localhost:3000/auth/accept-invitation?token=rel_token_777')
  })

  it('constructs canonical URL with origin when only rawToken is supplied', () => {
    const resolved = resolveInvitationUrl(null, 'raw_only_token_444')

    expect(resolved).toBe('http://localhost:3000/auth/accept-invitation?token=raw_only_token_444')
  })

  it('properly encodes special characters in raw token parameter', () => {
    const specialToken = 'tok+abc/123==?&#'
    const resolved = resolveInvitationUrl(null, specialToken)

    expect(resolved).toBe(
      `http://localhost:3000/auth/accept-invitation?token=${encodeURIComponent(specialToken)}`
    )
  })

  it('defensively repairs an accidentally duplicated origin', () => {
    const corrupted =
      'http://localhost:3000http://localhost:3000/auth/accept-invitation?token=corrupted_token_555'
    const resolved = resolveInvitationUrl(corrupted, 'corrupted_token_555')

    expect(resolved).toBe('http://localhost:3000/auth/accept-invitation?token=corrupted_token_555')
    expect(resolved).not.toContain('http://localhost:3000http://localhost:3000')
  })

  it('returns null when neither invitationUrl nor rawToken is available', () => {
    expect(resolveInvitationUrl(null, null)).toBeNull()
    expect(resolveInvitationUrl('', '')).toBeNull()
    expect(resolveInvitationUrl(undefined, undefined)).toBeNull()
  })

  it('trims extraneous whitespace from URL and token inputs', () => {
    const padded = '   http://localhost:3000/auth/accept-invitation?token=padded_tok   '
    expect(resolveInvitationUrl(padded)).toBe(
      'http://localhost:3000/auth/accept-invitation?token=padded_tok'
    )
  })
})
