/**
 * PEVN Frontend — Teacher Portal Master Workspace (Phase 13D.5 / 13E.3)
 *
 * Dedicated portal for educators:
 * - Subtabs: Inicio | Mi Carga | Mis Grupos | Actividades | Calificaciones | Asistencia | Planeación
 * - Preserves full separation from Rector administrative module (/academic).
 */

import React, { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { teacherApi } from '@/services/teacher'
import type {
  AcademicActivityResponse,
  TeacherAssignmentItemResponse,
  TeacherDashboardSummaryResponse,
  TeacherGroupItemResponse,
} from '@/types/teacher'
import { TeacherDashboardView } from './TeacherDashboardView'
import { TeacherAssignmentsView } from './TeacherAssignmentsView'
import { TeacherGroupsView } from './TeacherGroupsView'
import { TeacherActivitiesView } from './TeacherActivitiesView'
import { TeacherGradesView } from './TeacherGradesView'
import { TeacherAttendanceView } from './TeacherAttendanceView'
import { TeacherPlanningView } from './TeacherPlanningView'

type TeacherTab = 'dashboard' | 'load' | 'groups' | 'activities' | 'grades' | 'attendance' | 'planning'

export const TeacherPortal: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams()
  const initialTab = (searchParams.get('tab') as TeacherTab) || 'dashboard'
  const [activeTab, setActiveTab] = useState<TeacherTab>(initialTab)

  const [summary, setSummary] = useState<TeacherDashboardSummaryResponse | null>(null)
  const [assignments, setAssignments] = useState<TeacherAssignmentItemResponse[]>([])
  const [groups, setGroups] = useState<TeacherGroupItemResponse[]>([])
  const [activities, setActivities] = useState<AcademicActivityResponse[]>([])

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedGradingActivityId, setSelectedGradingActivityId] = useState<string | null>(null)

  // Sync tab with URL query parameter
  useEffect(() => {
    const tabParam = searchParams.get('tab') as TeacherTab
    if (tabParam && ['dashboard', 'load', 'groups', 'activities', 'grades', 'attendance', 'planning'].includes(tabParam)) {
      setActiveTab(tabParam)
    }
  }, [searchParams])

  const handleTabChange = (newTab: TeacherTab) => {
    setActiveTab(newTab)
    setSearchParams({ tab: newTab })
  }

  const loadAllTeacherData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [sumData, asgData, grpData, actData] = await Promise.all([
        teacherApi.getDashboardSummary(),
        teacherApi.listAssignments(),
        teacherApi.listGroups(),
        teacherApi.listActivities(),
      ])

      setSummary(sumData)
      setAssignments(asgData.items)
      setGroups(grpData.items)
      setActivities(actData.items)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al cargar los datos del portal docente.'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadAllTeacherData()
  }, [])

  const handleSelectActivityForGrading = (activityId: string) => {
    setSelectedGradingActivityId(activityId)
    handleTabChange('grades')
  }

  const tabs: { id: TeacherTab; label: string; icon: string }[] = [
    { id: 'dashboard', label: 'Inicio', icon: '🏠' },
    { id: 'load', label: 'Mi Carga', icon: '📚' },
    { id: 'groups', label: 'Mis Grupos', icon: '👥' },
    { id: 'activities', label: 'Actividades', icon: '📝' },
    { id: 'grades', label: 'Calificaciones', icon: '📊' },
    { id: 'attendance', label: 'Asistencia', icon: '📋' },
    { id: 'planning', label: 'Planeación', icon: '🎯' },
  ]

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '1.5rem' }}>
      {/* Top Header */}
      <div style={{ marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: '1.5rem' }}>🎓</span>
            <h1 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 800, color: '#0F172A' }}>
              Portal Docente Institucional
            </h1>
          </div>
          <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.875rem', color: '#64748B' }}>
            Gestión pedagógica del educador: Carga Académica, Salones, Actividades, Calificaciones, Asistencia y Planeación Curricular.
          </p>
        </div>
      </div>

      {/* Navigation Subtabs Bar */}
      <div
        style={{
          display: 'flex',
          gap: '0.5rem',
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
              onClick={() => handleTabChange(t.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
                padding: '0.625rem 1rem',
                borderRadius: '8px 8px 0 0',
                border: 'none',
                backgroundColor: isActive ? '#1E3A8A' : 'transparent',
                color: isActive ? '#FFFFFF' : '#475569',
                fontWeight: isActive ? 700 : 500,
                fontSize: '0.875rem',
                cursor: 'pointer',
                transition: 'background-color 150ms, color 150ms',
                whiteSpace: 'nowrap',
              }}
            >
              <span>{t.icon}</span>
              <span>{t.label}</span>
            </button>
          )
        })}
      </div>

      {/* Error alert if any */}
      {error && (
        <div
          style={{
            backgroundColor: '#FEF2F2',
            border: '1px solid #FCA5A5',
            borderRadius: '8px',
            padding: '1rem',
            marginBottom: '1.5rem',
            color: '#991B1B',
            fontSize: '0.875rem',
          }}
        >
          {error}
        </div>
      )}

      {/* Main Content Area */}
      <div>
        {activeTab === 'dashboard' && (
          <TeacherDashboardView
            summary={summary}
            loading={loading}
            onTabChange={(tab) => handleTabChange(tab as TeacherTab)}
          />
        )}

        {activeTab === 'load' && (
          <TeacherAssignmentsView
            assignments={assignments}
            groups={groups}
            teacherName={summary?.teacher_name}
            totalUniqueStudents={summary?.total_enrolled_students}
            loading={loading}
          />
        )}

        {activeTab === 'groups' && (
          <TeacherGroupsView
            groups={groups}
            teacherName={summary?.teacher_name}
            loading={loading}
          />
        )}

        {activeTab === 'activities' && (
          <TeacherActivitiesView
            activities={activities}
            assignments={assignments}
            loading={loading}
            onRefresh={loadAllTeacherData}
            onSelectActivityForGrading={handleSelectActivityForGrading}
          />
        )}

        {activeTab === 'grades' && (
          <TeacherGradesView
            activities={activities}
            assignments={assignments}
            initialSelectedActivityId={selectedGradingActivityId}
          />
        )}

        {activeTab === 'attendance' && (
          <TeacherAttendanceView
            assignments={assignments}
          />
        )}

        {activeTab === 'planning' && (
          <TeacherPlanningView
            assignments={assignments}
          />
        )}
      </div>
    </div>
  )
}

export default TeacherPortal
