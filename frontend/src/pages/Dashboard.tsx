/**
 * PEVN Frontend — Authenticated Dashboard
 *
 * Displays identity verification, institutional context, assigned RBAC roles,
 * granular permissions, and session management actions.
 */

import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { Button } from '@/components/ui/Button'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'

export const Dashboard: React.FC = () => {
  const { user, logout, changePassword, hasPermission } = useAuth()

  // Change password modal / state
  const [showPasswordModal, setShowPasswordModal] = useState(
    user?.must_change_password ?? false
  )
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [passwordError, setPasswordError] = useState<string | null>(null)
  const [passwordSuccess, setPasswordSuccess] = useState<string | null>(null)
  const [isChangingPassword, setIsChangingPassword] = useState(false)

  if (!user) {
    return null
  }

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setPasswordError(null)
    setPasswordSuccess(null)

    if (!currentPassword) {
      setPasswordError('Ingrese su contraseña actual.')
      return
    }

    if (newPassword.length < 12) {
      setPasswordError('La nueva contraseña debe tener al menos 12 caracteres.')
      return
    }

    if (newPassword !== confirmPassword) {
      setPasswordError('Las nuevas contraseñas no coinciden.')
      return
    }

    setIsChangingPassword(true)
    try {
      await changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      })
      setPasswordSuccess('¡Contraseña actualizada exitosamente!')
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
      setTimeout(() => {
        setShowPasswordModal(false)
      }, 2000)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al cambiar contraseña.'
      setPasswordError(msg)
    } finally {
      setIsChangingPassword(false)
    }
  }

  return (
    <div style={{ maxWidth: '1000px', margin: '2rem auto', padding: '0 1rem' }}>
      {/* Header Banner */}
      <div
        style={{
          backgroundColor: '#0F172A',
          color: '#FFFFFF',
          borderRadius: '16px',
          padding: '2rem',
          marginBottom: '2rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
          boxShadow: '0 10px 15px -3px rgba(15, 23, 42, 0.15)',
        }}
      >
        <div>
          <div
            style={{
              display: 'inline-block',
              fontSize: '0.75rem',
              fontWeight: 700,
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              backgroundColor: 'rgba(255, 255, 255, 0.15)',
              color: '#F8FAFC',
              padding: '0.25rem 0.75rem',
              borderRadius: '9999px',
              marginBottom: '0.5rem',
            }}
          >
            Sesión Activa • PEVN Colombia
          </div>
          <h1
            style={{
              fontSize: '1.75rem',
              fontWeight: 800,
              margin: '0.25rem 0',
              color: '#FFFFFF',
              lineHeight: 1.25,
            }}
          >
            Bienvenido, {user.full_name || user.username}
          </h1>
          <p style={{ color: '#E2E8F0', fontSize: '0.875rem', margin: 0, fontWeight: 400 }}>
            {user.email} • Documento: {user.document_type} {user.document_number || 'N/A'}
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <Button
            variant="secondary"
            onClick={() => {
              setShowPasswordModal(true)
            }}
            style={{
              backgroundColor: 'rgba(255, 255, 255, 0.15)',
              color: '#FFFFFF',
              border: '1px solid rgba(255, 255, 255, 0.3)',
            }}
          >
            Cambiar Contraseña
          </Button>
          <Button
            variant="danger"
            onClick={() => {
              void logout()
            }}
          >
            Cerrar Sesión
          </Button>
        </div>
      </div>

      {/* Must Change Password Warning Banner */}
      {user.must_change_password && (
        <div
          style={{
            backgroundColor: '#FEF3C7',
            border: '1px solid #F59E0B',
            color: '#92400E',
            padding: '1rem 1.5rem',
            borderRadius: '12px',
            marginBottom: '2rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div>
            <strong>Cambio de contraseña obligatorio:</strong> Su cuenta requiere actualizar la contraseña para continuar.
          </div>
          <Button
            variant="primary"
            size="sm"
            onClick={() => {
              setShowPasswordModal(true)
            }}
          >
            Actualizar Ahora
          </Button>
        </div>
      )}

      {/* Grid Layout: Context & Permissions */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
          gap: '1.5rem',
        }}
      >
        {/* Institutional Context Card */}
        <div
          style={{
            backgroundColor: '#FFFFFF',
            borderRadius: '12px',
            border: '1px solid #E2E8F0',
            padding: '1.5rem',
            boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
          }}
        >
          <h2 style={{ fontSize: '1.125rem', fontWeight: 700, color: '#0F172A', marginBottom: '1rem' }}>
            Alcance Institucional
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.875rem' }}>
            <div>
              <span style={{ color: '#64748B' }}>Nivel de Alcance: </span>
              <strong>{user.scope.is_national ? 'Nacional (Todo el Territorio)' : 'Institucional'}</strong>
            </div>
            <div>
              <span style={{ color: '#64748B' }}>País: </span>
              <strong>{user.scope.country_code || 'CO'}</strong>
            </div>
            {user.scope.institution_id && (
              <div>
                <span style={{ color: '#64748B' }}>ID Institución: </span>
                <code style={{ fontSize: '0.8rem', backgroundColor: '#F1F5F9', padding: '0.2rem 0.4rem', borderRadius: '4px' }}>
                  {user.scope.institution_id}
                </code>
              </div>
            )}
          </div>
        </div>

        {/* Roles & Permissions Card */}
        <div
          style={{
            backgroundColor: '#FFFFFF',
            borderRadius: '12px',
            border: '1px solid #E2E8F0',
            padding: '1.5rem',
            boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
          }}
        >
          <h2 style={{ fontSize: '1.125rem', fontWeight: 700, color: '#0F172A', marginBottom: '1rem' }}>
            Roles y Permisos RBAC
          </h2>
          <div style={{ marginBottom: '1rem' }}>
            <div style={{ fontSize: '0.8125rem', fontWeight: 600, color: '#64748B', marginBottom: '0.5rem' }}>
              ROLES ASIGNADOS
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
              {user.roles.map((role) => (
                <span
                  key={role}
                  style={{
                    backgroundColor: '#EFF6FF',
                    color: '#1D4ED8',
                    padding: '0.25rem 0.75rem',
                    borderRadius: '9999px',
                    fontSize: '0.8125rem',
                    fontWeight: 600,
                  }}
                >
                  {role}
                </span>
              ))}
            </div>
          </div>

          <div>
            <div style={{ fontSize: '0.8125rem', fontWeight: 600, color: '#64748B', marginBottom: '0.5rem' }}>
              PERMISOS ATÓMICOS ({user.permissions.length})
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem', maxHeight: '150px', overflowY: 'auto' }}>
              {user.permissions.map((perm) => (
                <code
                  key={perm}
                  style={{
                    backgroundColor: '#F8FAFC',
                    border: '1px solid #E2E8F0',
                    color: '#334155',
                    padding: '0.15rem 0.4rem',
                    borderRadius: '4px',
                    fontSize: '0.75rem',
                  }}
                >
                  {perm}
                </code>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* National Administration Module Access Card (Fase 3C) */}
      {(user.scope.is_national || user.roles.includes('national_admin') || user.roles.includes('superadmin')) && (
        <div
          style={{
            marginTop: '2rem',
            backgroundColor: '#0F172A',
            color: '#FFFFFF',
            borderRadius: '16px',
            border: '1px solid #1E293B',
            padding: '2rem',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
            <div>
              <div
                style={{
                  display: 'inline-block',
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  backgroundColor: 'rgba(252, 209, 22, 0.2)',
                  color: '#FCD116',
                  padding: '0.25rem 0.75rem',
                  borderRadius: '9999px',
                  marginBottom: '0.5rem',
                }}
              >
                Nivel Nacional • Fase 3C
              </div>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#FFFFFF', margin: '0 0 0.25rem 0' }}>
                Aprovisionamiento Institucional y Rectores
              </h2>
              <p style={{ fontSize: '0.875rem', color: '#94A3B8', margin: 0 }}>
                Catálogo general de colegios, registro oficial DANE, creación de sedes e invitaciones seguras a Rectores.
              </p>
            </div>
            <Link to="/admin/institutions" style={{ textDecoration: 'none' }}>
              <Button
                variant="primary"
                style={{
                  backgroundColor: '#2563EB',
                  fontWeight: 700,
                }}
              >
                Abrir Catálogo Nacional →
              </Button>
            </Link>
          </div>
        </div>
      )}

      {/* Academic Management Module Access Card (Directive Roles Only) */}
      {(() => {
        const isDirective = user.roles.some((r) =>
          ['rector', 'superadmin', 'national_admin', 'coordinator', 'academic_coordinator', 'institution_admin', 'department_admin', 'municipality_admin'].includes(r)
        )

        if (!isDirective) {
          return null
        }

        const availableAcademicCards = [
          {
            tab: 'years',
            title: 'Años Lectivos',
            desc: 'Calendario, vigencias y cierres',
            icon: '📅',
            permission: 'academic_years:read',
          },
          {
            tab: 'groups',
            title: 'Grupos y Cupos',
            desc: 'Salones, cupos y directores',
            icon: '🏫',
            permission: 'groups:read',
          },
          {
            tab: 'students',
            title: 'Estudiantes (SIMAT)',
            desc: 'Fichas y datos de inclusión',
            icon: '🎓',
            permission: 'students:read',
          },
          {
            tab: 'teachers',
            title: 'Planta Docente',
            desc: 'Nombramientos y aptitud',
            icon: '👩‍🏫',
            permission: 'teachers:read',
          },
          {
            tab: 'enrollments',
            title: 'Libro de Matrículas',
            desc: 'Contratos, retiros y grados',
            icon: '📑',
            permission: 'enrollments:read',
          },
          {
            tab: 'transfers',
            title: 'Traslados de Salón',
            desc: 'Reubicaciones y auditoría',
            icon: '🔄',
            permission: 'enrollments:read',
          },
          {
            tab: 'assignments',
            title: 'Carga Académica',
            desc: 'Asignaturas y sustituciones',
            icon: '📚',
            permission: 'academic_assignments:read',
          },
          {
            tab: 'guardians',
            title: 'Acudientes',
            desc: 'Contactos y autorizaciones',
            icon: '👪',
            permission: 'guardians:read',
          },
        ].filter((c) => hasPermission(c.permission))

        if (availableAcademicCards.length > 0) {
          return (
            <div
              style={{
                marginTop: '2rem',
                backgroundColor: '#FFFFFF',
                borderRadius: '16px',
                border: '1px solid #E2E8F0',
                padding: '2rem',
                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  flexWrap: 'wrap',
                  gap: '1rem',
                  marginBottom: '1.5rem',
                }}
              >
                <div>
                  <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#0F172A', margin: '0 0 0.25rem 0' }}>
                    Módulo de Gestión Académica e Institucional
                  </h2>
                  <p style={{ fontSize: '0.875rem', color: '#64748B', margin: 0 }}>
                    Consola directiva de administración escolar: Años Lectivos, Censo SIMAT, Grupos, Docentes y Carga Académica.
                  </p>
                </div>
                <Link to={`/academic?tab=${availableAcademicCards[0].tab}`} style={{ textDecoration: 'none' }}>
                  <Button variant="primary">
                    Abrir Gestión Académica →
                  </Button>
                </Link>
              </div>

              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                  gap: '1rem',
                }}
              >
                {availableAcademicCards.map((card) => (
                  <Link key={card.tab} to={`/academic?tab=${card.tab}`} style={{ textDecoration: 'none' }}>
                    <div
                      style={{
                        padding: '1rem',
                        backgroundColor: '#F8FAFC',
                        borderRadius: '10px',
                        border: '1px solid #E2E8F0',
                        transition: 'border-color 150ms, box-shadow 150ms',
                        cursor: 'pointer',
                      }}
                    >
                      <div style={{ fontSize: '1.5rem', marginBottom: '0.25rem' }}>{card.icon}</div>
                      <div style={{ fontWeight: 700, color: '#0F172A', fontSize: '0.9375rem' }}>{card.title}</div>
                      <div style={{ fontSize: '0.75rem', color: '#64748B', marginTop: '0.25rem' }}>{card.desc}</div>
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          )
        }

        return null
      })()}

      {/* Guardian Family Portal Access Card */}
      {user.roles.includes('guardian') && (
        <div
          style={{
            marginTop: '2rem',
            backgroundColor: '#FFFFFF',
            borderRadius: '16px',
            border: '1px solid #E2E8F0',
            padding: '2rem',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
            <span style={{ fontSize: '1.75rem' }}>👪</span>
            <div>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#0F172A', margin: 0 }}>
                Portal de Acompañamiento Familiar
              </h2>
              <p style={{ fontSize: '0.875rem', color: '#64748B', margin: '0.25rem 0 0 0' }}>
                Rol de Acudiente Legal vinculado a su establecimiento educativo.
              </p>
            </div>
          </div>
          <p style={{ fontSize: '0.875rem', color: '#334155', lineHeight: 1.6, margin: 0 }}>
            Su cuenta se encuentra debidamente autenticada como Acudiente. El seguimiento a calificaciones, reportes de asistencia y citaciones institucionales de sus tutorados se canaliza a través de los directores de grupo y los boletines emitidos por la institución educativa.
          </p>
        </div>
      )}

      {/* Virtual Classrooms & Real-Time Collaboration Access Card (Phase 4) */}
      {hasPermission('virtual_classrooms:read') && (
        <div
          style={{
            marginTop: '2rem',
            backgroundColor: '#FFFFFF',
            borderRadius: '16px',
            border: '1px solid #E2E8F0',
            padding: '2rem',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
            <div>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#0F172A', margin: '0 0 0.25rem 0' }}>
                Aulas Virtuales y Clases en Vivo (Fase 4)
              </h2>
              <p style={{ fontSize: '0.875rem', color: '#64748B', margin: 0 }}>
                Videoconferencias en tiempo real, registro de asistencia automática y repositorio de grabaciones.
              </p>
            </div>
            <Link to="/virtual-classrooms" style={{ textDecoration: 'none' }}>
              <Button variant="primary">
                Ingresar a Aulas Virtuales →
              </Button>
            </Link>
          </div>
        </div>
      )}

      {/* Teacher Portal Module Access Card (Phase 13D.5 / 13E.3) */}
      {user.roles.includes('teacher') && (
        <div
          style={{
            marginTop: '2rem',
            backgroundColor: '#0F172A',
            color: '#FFFFFF',
            borderRadius: '16px',
            border: '1px solid #1E293B',
            padding: '2rem',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.5rem' }}>
            <div>
              <div
                style={{
                  display: 'inline-block',
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  backgroundColor: 'rgba(56, 189, 248, 0.2)',
                  color: '#38BDF8',
                  padding: '0.25rem 0.75rem',
                  borderRadius: '9999px',
                  marginBottom: '0.5rem',
                }}
              >
                Espacio Pedagógico Docente
              </div>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#FFFFFF', margin: '0 0 0.25rem 0' }}>
                Portal Docente y Gestión Pedagógica
              </h2>
              <p style={{ fontSize: '0.875rem', color: '#94A3B8', margin: 0 }}>
                Carga académica asignada, control de salones, actividades, calificaciones, asistencia y planeación curricular.
              </p>
            </div>
            <Link to="/teacher?tab=load" style={{ textDecoration: 'none' }}>
              <Button
                variant="primary"
                style={{
                  backgroundColor: '#0284C7',
                  fontWeight: 700,
                }}
              >
                Abrir Mi Carga Académica →
              </Button>
            </Link>
          </div>

          {/* Quick Access Subcards */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
              gap: '0.75rem',
            }}
          >
            {[
              { tab: 'load', title: 'Mi Carga', desc: 'Materias y asignaciones', icon: '📚' },
              { tab: 'groups', title: 'Mis Grupos', desc: 'Salones y planillas', icon: '👥' },
              { tab: 'activities', title: 'Actividades', desc: 'Tareas y evaluaciones', icon: '📝' },
              { tab: 'grades', title: 'Calificaciones', desc: 'Planilla de notas', icon: '📊' },
              { tab: 'attendance', title: 'Asistencia', desc: 'Control diario de clase', icon: '📋' },
              { tab: 'planning', title: 'Planeación', desc: 'Unidades curriculares', icon: '🎯' },
            ].map((sc) => (
              <Link key={sc.tab} to={`/teacher?tab=${sc.tab}`} style={{ textDecoration: 'none' }}>
                <div
                  style={{
                    backgroundColor: 'rgba(255, 255, 255, 0.06)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: '10px',
                    padding: '0.875rem 1rem',
                    transition: 'background-color 150ms',
                    cursor: 'pointer',
                  }}
                >
                  <div style={{ fontSize: '1.25rem', marginBottom: '0.2rem' }}>{sc.icon}</div>
                  <div style={{ fontSize: '0.875rem', fontWeight: 700, color: '#FFFFFF' }}>{sc.title}</div>
                  <div style={{ fontSize: '0.75rem', color: '#94A3B8', marginTop: '0.15rem' }}>{sc.desc}</div>
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Student Portal Module Access Card (Phase 14B) */}
      {user.roles.includes('student') && (
        <div
          style={{
            marginTop: '2rem',
            backgroundColor: '#1E3A8A',
            color: '#FFFFFF',
            borderRadius: '16px',
            border: '1px solid #1E40AF',
            padding: '2rem',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.5rem' }}>
            <div>
              <div
                style={{
                  display: 'inline-block',
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  backgroundColor: 'rgba(147, 197, 253, 0.2)',
                  color: '#93C5FD',
                  padding: '0.25rem 0.75rem',
                  borderRadius: '9999px',
                  marginBottom: '0.5rem',
                }}
              >
                Espacio Académico Estudiantil
              </div>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#FFFFFF', margin: '0 0 0.25rem 0' }}>
                Portal del Estudiante
              </h2>
              <p style={{ fontSize: '0.875rem', color: '#BFDBFE', margin: 0 }}>
                Tareas pendientes, evaluaciones, calificaciones oficiales, control de asistencia y salas de clase virtual.
              </p>
            </div>
            <Link to="/student?tab=dashboard" style={{ textDecoration: 'none' }}>
              <Button
                variant="primary"
                style={{
                  backgroundColor: '#2563EB',
                  fontWeight: 700,
                }}
              >
                Ingresar al Portal Estudiante →
              </Button>
            </Link>
          </div>

          {/* Quick Access Subcards */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
              gap: '0.75rem',
            }}
          >
            {[
              { tab: 'subjects', title: 'Mis Asignaturas', desc: 'Docentes y materias', icon: '📚' },
              { tab: 'tasks', title: 'Mis Tareas', desc: 'Talleres y entregas', icon: '📝' },
              { tab: 'grades', title: 'Calificaciones', desc: 'Libreta de notas', icon: '📊' },
              { tab: 'attendance', title: 'Mi Asistencia', desc: 'Historial y porcentaje', icon: '📋' },
              { tab: 'virtual-classes', title: 'Clases Virtuales', desc: 'En vivo y grabaciones', icon: '💻' },
              { tab: 'profile', title: 'Mi Perfil', desc: 'Matrícula y SIMAT', icon: '👤' },
            ].map((sc) => (
              <Link key={sc.tab} to={`/student?tab=${sc.tab}`} style={{ textDecoration: 'none' }}>
                <div
                  style={{
                    backgroundColor: 'rgba(255, 255, 255, 0.08)',
                    border: '1px solid rgba(255, 255, 255, 0.15)',
                    borderRadius: '10px',
                    padding: '0.875rem 1rem',
                    transition: 'background-color 150ms',
                    cursor: 'pointer',
                  }}
                >
                  <div style={{ fontSize: '1.25rem', marginBottom: '0.2rem' }}>{sc.icon}</div>
                  <div style={{ fontSize: '0.875rem', fontWeight: 700, color: '#FFFFFF' }}>{sc.title}</div>
                  <div style={{ fontSize: '0.75rem', color: '#BFDBFE', marginTop: '0.15rem' }}>{sc.desc}</div>
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Guardian Portal Module Access Card (Phase 14C) */}
      {user.roles.includes('guardian') && (
        <div
          style={{
            marginTop: '2rem',
            backgroundColor: '#0F172A',
            color: '#FFFFFF',
            borderRadius: '16px',
            border: '1px solid #1E293B',
            padding: '2rem',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.5rem' }}>
            <div>
              <div
                style={{
                  display: 'inline-block',
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  backgroundColor: 'rgba(244, 114, 182, 0.2)',
                  color: '#F472B6',
                  padding: '0.25rem 0.75rem',
                  borderRadius: '9999px',
                  marginBottom: '0.5rem',
                }}
              >
                Acompañamiento y Supervisión Familiar
              </div>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#FFFFFF', margin: '0 0 0.25rem 0' }}>
                Portal de Acudientes y Familias
              </h2>
              <p style={{ fontSize: '0.875rem', color: '#94A3B8', margin: 0 }}>
                Monitoreo de deberes, calificaciones oficiales, control de asistencia y agenda de clases virtuales de sus hijos.
              </p>
            </div>
            <Link to="/guardian?tab=dashboard" style={{ textDecoration: 'none' }}>
              <Button
                variant="primary"
                style={{
                  backgroundColor: '#DB2777',
                  fontWeight: 700,
                }}
              >
                Ingresar al Portal Acudiente →
              </Button>
            </Link>
          </div>

          {/* Quick Access Subcards */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
              gap: '0.75rem',
            }}
          >
            {[
              { tab: 'students', title: 'Mis Hijos', desc: 'Tutorados y matrícula', icon: '👨‍👧‍👦' },
              { tab: 'academic', title: 'Rendimiento', desc: 'Promedios y materias', icon: '📈' },
              { tab: 'tasks', title: 'Tareas Escolares', desc: 'Seguimiento de deberes', icon: '📝' },
              { tab: 'grades', title: 'Calificaciones', desc: 'Libreta de notas', icon: '📊' },
              { tab: 'attendance', title: 'Asistencia', desc: 'Historial y reportes', icon: '📋' },
              { tab: 'virtual-classes', title: 'Clases Virtuales', desc: 'Agenda y grabaciones', icon: '💻' },
            ].map((gc) => (
              <Link key={gc.tab} to={`/guardian?tab=${gc.tab}`} style={{ textDecoration: 'none' }}>
                <div
                  style={{
                    backgroundColor: 'rgba(255, 255, 255, 0.05)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: '10px',
                    padding: '0.875rem 1rem',
                    transition: 'background-color 150ms',
                    cursor: 'pointer',
                  }}
                >
                  <div style={{ fontSize: '1.25rem', marginBottom: '0.2rem' }}>{gc.icon}</div>
                  <div style={{ fontSize: '0.875rem', fontWeight: 700, color: '#FFFFFF' }}>{gc.title}</div>
                  <div style={{ fontSize: '0.75rem', color: '#94A3B8', marginTop: '0.15rem' }}>{gc.desc}</div>
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Change Password Modal */}
      {showPasswordModal && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(15, 23, 42, 0.6)',
            backdropFilter: 'blur(4px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 50,
            padding: '1rem',
          }}
        >
          <div
            style={{
              backgroundColor: '#FFFFFF',
              borderRadius: '16px',
              maxWidth: '440px',
              width: '100%',
              padding: '2rem',
              boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
            }}
          >
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#0F172A', marginBottom: '0.5rem' }}>
              Cambiar Contraseña
            </h2>
            <p style={{ fontSize: '0.875rem', color: '#64748B', marginBottom: '1.5rem' }}>
              La contraseña debe contener mínimo 12 caracteres cumpliendo los estándares de seguridad nacional.
            </p>

            {passwordError && (
              <div
                style={{
                  backgroundColor: '#FEF2F2',
                  border: '1px solid #FCA5A5',
                  color: '#991B1B',
                  padding: '0.75rem',
                  borderRadius: '8px',
                  fontSize: '0.875rem',
                  marginBottom: '1rem',
                }}
              >
                {passwordError}
              </div>
            )}

            {passwordSuccess && (
              <div
                style={{
                  backgroundColor: '#ECFDF5',
                  border: '1px solid #6EE7B7',
                  color: '#065F46',
                  padding: '0.75rem',
                  borderRadius: '8px',
                  fontSize: '0.875rem',
                  marginBottom: '1rem',
                }}
              >
                {passwordSuccess}
              </div>
            )}

            <form
              onSubmit={(e) => {
                void handlePasswordSubmit(e)
              }}
            >
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                  Contraseña Actual
                </label>
                <input
                  type="password"
                  value={currentPassword}
                  onChange={(e) => {
                    setCurrentPassword(e.target.value)
                  }}
                  disabled={isChangingPassword}
                  required
                  style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
                />
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                  Nueva Contraseña (mínimo 12 caracteres)
                </label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => {
                    setNewPassword(e.target.value)
                  }}
                  disabled={isChangingPassword}
                  required
                  style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
                />
              </div>

              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#334155', marginBottom: '0.25rem' }}>
                  Confirmar Nueva Contraseña
                </label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => {
                    setConfirmPassword(e.target.value)
                  }}
                  disabled={isChangingPassword}
                  required
                  style={{ width: '100%', padding: '0.625rem', borderRadius: '6px', border: '1px solid #CBD5E1', boxSizing: 'border-box' }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
                {!user.must_change_password && (
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={() => {
                      setShowPasswordModal(false)
                    }}
                    disabled={isChangingPassword}
                  >
                    Cancelar
                  </Button>
                )}
                <Button
                  type="submit"
                  variant="primary"
                  disabled={isChangingPassword}
                >
                  {isChangingPassword ? <LoadingSpinner size="sm" /> : 'Actualizar Contraseña'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default Dashboard
