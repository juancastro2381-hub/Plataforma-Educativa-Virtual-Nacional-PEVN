/**
 * PEVN Frontend — Application Root
 *
 * Defines the client-side routing structure using React Router v6.
 * All routes go through RootLayout which provides the consistent shell.
 */

import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import { ErrorBoundary } from '@components/ErrorBoundary'
import { RootLayout } from '@/layouts/RootLayout'
import { ComingSoon } from '@pages/ComingSoon'
import { NotFound } from '@pages/NotFound'

/**
 * Application router.
 *
 * Route structure:
 *   / → RootLayout
 *     /       → ComingSoon (Phase 1 landing)
 *     /*      → NotFound
 *
 * Future routes (Phase 2+):
 *   /login          → Login page
 *   /dashboard      → Authenticated dashboard
 *   /institutions/* → Institutional management
 */
const router = createBrowserRouter([
  {
    path: '/',
    element: <RootLayout />,
    errorElement: <ErrorBoundary />,
    children: [
      {
        index: true,
        element: <ComingSoon />,
      },
      {
        path: '*',
        element: <NotFound />,
      },
    ],
  },
])

/**
 * Root application component.
 * Wrapped in ErrorBoundary at the very top level.
 */
export function App() {
  return (
    <ErrorBoundary>
      <RouterProvider router={router} />
    </ErrorBoundary>
  )
}

export default App
