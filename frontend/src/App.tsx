/**
 * PEVN Frontend — Application Root & Routing Configuration
 *
 * Configures the React Router v6 routing tree, AuthProvider context provider,
 * and top-level ErrorBoundary for disaster recovery.
 */

import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import { ErrorBoundary } from '@components/ErrorBoundary'
import { RootLayout } from '@/layouts/RootLayout'
import { ComingSoon } from '@pages/ComingSoon'
import { NotFound } from '@pages/NotFound'
import { Login } from '@/pages/Login'
import { Dashboard } from '@/pages/Dashboard'
import { AcademicHub } from '@/pages/academic/AcademicHub'
import { VirtualClassroomsView } from '@/pages/virtual-classrooms/VirtualClassroomsView'
import { AuthProvider } from '@/context/AuthContext'
import { RequireAuth } from '@/components/auth/RequireAuth'

/**
 * Application router.
 *
 * Route tree:
 *   /                     → RootLayout
 *     /                   → ComingSoon (Landing)
 *     /login              → Login (Authentication)
 *     /dashboard          → Dashboard (Protected by RequireAuth)
 *     /academic           → AcademicHub (Protected by RequireAuth)
 *     /virtual-classrooms → VirtualClassroomsView (Protected by RequireAuth)
 *     /*                  → NotFound (404)
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
        path: 'login',
        element: <Login />,
      },
      {
        path: 'dashboard',
        element: (
          <RequireAuth>
            <Dashboard />
          </RequireAuth>
        ),
      },
      {
        path: 'academic',
        element: (
          <RequireAuth>
            <AcademicHub />
          </RequireAuth>
        ),
      },
      {
        path: 'virtual-classrooms',
        element: (
          <RequireAuth>
            <VirtualClassroomsView />
          </RequireAuth>
        ),
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
 */
export function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <RouterProvider router={router} />
      </AuthProvider>
    </ErrorBoundary>
  )
}

export default App
