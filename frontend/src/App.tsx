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
import { InstitutionsView } from '@/pages/admin/InstitutionsView'
import { AcceptInvitation } from '@/pages/auth/AcceptInvitation'
import { GuardianActivationView } from '@/pages/auth/GuardianActivationView'
import { ForgotPassword } from '@/pages/auth/ForgotPassword'
import { ResetPassword } from '@/pages/auth/ResetPassword'
import { TerritorialAnalyticsView } from '@/pages/analytics/TerritorialAnalyticsView'
import { TeacherPortal } from '@/pages/teacher/TeacherPortal'
import { StudentPortal } from '@/pages/student/StudentPortal'
import { GuardianPortal } from '@/pages/guardian/GuardianPortal'
import { AuthProvider } from '@/context/AuthContext'
import { RequireAuth } from '@/components/auth/RequireAuth'

/**
 * Application router.
 *
 * Route tree:
 *   /                     → RootLayout
 *     /                   → ComingSoon (Landing)
 *     /login              → Login (Authentication)
 *     /auth/forgot-password → ForgotPassword (Password Recovery Request)
 *     /auth/reset-password → ResetPassword (Password Reset Execution)
 *     /auth/accept-invitation → AcceptInvitation (Public Rector Onboarding)
 *     /guardian/activate  → GuardianActivationView (Public Guardian Self-Activation)
 *     /dashboard          → Dashboard (Protected by RequireAuth)
 *     /admin/institutions → InstitutionsView (Protected by RequireAuth)
 *     /academic           → AcademicHub (Protected by RequireAuth)
 *     /teacher            → TeacherPortal (Protected by RequireAuth)
 *     /student            → StudentPortal (Protected by RequireAuth)
 *     /guardian           → GuardianPortal (Protected by RequireAuth)
 *     /virtual-classrooms → VirtualClassroomsView (Protected by RequireAuth)
 *     /analytics/territorial → TerritorialAnalyticsView (Protected by RequireAuth)
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
        path: 'auth/forgot-password',
        element: <ForgotPassword />,
      },
      {
        path: 'auth/reset-password',
        element: <ResetPassword />,
      },
      {
        path: 'auth/accept-invitation',
        element: <AcceptInvitation />,
      },
      {
        path: 'guardian/activate',
        element: <GuardianActivationView />,
      },
      {
        path: 'auth/guardian-activation',
        element: <GuardianActivationView />,
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
        path: 'admin/institutions',
        element: (
          <RequireAuth roles={['superadmin', 'national_admin']}>
            <InstitutionsView />
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
        path: 'teacher',
        element: (
          <RequireAuth roles={['teacher']}>
            <TeacherPortal />
          </RequireAuth>
        ),
      },
      {
        path: 'student',
        element: (
          <RequireAuth roles={['student']}>
            <StudentPortal />
          </RequireAuth>
        ),
      },
      {
        path: 'student/*',
        element: (
          <RequireAuth roles={['student']}>
            <StudentPortal />
          </RequireAuth>
        ),
      },
      {
        path: 'guardian',
        element: (
          <RequireAuth roles={['guardian']}>
            <GuardianPortal />
          </RequireAuth>
        ),
      },
      {
        path: 'guardian/*',
        element: (
          <RequireAuth roles={['guardian']}>
            <GuardianPortal />
          </RequireAuth>
        ),
      },
      {
        path: 'virtual-classrooms',
        element: (
          <RequireAuth permissions={['virtual_classrooms:read']}>
            <VirtualClassroomsView />
          </RequireAuth>
        ),
      },
      {
        path: 'analytics/territorial',
        element: (
          <RequireAuth permissions={['institutions:read']}>
            <TerritorialAnalyticsView />
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
