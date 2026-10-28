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
import { PevnBrandText } from '@components/ui/PevnLogo'
import { useAuth } from '@/hooks/useAuth'
import config from '@config/index'

export function RootLayout() {
  const {
    user,
    isAuthenticated,
    logout,
    hasPermission,
    hasRole,
    activeInstitutionId,
    activeInstitutionName,
    setActiveInstitutionContext,
  } = useAuth()

  const isSuperAdmin = hasRole(['superadmin', 'super_admin'])

  const isInstitutionalDirective = hasRole([
    'rector',
    'institution_admin',
    'coordinator',
    'academic_coordinator',
  ])
  const canAccessInstitutions =
    !isSuperAdmin && (
      hasPermission('institutions:read') ||
      hasRole('national_admin') ||
      Boolean(user?.scope.is_national)
    )

  const canAccessUsers =
    !isSuperAdmin && (
      hasPermission('users:read') ||
      hasRole('national_admin')
    )

  const canAccessAcademic = !isSuperAdmin && isInstitutionalDirective

  const canAccessVirtualClassrooms =
    !isSuperAdmin && hasPermission('virtual_classrooms:read')

  const canAccessCommunications =
    !isSuperAdmin && hasPermission('communications:read')

  const canAccessNews =
    !isSuperAdmin && hasPermission('news:read')

  const canAccessIncidents =
    !isSuperAdmin && hasPermission('incidents:read')

  const canAccessTerritorial =
    !isSuperAdmin && hasRole(['national_admin', 'department_admin', 'municipality_admin'])

  const canAccessControlCenter =
    !isSuperAdmin && hasRole(['national_admin', 'department_admin'])

  const canAccessOnboarding =
    !isSuperAdmin && hasRole(['national_admin', 'department_admin'])

  const canAccessDepartmentAdmins =
    !isSuperAdmin && hasRole('national_admin')

  const canAccessMunicipalityAdmins =
    !isSuperAdmin && hasRole(['national_admin', 'department_admin'])

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
            maxWidth: '1360px',
            margin: '0 auto',
            padding: '0.625rem 1rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '0.75rem',
            minHeight: '64px',
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
                backgroundColor: 'rgba(255,255,255,0.08)',
                border: '1px solid rgba(255, 255, 255, 0.15)',
                padding: '0.25rem 0.6rem',
                borderRadius: '8px',
                display: 'inline-flex',
                alignItems: 'center',
                boxShadow: '0 2px 4px rgba(0,0,0,0.25)',
              }}
              aria-label="PEVN"
            >
              <PevnBrandText variant="dark" />
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
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
                {/* CONSOLA DE OPERACIONES TÉCNICAS (SUPER_ADMIN L100 EXCLUSIVO) */}
                {isSuperAdmin && (
                  <>
                    <Link
                      to="/dashboard"
                      style={{
                        color: '#FCD116',
                        textDecoration: 'none',
                        fontSize: '0.8125rem',
                        fontWeight: 700,
                        padding: '0.25rem 0.4rem',
                      }}
                      title="Centro de Operaciones y Gobernanza L100"
                    >
                      ⚙️ Operaciones
                    </Link>
                    <Link
                      to="/operations/health"
                      style={{
                        color: '#4ADE80',
                        textDecoration: 'none',
                        fontSize: '0.8125rem',
                        fontWeight: 600,
                        padding: '0.25rem 0.4rem',
                      }}
                      title="Salud de Infraestructura y Conectividad"
                    >
                      Salud Plataforma
                    </Link>
                    <Link
                      to="/operations/support"
                      style={{
                        color: '#38BDF8',
                        textDecoration: 'none',
                        fontSize: '0.8125rem',
                        fontWeight: 600,
                        padding: '0.25rem 0.4rem',
                      }}
                      title="Mesa de Ayuda Técnica e Incidentes"
                    >
                      Soporte Técnico
                    </Link>
                    <Link
                      to="/operations/audit"
                      style={{
                        color: '#F87171',
                        textDecoration: 'none',
                        fontSize: '0.8125rem',
                        fontWeight: 600,
                        padding: '0.25rem 0.4rem',
                      }}
                      title="Auditoría de Seguridad y Accesos"
                    >
                      Seguridad & Auditoría
                    </Link>
                    <Link
                      to="/admin/users"
                      style={{
                        color: '#2DD4BF',
                        textDecoration: 'none',
                        fontSize: '0.8125rem',
                        fontWeight: 600,
                        padding: '0.25rem 0.4rem',
                      }}
                      title="Directorio Global de Usuarios"
                    >
                      Usuarios
                    </Link>
                    <Link
                      to="/operations/tenant-diagnostics"
                      style={{
                        color: '#FBBF24',
                        textDecoration: 'none',
                        fontSize: '0.8125rem',
                        fontWeight: 600,
                        padding: '0.25rem 0.4rem',
                      }}
                      title="Diagnóstico Operacional de Inquilinos"
                    >
                      Diagnóstico Inquilinos
                    </Link>
                  </>
                )}

                {/* GESTIÓN EDUCATIVA Y TERRITORIAL (ROLES NACIONAL, TERRITORIAL Y DIRECTIVO) */}
                {canAccessInstitutions && (
                  <Link
                    to="/admin/institutions"
                    style={{
                      color: '#4ADE80',
                      textDecoration: 'none',
                      fontSize: '0.8125rem',
                      fontWeight: 600,
                      padding: '0.25rem 0.4rem',
                    }}
                    title={
                      hasRole('rector')
                        ? 'Mi Institución Educativa'
                        : 'Catálogo de Instituciones Educativas'
                    }
                  >
                    {hasRole('rector') ? '🏛️ Mi Institución' : 'Instituciones'}
                  </Link>
                )}
                {canAccessUsers && (
                  <Link
                    to="/admin/users"
                    style={{
                      color: '#2DD4BF',
                      textDecoration: 'none',
                      fontSize: '0.8125rem',
                      fontWeight: 600,
                      padding: '0.25rem 0.4rem',
                    }}
                    title="Usuarios del Sistema"
                  >
                    Usuarios
                  </Link>
                )}
                {canAccessDepartmentAdmins && (
                  <Link
                    to="/admin/department-admins"
                    style={{
                      color: '#FBBF24',
                      textDecoration: 'none',
                      fontSize: '0.8125rem',
                      fontWeight: 600,
                      padding: '0.25rem 0.4rem',
                    }}
                    title="Gestión de Administradores Departamentales"
                  >
                    Admin Dptal.
                  </Link>
                )}
                {canAccessMunicipalityAdmins && (
                  <Link
                    to="/admin/municipality-admins"
                    style={{
                      color: '#34D399',
                      textDecoration: 'none',
                      fontSize: '0.8125rem',
                      fontWeight: 600,
                      padding: '0.25rem 0.4rem',
                    }}
                    title="Gestión de Administradores Municipales (NTA-09)"
                  >
                    Admin Mpal.
                  </Link>
                )}
                {canAccessControlCenter && (
                  <Link
                    to="/admin/control-center"
                    style={{
                      color: '#38BDF8',
                      textDecoration: 'none',
                      fontSize: '0.8125rem',
                      fontWeight: 600,
                      padding: '0.25rem 0.4rem',
                    }}
                    title="Centro de Control Territorial (NTA-05)"
                  >
                    Control Territorial
                  </Link>
                )}
                {canAccessOnboarding && (
                  <Link
                    to="/admin/onboarding"
                    style={{
                      color: '#A5B4FC',
                      textDecoration: 'none',
                      fontSize: '0.8125rem',
                      fontWeight: 600,
                      padding: '0.25rem 0.4rem',
                    }}
                    title="Adopción y Onboarding Institucional (NTA-04)"
                  >
                    Onboarding
                  </Link>
                )}

                {/* GESTIÓN ACADÉMICA */}
                {canAccessAcademic && (
                  <Link
                    to="/academic"
                    style={{
                      color: '#FCD116',
                      textDecoration: 'none',
                      fontSize: '0.8125rem',
                      fontWeight: 600,
                      padding: '0.25rem 0.4rem',
                    }}
                    title="Gestión Curricular y Académica"
                  >
                    Académica
                  </Link>
                )}

                {/* AULAS VIRTUALES */}
                {canAccessVirtualClassrooms && (
                  <Link
                    to="/virtual-classrooms"
                    style={{
                      color: '#38BDF8',
                      textDecoration: 'none',
                      fontSize: '0.8125rem',
                      fontWeight: 600,
                      padding: '0.25rem 0.4rem',
                    }}
                    title="Aulas Virtuales y Grabaciones"
                  >
                    Aulas Virtuales
                  </Link>
                )}

                {/* COMUNICACIONES */}
                {canAccessCommunications && (
                  <Link
                    to="/communications"
                    style={{
                      color: '#818CF8',
                      textDecoration: 'none',
                      fontSize: '0.8125rem',
                      fontWeight: 600,
                      padding: '0.25rem 0.4rem',
                    }}
                    title="Comunicaciones Oficiales"
                  >
                    Comunicaciones
                  </Link>
                )}
                {canAccessNews && (
                  <Link
                    to="/news"
                    style={{
                      color: '#C084FC',
                      textDecoration: 'none',
                      fontSize: '0.8125rem',
                      fontWeight: 600,
                      padding: '0.25rem 0.4rem',
                    }}
                    title="Muro de Noticias"
                  >
                    Noticias
                  </Link>
                )}

                {/* CONVIVENCIA */}
                {canAccessIncidents && (
                  <Link
                    to="/incidents"
                    style={{
                      color: '#FB923C',
                      textDecoration: 'none',
                      fontSize: '0.8125rem',
                      fontWeight: 600,
                      padding: '0.25rem 0.4rem',
                    }}
                    title="Gestión de Convivencia e Incidentes"
                  >
                    Convivencia
                  </Link>
                )}

                {/* SUPERVISIÓN TERRITORIAL */}
                {canAccessTerritorial && (
                  <Link
                    to="/analytics/territorial"
                    style={{
                      color: '#A78BFA',
                      textDecoration: 'none',
                      fontSize: '0.8125rem',
                      fontWeight: 600,
                      padding: '0.25rem 0.4rem',
                    }}
                    title="Supervisión e Inspección Territorial"
                  >
                    Analítica Territorial
                  </Link>
                )}

                {/* Role Portals */}
                {hasRole('teacher') && (
                  <Link
                    to="/teacher"
                    style={{
                      color: '#67E8F9',
                      textDecoration: 'none',
                      fontSize: '0.8125rem',
                      fontWeight: 600,
                    }}
                  >
                    Portal Docente
                  </Link>
                )}
                {hasRole('student') && (
                  <Link
                    to="/student"
                    style={{
                      color: '#93C5FD',
                      textDecoration: 'none',
                      fontSize: '0.8125rem',
                      fontWeight: 600,
                    }}
                  >
                    Portal Estudiante
                  </Link>
                )}
                {hasRole('guardian') && (
                  <Link
                    to="/guardian"
                    style={{
                      color: '#F472B6',
                      textDecoration: 'none',
                      fontSize: '0.8125rem',
                      fontWeight: 600,
                    }}
                  >
                    Portal Acudiente
                  </Link>
                )}

                {/* Active Context Indicator */}
                {activeInstitutionId && (
                  isSuperAdmin ? (
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                        backgroundColor: 'rgba(239, 68, 68, 0.2)',
                        border: '1px solid rgba(239, 68, 68, 0.5)',
                        color: '#FECACA',
                        borderRadius: '6px',
                        padding: '0.2rem 0.6rem',
                        fontSize: '0.75rem',
                        fontWeight: 700,
                      }}
                      title={`Contexto Diagnóstico de Inquilino Activo: ${activeInstitutionName || activeInstitutionId}`}
                    >
                      <span>🔍 DIAGNÓSTICO: {activeInstitutionName ? (activeInstitutionName.length > 16 ? activeInstitutionName.slice(0, 14) + '...' : activeInstitutionName) : 'Inquilino'}</span>
                      <button
                        type="button"
                        onClick={() => setActiveInstitutionContext(null)}
                        style={{
                          backgroundColor: '#DC2626',
                          border: 'none',
                          color: '#FFFFFF',
                          cursor: 'pointer',
                          fontWeight: 700,
                          fontSize: '0.75rem',
                          padding: '0.15rem 0.5rem',
                          borderRadius: '4px',
                        }}
                        title="Salir del diagnóstico de inquilino y volver a Operaciones Globales"
                      >
                        ✕ Salir a Operaciones Globales
                      </button>
                    </div>
                  ) : (
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.4rem',
                        backgroundColor: 'rgba(252, 209, 22, 0.15)',
                        border: '1px solid rgba(252, 209, 22, 0.4)',
                        color: '#FCD116',
                        borderRadius: '6px',
                        padding: '0.2rem 0.5rem',
                        fontSize: '0.75rem',
                        fontWeight: 600,
                      }}
                      title={`Contexto institucional activo: ${activeInstitutionName || activeInstitutionId}`}
                    >
                      <span>🏛️ {activeInstitutionName ? (activeInstitutionName.length > 18 ? activeInstitutionName.slice(0, 16) + '...' : activeInstitutionName) : 'Sede Activa'}</span>
                      <button
                        type="button"
                        onClick={() => setActiveInstitutionContext(null)}
                        style={{
                          background: 'none',
                          border: 'none',
                          color: '#FCA5A5',
                          cursor: 'pointer',
                          fontWeight: 'bold',
                          fontSize: '0.8rem',
                          padding: '0 2px',
                          lineHeight: 1,
                        }}
                        title="Salir del contexto institucional"
                      >
                        ✕
                      </button>
                    </div>
                  )
                )}

                {/* Scope Badge */}
                {user.scope && (
                  <div
                    style={{
                      backgroundColor: 'rgba(255, 255, 255, 0.08)',
                      border: '1px solid rgba(255, 255, 255, 0.15)',
                      color: '#E2E8F0',
                      borderRadius: '6px',
                      padding: '0.2rem 0.45rem',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                    }}
                    title={
                      hasRole('superadmin')
                        ? 'Gobernanza Global de Plataforma (Nivel 100)'
                        : `Jurisdicción operativa: ${user.scope.is_national ? 'Nacional' : user.scope.is_department ? `Departamento ${user.scope.department_id}` : user.scope.is_municipality ? `Municipio ${user.scope.municipality_code || user.scope.jurisdiction_name || user.scope.municipality_id}` : user.scope.institution_id ? `Institucional` : 'Local'}`
                    }
                  >
                    {hasRole('superadmin')
                      ? '🌐 Global'
                      : user.scope.is_national
                      ? '🇨🇴 Nal.'
                      : user.scope.is_department
                      ? `📍 Dpto ${user.scope.department_id}`
                      : user.scope.is_municipality
                      ? `🏛️ Mun ${user.scope.municipality_code || ''}`
                      : user.scope.institution_id
                      ? `🏫 Inst`
                      : 'Local'}
                  </div>
                )}

                <Link
                  to="/dashboard"
                  style={{
                    color: isSuperAdmin ? '#FCD116' : '#F8FAFC',
                    textDecoration: 'none',
                    fontSize: '0.8125rem',
                    fontWeight: 600,
                  }}
                  title={
                    isSuperAdmin
                      ? 'Consola de Operaciones Globales (SUPER_ADMIN L100)'
                      : hasRole('national_admin')
                      ? 'Panel de Gobernanza Nacional (NATIONAL_ADMIN L90)'
                      : `Panel de control (${user.username})`
                  }
                >
                  {isSuperAdmin
                    ? `⚙️ Operaciones (${user.username})`
                    : hasRole('national_admin')
                    ? `🇨🇴 Panel Nacional (${user.username})`
                    : `Panel (${user.username})`}
                </Link>
                <button
                  onClick={() => void logout()}
                  style={{
                    backgroundColor: 'rgba(239, 68, 68, 0.2)',
                    color: '#FCA5A5',
                    border: '1px solid rgba(239, 68, 68, 0.4)',
                    padding: '0.3rem 0.65rem',
                    borderRadius: '6px',
                    fontSize: '0.75rem',
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
