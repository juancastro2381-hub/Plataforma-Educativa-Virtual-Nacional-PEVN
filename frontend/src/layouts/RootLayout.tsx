/**
 * PEVN Frontend — Root Layout
 *
 * The base layout shell for all application pages.
 * Integrates institutional header branding, auth navigation state,
 * and responsive container layout.
 */

import { Suspense } from 'react'
import { Link, Outlet } from 'react-router-dom'
import { PageLoader } from '@components/ui/LoadingSpinner'
import { useAuth } from '@/hooks/useAuth'
import config from '@config/index'

export function RootLayout() {
  const { user, isAuthenticated, logout, hasPermission } = useAuth()

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', backgroundColor: '#F8FAFC' }}>
      {/* Colombian Flag Bar */}
      <div style={{ height: '4px', width: '100%', display: 'flex' }}>
        <div style={{ flex: 2, backgroundColor: '#FCD116' }} />
        <div style={{ flex: 1, backgroundColor: '#003893' }} />
        <div style={{ flex: 1, backgroundColor: '#CE1126' }} />
      </div>

      {/* Accessible page header */}
      <header
        style={{
          backgroundColor: '#0F172A',
          color: '#FFFFFF',
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
        }}
        role="banner"
        aria-label="Encabezado de la aplicación"
      >
        <div
          style={{
            maxWidth: '1280px',
            margin: '0 auto',
            padding: '0 1rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            height: '64px',
          }}
        >
          {/* Brand */}
          <Link
            to="/"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.75rem',
              textDecoration: 'none',
              color: '#FFFFFF',
            }}
          >
            <span
              style={{
                fontSize: '1.25rem',
                fontWeight: 800,
                letterSpacing: '0.05em',
                backgroundColor: 'rgba(255,255,255,0.1)',
                padding: '0.25rem 0.5rem',
                borderRadius: '6px',
              }}
              aria-label="PEVN"
            >
              PEVN
            </span>
            <span
              style={{
                fontSize: '0.875rem',
                fontWeight: 600,
                color: '#FCD116',
                borderLeft: '1px solid #334155',
                paddingLeft: '0.75rem',
              }}
            >
              {config.appName}
            </span>
          </Link>

          {/* Navigation */}
          <nav aria-label="Navegación principal">
            {isAuthenticated && user ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                {(user.roles.includes('rector') || user.roles.includes('institution_admin') || user.roles.includes('superadmin') || user.roles.includes('coordinator') || user.roles.includes('academic_coordinator')) && (
                  <Link
                    to="/academic"
                    style={{
                      color: '#FCD116',
                      textDecoration: 'none',
                      fontSize: '0.875rem',
                      fontWeight: 600,
                    }}
                  >
                    Gestión Académica
                  </Link>
                )}
                {user.roles.includes('teacher') && (
                  <Link
                    to="/teacher"
                    style={{
                      color: '#67E8F9',
                      textDecoration: 'none',
                      fontSize: '0.875rem',
                      fontWeight: 600,
                    }}
                  >
                    Portal Docente
                  </Link>
                )}
                {user.roles.includes('student') && (
                  <Link
                    to="/student"
                    style={{
                      color: '#93C5FD',
                      textDecoration: 'none',
                      fontSize: '0.875rem',
                      fontWeight: 600,
                    }}
                  >
                    Portal Estudiante
                  </Link>
                )}
                {user.roles.includes('guardian') && (
                  <Link
                    to="/guardian"
                    style={{
                      color: '#F472B6',
                      textDecoration: 'none',
                      fontSize: '0.875rem',
                      fontWeight: 600,
                    }}
                  >
                    Portal Acudiente
                  </Link>
                )}
                {(user.scope.is_national || user.roles.includes('national_admin') || user.roles.includes('superadmin')) && (
                  <Link
                    to="/admin/institutions"
                    style={{
                      color: '#4ADE80',
                      textDecoration: 'none',
                      fontSize: '0.875rem',
                      fontWeight: 600,
                    }}
                  >
                    Instituciones
                  </Link>
                )}
                {hasPermission('institutions:read') && (
                  <Link
                    to="/analytics/territorial"
                    style={{
                      color: '#A78BFA',
                      textDecoration: 'none',
                      fontSize: '0.875rem',
                      fontWeight: 600,
                    }}
                  >
                    Analítica Territorial
                  </Link>
                )}
                {hasPermission('virtual_classrooms:read') && (
                  <Link
                    to="/virtual-classrooms"
                    style={{
                      color: '#38BDF8',
                      textDecoration: 'none',
                      fontSize: '0.875rem',
                      fontWeight: 600,
                    }}
                  >
                    Aulas Virtuales
                  </Link>
                )}
                <Link
                  to="/dashboard"
                  style={{
                    color: '#F8FAFC',
                    textDecoration: 'none',
                    fontSize: '0.875rem',
                    fontWeight: 600,
                  }}
                >
                  Panel ({user.username})
                </Link>
                <button
                  onClick={() => void logout()}
                  style={{
                    backgroundColor: 'rgba(239, 68, 68, 0.2)',
                    color: '#FCA5A5',
                    border: '1px solid rgba(239, 68, 68, 0.4)',
                    padding: '0.35rem 0.75rem',
                    borderRadius: '6px',
                    fontSize: '0.8125rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                  }}
                >
                  Salir
                </button>
              </div>
            ) : (
              <Link
                to="/login"
                style={{
                  backgroundColor: '#2563EB',
                  color: '#FFFFFF',
                  padding: '0.45rem 1rem',
                  borderRadius: '6px',
                  textDecoration: 'none',
                  fontSize: '0.875rem',
                  fontWeight: 600,
                }}
              >
                Iniciar Sesión
              </Link>
            )}
          </nav>
        </div>
      </header>

      {/* Main content area */}
      <main
        id="main-content"
        style={{ flex: 1, display: 'flex', flexDirection: 'column' }}
        role="main"
        tabIndex={-1}
      >
        <Suspense fallback={<PageLoader />}>
          <Outlet />
        </Suspense>
      </main>

      {/* Footer */}
      <footer
        style={{
          backgroundColor: '#0F172A',
          color: '#94A3B8',
          padding: '1.5rem 0',
          borderTop: '1px solid #1E293B',
        }}
        role="contentinfo"
        aria-label="Pie de página"
      >
        <div
          style={{
            maxWidth: '1280px',
            margin: '0 auto',
            padding: '0 1rem',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            fontSize: '0.8125rem',
            flexWrap: 'wrap',
            gap: '0.5rem',
          }}
        >
          <p style={{ margin: 0 }}>
            © {String(new Date().getFullYear())} Plataforma Educativa Virtual Nacional. República de Colombia.
          </p>
          <p style={{ margin: 0 }}>v{config.version}</p>
        </div>
      </footer>
    </div>
  )
}

export default RootLayout
