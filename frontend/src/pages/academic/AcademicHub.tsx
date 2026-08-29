/**
 * PEVN Frontend — Academic Management Hub (Portal de Gestión Académica)
 *
 * Central master view aggregating all 8 academic domain modules:
 * Años Lectivos, Grupos/Salones, Estudiantes, Docentes, Acudientes,
 * Matrículas, Traslados de Salón y Carga Académica.
 */

import React, { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Tabs, type TabItem } from '@/components/ui/Tabs'
import { useAuth } from '@/hooks/useAuth'
import { AcademicYearsView } from './AcademicYearsView'
import { GroupsView } from './GroupsView'
import { StudentsView } from './StudentsView'
import { TeachersView } from './TeachersView'
import { GuardiansView } from './GuardiansView'
import { EnrollmentsView } from './EnrollmentsView'
import { TransfersView } from './TransfersView'
import { AcademicAssignmentsView } from './AcademicAssignmentsView'

export const AcademicHub: React.FC = () => {
  const { user, hasPermission } = useAuth()
  const [searchParams, setSearchParams] = useSearchParams()
  const [unauthorizedMessage, setUnauthorizedMessage] = useState<string | null>(null)

  const allTabs: (TabItem & { permission?: string })[] = [
    { id: 'years', label: 'Años Lectivos', icon: '📅', permission: 'academic_years:read' },
    { id: 'groups', label: 'Grupos y Cupos', icon: '🏫', permission: 'groups:read' },
    { id: 'students', label: 'Estudiantes (SIMAT)', icon: '🎓', permission: 'students:read' },
    { id: 'teachers', label: 'Planta Docente', icon: '👩‍🏫', permission: 'teachers:read' },
    { id: 'guardians', label: 'Acudientes', icon: '👪', permission: 'guardians:read' },
    { id: 'enrollments', label: 'Libro de Matrículas', icon: '📑', permission: 'enrollments:read' },
    { id: 'transfers', label: 'Traslados de Salón', icon: '🔄', permission: 'enrollments:read' },
    { id: 'assignments', label: 'Carga Académica', icon: '📚', permission: 'academic_assignments:read' },
  ]

  const academicTabs = useMemo<TabItem[]>(() => {
    return allTabs.filter(t => !t.permission || hasPermission(t.permission))
  }, [hasPermission])

  const currentTab = searchParams.get('tab')
  const defaultTab = academicTabs[0]?.id || 'years'
  const validTab = academicTabs.some(t => t.id === currentTab) ? (currentTab as string) : defaultTab
  const [activeTab, setActiveTab] = useState<string>(validTab)

  useEffect(() => {
    if (currentTab) {
      const requestedTab = allTabs.find(t => t.id === currentTab)
      const isAuthorized = academicTabs.some(t => t.id === currentTab)

      if (requestedTab && !isAuthorized) {
        const fallbackLabel = academicTabs[0]?.label ? `"${academicTabs[0].label}"` : 'su panel institucional'
        setUnauthorizedMessage(
          `La sección "${requestedTab.label}" no se encuentra disponible para su rol institucional o nivel de permisos actual. Ha sido redirigido a ${fallbackLabel}.`
        )
      } else {
        setUnauthorizedMessage(null)
      }
    }
  }, [currentTab, academicTabs])

  useEffect(() => {
    if (academicTabs.length > 0 && !academicTabs.some(t => t.id === activeTab)) {
      setActiveTab(academicTabs[0].id)
    }
  }, [academicTabs, activeTab])

  const handleTabChange = (tabId: string) => {
    setUnauthorizedMessage(null)
    setActiveTab(tabId)
    setSearchParams({ tab: tabId })
  }

  const renderActiveModule = () => {
    switch (activeTab) {
      case 'years':
        return <AcademicYearsView />
      case 'groups':
        return <GroupsView />
      case 'students':
        return <StudentsView />
      case 'teachers':
        return <TeachersView />
      case 'guardians':
        return <GuardiansView />
      case 'enrollments':
        return <EnrollmentsView />
      case 'transfers':
        return <TransfersView />
      case 'assignments':
        return <AcademicAssignmentsView />
      default:
        return <AcademicYearsView />
    }
  }

  return (
    <div style={{ maxWidth: '1200px', margin: '2rem auto', padding: '0 1rem' }}>
      {/* Header Banner */}
      <div
        style={{
          backgroundColor: '#0F172A',
          color: '#FFFFFF',
          borderRadius: '16px',
          padding: '2rem',
          marginBottom: '2rem',
          boxShadow: '0 10px 15px -3px rgba(15, 23, 42, 0.15)',
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
                backgroundColor: 'rgba(255, 255, 255, 0.15)',
                color: '#F8FAFC',
                padding: '0.25rem 0.75rem',
                borderRadius: '9999px',
                marginBottom: '0.5rem',
              }}
            >
              Módulo de Gestión Académica • Fase 3B
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
              Gestión Académica e Institucional
            </h1>
            <p style={{ color: '#E2E8F0', fontSize: '0.875rem', margin: 0 }}>
              Administración de calendarios escolares, salones, matrículas, planta docente y carga horaria.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <Link to="/dashboard" style={{ textDecoration: 'none' }}>
              <button
                type="button"
                style={{
                  backgroundColor: 'rgba(255, 255, 255, 0.15)',
                  color: '#FFFFFF',
                  border: '1px solid rgba(255, 255, 255, 0.3)',
                  padding: '0.5rem 1rem',
                  borderRadius: '8px',
                  fontSize: '0.875rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                ← Volver al Panel
              </button>
            </Link>
          </div>
        </div>

        {user && (
          <div
            style={{
              marginTop: '1.25rem',
              paddingTop: '1rem',
              borderTop: '1px solid rgba(255, 255, 255, 0.1)',
              display: 'flex',
              gap: '1.5rem',
              fontSize: '0.8125rem',
              color: '#CBD5E1',
              flexWrap: 'wrap',
            }}
          >
            <div>
              Operador: <strong>{user.full_name || user.username}</strong>
            </div>
            <div>
              Alcance:{' '}
              <strong>{user.scope.is_national ? 'Nacional' : 'Institucional'}</strong>
            </div>
            {user.scope.institution_id && (
              <div>
                ID Institución: <code>{user.scope.institution_id}</code>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Unauthorized Access Notification Banner */}
      {unauthorizedMessage && (
        <div
          role="alert"
          aria-live="polite"
          style={{
            backgroundColor: '#EFF6FF',
            border: '1px solid #93C5FD',
            borderLeft: '4px solid #3B82F6',
            borderRadius: '8px',
            padding: '1rem 1.25rem',
            marginBottom: '1.5rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '1rem',
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.05)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <span style={{ fontSize: '1.25rem' }}>ℹ️</span>
            <span style={{ color: '#1E40AF', fontSize: '0.875rem', fontWeight: 500 }}>
              {unauthorizedMessage}
            </span>
          </div>
          <button
            type="button"
            onClick={() => setUnauthorizedMessage(null)}
            aria-label="Cerrar notificación"
            style={{
              backgroundColor: 'transparent',
              border: 'none',
              color: '#3B82F6',
              fontWeight: 700,
              fontSize: '1rem',
              cursor: 'pointer',
              padding: '0.25rem 0.5rem',
              borderRadius: '4px',
            }}
          >
            ✕
          </button>
        </div>
      )}

      {/* Zero State for users without Academic Management Permissions */}
      {academicTabs.length === 0 ? (
        <div
          style={{
            backgroundColor: '#FFFFFF',
            borderRadius: '16px',
            border: '1px solid #E2E8F0',
            padding: '3rem 2rem',
            textAlign: 'center',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)',
          }}
        >
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🔒</div>
          <h2 style={{ fontSize: '1.375rem', fontWeight: 700, color: '#0F172A', marginBottom: '0.75rem' }}>
            Portal de Gestión Académica — Acceso Restringido
          </h2>
          <p style={{ color: '#64748B', maxWidth: '600px', margin: '0 auto 1.5rem auto', lineHeight: 1.6, fontSize: '0.9375rem' }}>
            Su cuenta de usuario ({user?.email}) no dispone de módulos de administración académica asignados para su rol actual ({user?.roles.join(', ') || 'Usuario'}). 
            Las funciones de gestión de salones, matrículas y personal están reservadas para directivos y coordinadores de la institución educativa.
          </p>
          <Link to="/dashboard" style={{ textDecoration: 'none' }}>
            <button
              type="button"
              style={{
                backgroundColor: '#2563EB',
                color: '#FFFFFF',
                border: 'none',
                padding: '0.625rem 1.5rem',
                borderRadius: '8px',
                fontSize: '0.875rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              ← Volver al Panel Principal
            </button>
          </Link>
        </div>
      ) : (
        <>
          {/* Module Tabs Navigation */}
          <Tabs tabs={academicTabs} activeTab={activeTab} onChange={handleTabChange} />

          {/* Render Selected Academic Module */}
          <div>{renderActiveModule()}</div>
        </>
      )}
    </div>
  )
}

export default AcademicHub
