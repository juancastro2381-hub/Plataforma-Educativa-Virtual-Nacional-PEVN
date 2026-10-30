/**
 * PEVN Design System — PevnLogo & PevnBrandText Component
 *
 * Renders the official brand wordmark "PEVN" with the authentic colors of the
 * Colombian national flag (Bandera de Colombia):
 *   - P: Amarillo (#FCD116) — 50% flag proportion (shared with E)
 *   - E: Amarillo (#FCD116) — 50% flag proportion
 *   - V: Azul (#003893 / #2563EB on dark) — 25% flag proportion
 *   - N: Rojo (#CE1126) — 25% flag proportion
 *
 * Mathematically matches the canonical 2:1:1 Colombian vexillological ratio
 * across the 4 letters of PEVN.
 *
 * Accessibility:
 *   - Exposes aria-label="PEVN" to assistive technologies
 *   - Individual letter spans are marked aria-hidden="true" to prevent screen
 *     readers from awkwardly reading individual letters or pauses.
 */

import React from 'react'

export interface PevnBrandTextProps {
  /**
   * Surface context:
   *   - 'dark' (default for dark navbars and #0F172A badges): Uses high-contrast Colombian Royal Blue for 'V'
   *   - 'light': Uses official dark navy Blue (#003893) for 'V'
   *   - 'gradient': Uses CSS background-clip with the 2:1:1 Colombian tricolor gradient
   */
  variant?: 'dark' | 'light' | 'gradient'
  /** Optional className for the outer container */
  className?: string
  /** Optional inline styles */
  style?: React.CSSProperties
  /** Letter spacing adjustment */
  letterSpacing?: string
  /** Font weight */
  fontWeight?: number | string
}

export const COLOMBIA_FLAG_COLORS = {
  yellow: '#FCD116',
  blueDarkSurface: '#2563EB', // High-contrast Colombian royal blue on dark (#0F172A, #0A192F)
  blueLightSurface: '#003893', // Canonical MEN / National flag Pantone Reflex Blue
  red: '#CE1126', // Canonical Colombian flag red
} as const

/**
 * Renders the word "PEVN" with Colombian flag colors.
 */
export function PevnBrandText({
  variant = 'dark',
  className = '',
  style = {},
  letterSpacing = '0.05em',
  fontWeight = 800,
}: PevnBrandTextProps) {
  const blueColor =
    variant === 'light'
      ? COLOMBIA_FLAG_COLORS.blueLightSurface
      : COLOMBIA_FLAG_COLORS.blueDarkSurface

  if (variant === 'gradient') {
    return (
      <span
        role="img"
        aria-label="PEVN"
        className={`pevn-flag-gradient-text ${className}`}
        style={{
          fontWeight,
          letterSpacing,
          background: `linear-gradient(to right, ${COLOMBIA_FLAG_COLORS.yellow} 0%, ${COLOMBIA_FLAG_COLORS.yellow} 50%, ${COLOMBIA_FLAG_COLORS.blueDarkSurface} 50%, ${COLOMBIA_FLAG_COLORS.blueDarkSurface} 75%, ${COLOMBIA_FLAG_COLORS.red} 75%, ${COLOMBIA_FLAG_COLORS.red} 100%)`,
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          display: 'inline-block',
          ...style,
        }}
      >
        PEVN
      </span>
    )
  }

  const yellowStyle: React.CSSProperties =
    variant === 'light'
      ? {
          color: COLOMBIA_FLAG_COLORS.yellow,
          textShadow: '0 1px 2px rgba(0, 0, 0, 0.2)',
          filter: 'drop-shadow(0 0.5px 0.5px rgba(180, 83, 9, 0.4))',
        }
      : { color: COLOMBIA_FLAG_COLORS.yellow }

  return (
    <span
      role="img"
      aria-label="PEVN"
      className={`pevn-brand-text ${className}`}
      style={{
        fontWeight,
        letterSpacing,
        display: 'inline-flex',
        alignItems: 'baseline',
        ...style,
      }}
    >
      <span aria-hidden="true" style={yellowStyle}>
        P
      </span>
      <span aria-hidden="true" style={yellowStyle}>
        E
      </span>
      <span aria-hidden="true" style={{ color: blueColor }}>
        V
      </span>
      <span aria-hidden="true" style={{ color: COLOMBIA_FLAG_COLORS.red }}>
        N
      </span>
    </span>
  )
}

export interface PevnLogoBadgeProps {
  /** Size in pixels (width & height), defaults to 56 when width/height are not set */
  size?: number
  /** Optional width override (number in pixels or CSS string) */
  width?: number | string
  /** Optional height override (number in pixels or CSS string) */
  height?: number | string
  /** Border radius in pixels, defaults to 14 */
  borderRadius?: number | string
  /** Background color of the container, defaults to '#0F172A' */
  backgroundColor?: string
  /** Optional border styling */
  border?: string
  /** Optional box shadow */
  boxShadow?: string
  /** Text font size, defaults to 1.25rem */
  fontSize?: string
  /** Surface variant for blue contrast ('dark' | 'light'), defaults to 'dark' */
  variant?: 'dark' | 'light'
  /** Optional additional className */
  className?: string
  /** Optional inline styles */
  style?: React.CSSProperties
  /** Show top Colombian flag micro-accent stripe on the badge */
  withAccentStripe?: boolean
}

/**
 * Renders the iconic PEVN rounded container badge with Colombian flag typography.
 */
export function PevnLogoBadge({
  size = 56,
  width,
  height,
  borderRadius = '14px',
  backgroundColor = '#0F172A',
  border = '1px solid rgba(255, 255, 255, 0.1)',
  boxShadow = '0 4px 12px rgba(15, 23, 42, 0.25)',
  fontSize = '1.25rem',
  variant = 'dark',
  className = '',
  style = {},
  withAccentStripe = false,
}: PevnLogoBadgeProps) {
  const badgeWidth =
    width !== undefined ? (typeof width === 'number' ? `${width}px` : width) : `${size}px`
  const badgeHeight =
    height !== undefined ? (typeof height === 'number' ? `${height}px` : height) : `${size}px`

  return (
    <div
      className={`pevn-logo-badge ${className}`}
      style={{
        display: 'inline-flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        width: badgeWidth,
        height: badgeHeight,
        borderRadius,
        backgroundColor,
        border,
        boxShadow,
        overflow: 'hidden',
        position: 'relative',
        userSelect: 'none',
        ...style,
      }}
    >
      {withAccentStripe && (
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: '3px',
            display: 'flex',
          }}
          aria-hidden="true"
        >
          <div style={{ flex: 2, backgroundColor: COLOMBIA_FLAG_COLORS.yellow }} />
          <div style={{ flex: 1, backgroundColor: COLOMBIA_FLAG_COLORS.blueLightSurface }} />
          <div style={{ flex: 1, backgroundColor: COLOMBIA_FLAG_COLORS.red }} />
        </div>
      )}
      <span style={{ fontSize, lineHeight: 1 }}>
        <PevnBrandText variant={variant} fontWeight={800} />
      </span>
    </div>
  )
}

export default PevnBrandText
