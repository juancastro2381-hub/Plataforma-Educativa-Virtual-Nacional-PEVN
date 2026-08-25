/**
 * PEVN Frontend — Academic Management Hub (Portal de Gestión Académica)
 *
 * Central master view aggregating all 8 academic domain modules:
 * Años Lectivos, Grupos/Salones, Estudiantes, Docentes, Acudientes,
 * Matrículas, Traslados de Salón y Carga Académica.
 */

import React, { useState } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
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
  const { user } = useAuth()
  const [searchParams, setSearchParams] = useSearchParams()

  const currentTab = searchParams.get('tab') || 'years'
  const [activeTab, setActiveTab] = useState<string>(currentTab)

  const academicTabs: TabItem[] = [
    { id: 'years', label: 'Años Lectivos', icon: '📅' },
    { id: 'groups', label: 'Grupos y Cupos', icon: '🏫' },
    { id: 'students', label: 'Estudiantes (SIMAT)', icon: '🎓' },
    { id: 'teachers', label: 'Planta Docente', icon: '👩‍🏫' },
    { id: 'guardians', label: 'Acudientes', icon: '👪' },
    { id: 'enrollments', label: 'Libro de Matrículas', icon: '📑' },
    { id: 'transfers', label: 'Traslados de Salón', icon: '🔄' },
    { id: 'assignments', label: 'Carga Académica', icon: '📚' },
  ]

  const handleTabChange = (tabId: string) => {
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

      {/* Module Tabs Navigation */}
      <Tabs tabs={academicTabs} activeTab={activeTab} onChange={handleTabChange} />

      {/* Render Selected Academic Module */}
      <div>{renderActiveModule()}</div>
    </div>
  )
}

export default AcademicHub
