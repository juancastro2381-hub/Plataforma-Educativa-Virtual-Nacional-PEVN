/**
 * PEVN Design System — Loading Spinner Component
 *
 * Accessible loading indicator with ARIA live region support.
 *
 * Accessibility:
 *   - Uses role="status" to announce loading state to screen readers
 *   - Provides visually hidden text for screen reader context
 *   - Animation respects prefers-reduced-motion media query (via Tailwind)
 */

import { cn } from '@utils/index'

interface LoadingSpinnerProps {
  /** Size of the spinner */
  size?: 'sm' | 'md' | 'lg' | 'xl'
  /** Message announced to screen readers */
  label?: string
  /** Additional CSS classes */
  className?: string
  /** Color variant */
  color?: 'blue' | 'white' | 'gold' | 'current'
}

const SIZE_CLASSES = {
  sm: 'h-5 w-5',
  md: 'h-8 w-8',
  lg: 'h-12 w-12',
  xl: 'h-16 w-16',
}

const COLOR_CLASSES = {
  blue: 'text-pevn-blue',
  white: 'text-white',
  gold: 'text-pevn-gold',
  current: 'text-current',
}

export function LoadingSpinner({
  size = 'md',
  label = 'Cargando...',
  className,
  color = 'blue',
}: LoadingSpinnerProps) {
  return (
    <div
      role="status"
      aria-label={label}
      aria-live="polite"
      className={cn('flex items-center justify-center', className)}
    >
      <svg
        className={cn('animate-spin', SIZE_CLASSES[size], COLOR_CLASSES[color])}
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <circle
          className="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="4"
        />
        <path
          className="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
        />
      </svg>
      {/* Visually hidden text for screen readers */}
      <span className="sr-only">{label}</span>
    </div>
  )
}

/**
 * Full-page loading overlay.
 * Used during initial application load or page transitions.
 */
export function PageLoader({ label = 'Cargando...' }: { label?: string }) {
  return (
    <div
      className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-pevn-white"
      aria-label={label}
      role="status"
    >
      <div className="flex flex-col items-center gap-4">
        {/* PEVN Logo placeholder */}
        <div className="text-4xl font-bold text-pevn-blue tracking-tight">PEVN</div>
        <LoadingSpinner size="lg" label={label} color="blue" />
        <p className="text-sm text-gray-500 animate-pulse-soft">{label}</p>
      </div>
    </div>
  )
}

export default LoadingSpinner
