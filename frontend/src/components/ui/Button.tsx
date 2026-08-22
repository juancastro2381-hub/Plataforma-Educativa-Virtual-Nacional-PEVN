/**
 * PEVN Design System — Button Component
 *
 * Accessible, themeable button with PEVN brand variants.
 *
 * Accessibility:
 *   - Minimum 44px touch target (WCAG 2.5.8)
 *   - Visible focus ring
 *   - Loading state communicates to screen readers via aria-busy
 *   - Disabled state uses aria-disabled
 *   - Color contrast meets WCAG AA (4.5:1 minimum)
 */

import type { ButtonHTMLAttributes, ReactNode } from 'react'
import { cn } from '@utils/index'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type ButtonVariant = 'primary' | 'secondary' | 'danger' | 'ghost' | 'link'
export type ButtonSize = 'sm' | 'md' | 'lg'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** Visual style variant */
  variant?: ButtonVariant
  /** Size of the button */
  size?: ButtonSize
  /** Show loading spinner and disable interactions */
  isLoading?: boolean
  /** Content rendered before the button label */
  leftIcon?: ReactNode
  /** Content rendered after the button label */
  rightIcon?: ReactNode
  /** Expand to full container width */
  fullWidth?: boolean
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const BASE_STYLES =
  'inline-flex items-center justify-center gap-2 font-semibold rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 select-none min-h-touch min-w-touch'

const VARIANT_STYLES: Record<ButtonVariant, string> = {
  primary:
    'bg-pevn-blue text-white hover:bg-pevn-blue-800 active:bg-pevn-blue-900 focus:ring-pevn-blue disabled:bg-pevn-blue-200',
  secondary:
    'border-2 border-pevn-blue text-pevn-blue bg-transparent hover:bg-pevn-blue-50 active:bg-pevn-blue-100 focus:ring-pevn-blue disabled:border-gray-300 disabled:text-gray-400',
  danger:
    'bg-pevn-red text-white hover:bg-pevn-red-700 active:bg-pevn-red-800 focus:ring-pevn-red disabled:bg-pevn-red-200',
  ghost:
    'text-pevn-blue bg-transparent hover:bg-pevn-blue-50 active:bg-pevn-blue-100 focus:ring-pevn-blue disabled:text-gray-400',
  link: 'text-pevn-blue underline underline-offset-2 hover:text-pevn-blue-800 focus:ring-pevn-blue disabled:text-gray-400 min-h-0 min-w-0 p-0',
}

const SIZE_STYLES: Record<ButtonSize, string> = {
  sm: 'px-4 py-2 text-sm',
  md: 'px-6 py-3 text-base',
  lg: 'px-8 py-4 text-lg',
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function Button({
  variant = 'primary',
  size = 'md',
  isLoading = false,
  leftIcon,
  rightIcon,
  fullWidth = false,
  disabled,
  children,
  className,
  ...props
}: ButtonProps) {
  const isDisabled = disabled ?? isLoading

  return (
    <button
      {...props}
      disabled={isDisabled}
      aria-busy={isLoading}
      aria-disabled={isDisabled}
      className={cn(
        BASE_STYLES,
        VARIANT_STYLES[variant],
        variant !== 'link' ? SIZE_STYLES[size] : undefined,
        fullWidth ? 'w-full' : undefined,
        isDisabled ? 'cursor-not-allowed opacity-60' : 'cursor-pointer',
        className
      )}
    >
      {isLoading ? (
        <>
          <LoadingSpinner size="sm" color="current" aria-hidden="true" />
          <span>Cargando...</span>
        </>
      ) : (
        <>
          {leftIcon && <span aria-hidden="true">{leftIcon}</span>}
          {children}
          {rightIcon && <span aria-hidden="true">{rightIcon}</span>}
        </>
      )}
    </button>
  )
}

// Inline loading spinner (avoids circular import)
function LoadingSpinner({
  size = 'md',
  color = 'current',
  'aria-hidden': ariaHidden,
}: {
  size?: 'sm' | 'md' | 'lg'
  color?: string
  'aria-hidden'?: boolean | 'true' | 'false'
}) {
  const sizeClass = { sm: 'h-4 w-4', md: 'h-6 w-6', lg: 'h-8 w-8' }[size]
  const colorClass = color === 'current' ? 'text-current' : `text-${color}`
  return (
    <svg
      className={cn('animate-spin', sizeClass, colorClass)}
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      aria-hidden={ariaHidden}
    >
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
      />
    </svg>
  )
}

export default Button
