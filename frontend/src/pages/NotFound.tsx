/**
 * PEVN Frontend — 404 Not Found Page
 *
 * Displayed when the user navigates to a route that does not exist.
 *
 * Accessibility:
 *   - h1 clearly states the page was not found
 *   - Navigation back to home is prominently available
 *   - No confusing technical details
 */

import { Link } from 'react-router-dom'

export function NotFound() {
  return (
    <div className="flex-1 flex items-center justify-center p-6 animate-fade-in" role="main">
      <div className="max-w-md w-full text-center">
        {/* Error code — decorative */}
        <p className="text-8xl font-black text-pevn-blue/10 mb-4 select-none" aria-hidden="true">
          404
        </p>

        {/* Main message */}
        <h1 className="text-3xl font-bold text-pevn-blue mb-3">Página no encontrada</h1>

        <p className="text-gray-600 mb-8 leading-relaxed">
          La página que buscas no existe o ha sido movida. Verifique la dirección e intente de
          nuevo.
        </p>

        {/* Action */}
        <Link
          to="/"
          className="inline-flex items-center gap-2 px-6 py-3 bg-pevn-blue text-white font-semibold rounded-lg hover:bg-pevn-blue-800 focus:outline-none focus:ring-2 focus:ring-pevn-blue focus:ring-offset-2 transition-colors min-h-touch"
          aria-label="Ir a la página principal"
        >
          <svg
            className="w-4 h-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
            aria-hidden="true"
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Ir al inicio
        </Link>
      </div>
    </div>
  )
}

export default NotFound
