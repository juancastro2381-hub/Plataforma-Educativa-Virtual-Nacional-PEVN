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
import { OnboardingView } from '@/pages/admin/OnboardingView'
import { DepartmentAdminsView } from '@/pages/admin/DepartmentAdminsView'
import { MunicipalityAdminsView } from '@/pages/admin/MunicipalityAdminsView'
import { TerritorialControlCenterView } from '@/pages/admin/TerritorialControlCenterView'
import { AcceptInvitation } from '@/pages/auth/AcceptInvitation'
import { GuardianActivationView } from '@/pages/auth/GuardianActivationView'
import { ForgotPassword } from '@/pages/auth/ForgotPassword'
import { ResetPassword } from '@/pages/auth/ResetPassword'
import { TerritorialAnalyticsView } from '@/pages/analytics/TerritorialAnalyticsView'
import { UsersView } from '@/pages/admin/UsersView'
import { CommunicationsView } from '@/pages/communications/CommunicationsView'
import { NewsView } from '@/pages/communications/NewsView'
import { IncidentsView } from '@/pages/coexistence/IncidentsView'
import { TeacherPortal } from '@/pages/teacher/TeacherPortal'
import { StudentPortal } from '@/pages/student/StudentPortal'
import { GuardianPortal } from '@/pages/guardian/GuardianPortal'
import { PlatformHealthView } from '@/pages/operations/PlatformHealthView'
import { TechnicalSupportView } from '@/pages/operations/TechnicalSupportView'
import { SecurityAuditView } from '@/pages/operations/SecurityAuditView'
import { TenantDiagnosticsView } from '@/pages/operations/TenantDiagnosticsView'
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
        path: 'reset-password',
        element: <ResetPassword />,
      },
      {
        path: 'auth/accept-invitation',
        element: <AcceptInvitation />,
      },
      {
        path: 'invitation/accept',
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
          <RequireAuth permissions={['institutions:read']}>
            <InstitutionsView />
          </RequireAuth>
        ),
      },
      {
        path: 'admin/onboarding',
        element: (
          <RequireAuth roles={['superadmin', 'national_admin', 'department_admin']}>
            <OnboardingView />
          </RequireAuth>
        ),
      },
      {
        path: 'admin/users',
        element: (
          <RequireAuth permissions={['users:read']}>
            <UsersView />
          </RequireAuth>
        ),
      },
      {
        path: 'users',
        element: (
          <RequireAuth permissions={['users:read']}>
            <UsersView />
          </RequireAuth>
        ),
      },
      {
        path: 'admin/department-admins',
        element: (
          <RequireAuth roles={['superadmin', 'national_admin']}>
            <DepartmentAdminsView />
          </RequireAuth>
        ),
      },
      {
        path: 'admin/municipality-admins',
        element: (
          <RequireAuth roles={['superadmin', 'national_admin', 'department_admin']}>
            <MunicipalityAdminsView />
          </RequireAuth>
        ),
      },
      {
        path: 'admin/control-center',
        element: (
          <RequireAuth roles={['superadmin', 'national_admin', 'department_admin']}>
            <TerritorialControlCenterView />
          </RequireAuth>
        ),
      },
      {
        path: 'academic',
        element: (
          <RequireAuth
            roles={['rector', 'institution_admin', 'coordinator', 'academic_coordinator', 'superadmin', 'super_admin', 'national_admin', 'department_admin']}
            requireInstitutionContext
          >
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
          <RequireAuth permissions={['virtual_classrooms:read']} requireInstitutionContext>
            <VirtualClassroomsView />
          </RequireAuth>
        ),
      },
      {
        path: 'analytics/territorial',
        element: (
          <RequireAuth roles={['superadmin', 'national_admin', 'department_admin', 'municipality_admin']}>
            <TerritorialAnalyticsView />
          </RequireAuth>
        ),
      },
      {
        path: 'communications',
        element: (
          <RequireAuth permissions={['communications:read']}>
            <CommunicationsView />
          </RequireAuth>
        ),
      },
      {
        path: 'news',
        element: (
          <RequireAuth permissions={['news:read']}>
            <NewsView />
          </RequireAuth>
        ),
      },
      {
        path: 'incidents',
        element: (
          <RequireAuth permissions={['incidents:read']}>
            <IncidentsView />
          </RequireAuth>
        ),
      },
      {
        path: 'operations/health',
        element: (
          <RequireAuth roles={['superadmin', 'super_admin']}>
            <PlatformHealthView />
          </RequireAuth>
        ),
      },
      {
        path: 'operations/support',
        element: (
          <RequireAuth roles={['superadmin', 'super_admin']}>
            <TechnicalSupportView />
          </RequireAuth>
        ),
      },
      {
        path: 'operations/audit',
        element: (
          <RequireAuth roles={['superadmin', 'super_admin']}>
            <SecurityAuditView />
          </RequireAuth>
        ),
      },
      {
        path: 'operations/tenant-diagnostics',
        element: (
          <RequireAuth roles={['superadmin', 'super_admin']}>
            <TenantDiagnosticsView />
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
