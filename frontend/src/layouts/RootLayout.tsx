/**
 * PEVN Frontend — Root Layout
 *
 * The base layout shell for all application pages.
 * Provides:
 *   - Skip navigation link (accessibility)
 *   - Semantic <header>, <main>, <footer> structure
 *   - Outlet for child routes (React Router)
 *   - Consistent page structure
 */

import { Suspense } from 'react'
import { Outlet } from 'react-router-dom'
import { PageLoader } from '@components/ui/LoadingSpinner'
import config from '@config/index'

export function RootLayout() {
  return (
    <div className="min-h-screen flex flex-col bg-pevn-white">
      {/* Accessible page header */}
      <header
        className="bg-pevn-blue shadow-lg"
        role="banner"
        aria-label="Encabezado de la aplicación"
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Brand */}
            <div className="flex items-center gap-3">
              <span className="text-xl font-bold text-white tracking-wide" aria-label="PEVN">
                PEVN
              </span>
              <span className="hidden sm:block text-pevn-gold text-xs font-medium border-l border-pevn-blue-400 pl-3">
                {config.appName}
              </span>
            </div>

            {/* Navigation placeholder — Phase 2+ */}
            <nav aria-label="Navegación principal">
              {/* Navigation items will be added in Phase 2 */}
            </nav>
          </div>
        </div>
      </header>

      {/* Main content area */}
      <main
        id="main-content"
        className="flex-1 flex flex-col"
        role="main"
        tabIndex={-1} // Allows programmatic focus from skip link
      >
        <Suspense fallback={<PageLoader />}>
          <Outlet />
        </Suspense>
      </main>

      {/* Footer */}
      <footer
        className="bg-pevn-blue-900 text-white py-6"
        role="contentinfo"
        aria-label="Pie de página"
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 text-sm">
            <p className="text-pevn-white/80 text-center sm:text-left">
              © {String(new Date().getFullYear())} Plataforma Educativa Virtual Nacional. Todos los
              derechos reservados.
            </p>
            <p className="text-pevn-white/60 text-xs">v{config.version}</p>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default RootLayout
