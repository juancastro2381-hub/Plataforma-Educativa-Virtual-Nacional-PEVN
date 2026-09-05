/**
 * PEVN Frontend — Guardian Navigation Bar Component
 *
 * Tab bar with active indicators and badging for all 11 guardian navigation subviews.
 */

import React from 'react'
import type { GuardianTab } from '@/types/guardian'

interface Props {
  activeTab: GuardianTab
  onTabChange: (tab: GuardianTab) => void
  pendingTasksCount?: number
  upcomingClassesCount?: number
}

interface TabDef {
  id: GuardianTab
  label: string
  icon: string
  badge?: number
  isComingSoon?: boolean
}

export const GuardianNavbar: React.FC<Props> = ({
  activeTab,
  onTabChange,
  pendingTasksCount = 0,
  upcomingClassesCount = 0,
}) => {
  const tabs: TabDef[] = [
    { id: 'dashboard', label: 'Inicio', icon: '🏠' },
    { id: 'students', label: 'Mis Hijos', icon: '👨‍👧‍👦' },
    { id: 'academic', label: 'Rendimiento', icon: '📈' },
    { id: 'tasks', label: 'Tareas', icon: '📝', badge: pendingTasksCount },
    { id: 'grades', label: 'Calificaciones', icon: '📊' },
    { id: 'attendance', label: 'Asistencia', icon: '📋' },
    { id: 'virtual-classes', label: 'Clases Virtuales', icon: '💻', badge: upcomingClassesCount },
    { id: 'communications', label: 'Comunicados', icon: '📢', isComingSoon: true },
    { id: 'news', label: 'Noticias', icon: '📰', isComingSoon: true },
    { id: 'incidents', label: 'Convivencia', icon: '⚖️', isComingSoon: true },
    { id: 'profile', label: 'Mi Perfil', icon: '👤' },
  ]

  return (
    <div
      style={{
        display: 'flex',
        gap: '0.35rem',
        borderBottom: '2px solid #E2E8F0',
        marginBottom: '1.75rem',
        overflowX: 'auto',
        paddingBottom: '0.25rem',
      }}
    >
      {tabs.map((t) => {
        const isActive = activeTab === t.id
        return (
          <button
            key={t.id}
            type="button"
            data-testid={`guardian-tab-${t.id}`}
            aria-label={t.label}
            onClick={() => onTabChange(t.id)}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.45rem',
              padding: '0.625rem 0.875rem',
              borderRadius: '8px 8px 0 0',
              border: 'none',
              backgroundColor: isActive ? '#0F172A' : 'transparent',
              color: isActive ? '#FFFFFF' : '#475569',
              fontWeight: isActive ? 700 : 500,
              fontSize: '0.8125rem',
              cursor: 'pointer',
              transition: 'all 150ms ease',
              whiteSpace: 'nowrap',
            }}
          >
            <span>{t.icon}</span>
            <span>{t.label}</span>

            {t.badge !== undefined && t.badge > 0 && (
              <span
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '0.7rem',
                  fontWeight: 800,
                  backgroundColor: isActive ? '#EC4899' : '#F43F5E',
                  color: '#FFFFFF',
                  borderRadius: '9999px',
                  minWidth: '1.2rem',
                  height: '1.2rem',
                  padding: '0 0.35rem',
                }}
              >
                {t.badge}
              </span>
            )}

            {t.isComingSoon && (
              <span
                style={{
                  fontSize: '0.65rem',
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  letterSpacing: '0.04em',
                  backgroundColor: isActive ? 'rgba(255,255,255,0.2)' : '#F1F5F9',
                  color: isActive ? '#F8FAFC' : '#94A3B8',
                  padding: '0.15rem 0.4rem',
                  borderRadius: '4px',
                }}
              >
                Fase 15
              </span>
            )}
          </button>
        )
      })}
    </div>
  )
}
