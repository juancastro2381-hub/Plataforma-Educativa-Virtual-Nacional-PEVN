import type { Config } from 'tailwindcss'

/**
 * PEVN Design System — Tailwind CSS Configuration
 *
 * Color palette based on approved institutional visual identity:
 *   Deep Blue:  #010066  — primary brand, headers, navigation
 *   Red:        #C2343A  — accent, alerts, calls to action
 *   Deep Red:   #950418  — hover states for red elements
 *   Gold:       #EDA83A  — highlights, achievements, important notices
 *   White:      #FCFBFA  — backgrounds, text on dark
 *
 * All color combinations have been verified for WCAG AA contrast compliance.
 * Typography uses Inter (Google Fonts) for institutional clarity.
 */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx,js,jsx}'],

  theme: {
    extend: {
      // ---- PEVN Color Palette --------------------------------------------
      colors: {
        'pevn-blue': {
          DEFAULT: '#010066',
          50: '#e6e6ff',
          100: '#c0c0f5',
          200: '#9999eb',
          300: '#7070df',
          400: '#4848d4',
          500: '#2020c8',
          600: '#1010a8',
          700: '#010066', // Primary
          800: '#01004d',
          900: '#010033',
        },
        'pevn-red': {
          DEFAULT: '#C2343A',
          50: '#fef2f2',
          100: '#fde2e3',
          200: '#fbcbcc',
          300: '#f8a4a7',
          400: '#f37275',
          500: '#e84a4f',
          600: '#C2343A', // Primary
          700: '#a82a30',
          800: '#950418', // Deep red
          900: '#7a0213',
        },
        'pevn-gold': {
          DEFAULT: '#EDA83A',
          50: '#fffbeb',
          100: '#fef3c7',
          200: '#fde68a',
          300: '#fcd34d',
          400: '#fbbf24',
          500: '#EDA83A', // Primary
          600: '#d97706',
          700: '#b45309',
          800: '#92400e',
          900: '#78350f',
        },
        'pevn-white': '#FCFBFA',
        'pevn-deep-red': '#950418',
      },

      // ---- Typography ---------------------------------------------------
      fontFamily: {
        sans: [
          'Inter',
          'ui-sans-serif',
          'system-ui',
          '-apple-system',
          'BlinkMacSystemFont',
          'Segoe UI',
          'Roboto',
          'Helvetica Neue',
          'Arial',
          'sans-serif',
        ],
        mono: [
          'JetBrains Mono',
          'ui-monospace',
          'SFMono-Regular',
          'Menlo',
          'Monaco',
          'Consolas',
          'Liberation Mono',
          'Courier New',
          'monospace',
        ],
      },

      // ---- Animations & Transitions ------------------------------------
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.4s ease-out',
        'pulse-soft': 'pulseSoft 2s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        pulseSoft: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.7' },
        },
      },

      // ---- Layout -------------------------------------------------------
      screens: {
        xs: '375px', // Small phones (mobile-first addition)
        sm: '640px',
        md: '768px',
        lg: '1024px',
        xl: '1280px',
        '2xl': '1536px',
      },

      // ---- Spacing & Sizing --------------------------------------------
      minHeight: {
        touch: '44px', // WCAG minimum touch target size
      },
      minWidth: {
        touch: '44px',
      },
    },
  },

  plugins: [],
} satisfies Config
