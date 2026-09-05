/**
 * PEVN Frontend — Student Portal Navigation Subtabs
 *
 * Tab bar for navigating student portal modules:
 * - Inicio
 * - Mis asignaturas
 * - Mis tareas (with pending tasks badge)
 * - Mis calificaciones
 * - Mi asistencia
 * - Clases virtuales (with live/upcoming class indicator)
 * - Mi perfil
 */

import React from 'react'
import type { StudentTab } from '@/types/student'

interface StudentNavbarProps {
  activeTab: StudentTab
  onTabChange: (tab: StudentTab) => void
  pendingTasksCount?: number
  upcomingClassesCount?: number
}

export const StudentNavbar: React.FC<StudentNavbarProps> = ({
  activeTab,
  onTabChange,
  pendingTasksCount = 0,
  upcomingClassesCount = 0,
}) => {
  const tabs: {
    id: StudentTab
    label: string
    icon: string
    badge?: number | null
    badgeColor?: string
  }[] = [
    { id: 'dashboard', label: 'Inicio', icon: '🏠' },
    { id: 'subjects', label: 'Mis Asignaturas', icon: '📚' },
    {
      id: 'tasks',
      label: 'Mis Tareas',
      icon: '📝',
      badge: pendingTasksCount > 0 ? pendingTasksCount : null,
      badgeColor: '#EF4444',
    },
    { id: 'grades', label: 'Mis Calificaciones', icon: '📊' },
    { id: 'attendance', label: 'Mi Asistencia', icon: '📋' },
    {
      id: 'virtual-classes',
      label: 'Clases Virtuales',
      icon: '💻',
      badge: upcomingClassesCount > 0 ? upcomingClassesCount : null,
      badgeColor: '#10B981',
    },
    { id: 'communications', label: 'Comunicados', icon: '📢' },
    { id: 'news', label: 'Noticias', icon: '📰' },
    { id: 'incidents', label: 'Convivencia', icon: '⚖️' },
    { id: 'profile', label: 'Mi Perfil', icon: '👤' },
  ]

  return (
    <div
      style={{
        display: 'flex',
        gap: '0.4rem',
        borderBottom: '2px solid #E2E8F0',
        marginBottom: '1.75rem',
        overflowX: 'auto',
        paddingBottom: '2px',
      }}
      role="tablist"
      aria-label="Módulos del portal del estudiante"
    >
      {tabs.map((tab) => {
        const isActive = activeTab === tab.id
        return (
          <button
            key={tab.id}
            role="tab"
            aria-selected={isActive}
            onClick={() => onTabChange(tab.id)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.75rem 1.15rem',
              fontSize: '0.875rem',
              fontWeight: isActive ? 700 : 600,
              color: isActive ? '#1D4ED8' : '#64748B',
              backgroundColor: isActive ? '#EFF6FF' : 'transparent',
              border: 'none',
              borderBottom: isActive ? '3px solid #1D4ED8' : '3px solid transparent',
              borderRadius: '8px 8px 0 0',
              cursor: 'pointer',
              whiteSpace: 'nowrap',
              transition: 'all 0.15s ease',
              marginBottom: '-2px',
            }}
          >
            <span style={{ fontSize: '1.1rem' }} aria-hidden="true">
              {tab.icon}
            </span>
            <span>{tab.label}</span>

            {tab.badge !== null && tab.badge !== undefined && (
              <span
                style={{
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  backgroundColor: tab.badgeColor || '#EF4444',
                  color: '#FFFFFF',
                  borderRadius: '9999px',
                  padding: '0.1rem 0.45rem',
                  minWidth: '18px',
                  textAlign: 'center',
                  lineHeight: 1.2,
                }}
              >
                {tab.badge}
              </span>
            )}
          </button>
        )
      })}
    </div>
  )
}
